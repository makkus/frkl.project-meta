# -*- coding: utf-8 -*-
import importlib
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

import jinja2
from frkl.project_meta.core import ProjectMetadata
from frkl.project_meta.defaults import FRKL_PROJECT_META_RESOURCES_FOLDER
from jinja2 import Environment


log = logging.getLogger("frkl.project_meta")

DEFAULT_EXCLUDE_DIRS = [".git", ".tox", ".cache", ".mypy_cache"]


# -----------------------------------------------------------
# helper methods
def get_entry_point_imports_hook(
    entry_points: Mapping[str, Mapping[str, Mapping[str, str]]],
) -> Tuple[Mapping[str, str], Set]:

    hook_ep_packages: Dict[str, List[str]] = dict()
    hiddenimports = set()

    for group, ep_details in entry_points.items():

        for ep_name, ep_dict in ep_details.items():

            module_name = ep_dict["module"]
            attr = ep_dict["attr"]
            hiddenimports.add(module_name)
            hook_ep_packages.setdefault(group, []).append(
                f"{ep_name} = {module_name}:{attr}"
            )

    hooks = {}
    hooks[
        "pkg_resources_hook.py"
    ] = """# Runtime hook generated from spec file to support pkg_resources entrypoints.
ep_packages = {}

if ep_packages:
    import pkg_resources
    default_iter_entry_points = pkg_resources.iter_entry_points

    def hook_iter_entry_points(group, name=None):
        if group in ep_packages and ep_packages[group]:
            eps = ep_packages[group]
            for ep in eps:
                parsedEp = pkg_resources.EntryPoint.parse(ep)
                parsedEp.dist = pkg_resources.Distribution()
                yield parsedEp
        else:
            yield default_iter_entry_points(group, name)
            return

    pkg_resources.iter_entry_points = hook_iter_entry_points

""".format(
        hook_ep_packages
    )

    log.debug(f"Retrieved hooks: {hooks}")
    log.debug(f"Retrieved hidden imports: {hiddenimports}")

    return hooks, hiddenimports


def process_string_template(
    template_string: str, replacement_dict: Optional[Mapping[str, Any]] = None
):
    """Replace template markers with values from a replacement dictionary within a string.

    Args:
      - *template_string*: the template string
      - *replacement_dict*: the dictionary with the replacement strings
      - *jinja_env*: an existing jinja env to use, if specified, the following paramters will be ignored
    """

    if replacement_dict is None:
        sub_dict = {}
    else:
        sub_dict = dict(replacement_dict)

    env = Environment()

    if isinstance(template_string, jinja2.runtime.Undefined):
        return ""

    # add some keywords, to make sure we don't get any weird internal result objects
    sub_dict.setdefault("namespace", None)

    result = env.from_string(template_string).render(sub_dict)

    if isinstance(result, jinja2.runtime.Undefined):
        result = ""

    return result


def get_datas(
    resources_map: Mapping[str, List[str]], exclude_dirs: Optional[Iterable[str]] = None
):

    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS

    datas = []

    for package, files in resources_map.items():

        proot = os.path.dirname(importlib.import_module(package).__file__)
        for f in files:
            src = os.path.join(proot, f)
            if not os.path.isdir(os.path.realpath(src)):
                data = (src, package)
                datas.append(data)
            else:

                for root, dirnames, filenames in os.walk(src, topdown=True):

                    if exclude_dirs:
                        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

                    for filename in filenames:

                        path = os.path.join(root, filename)
                        rel_path = os.path.join(
                            package, os.path.dirname(os.path.relpath(path, proot))
                        )
                        data = (path, rel_path)
                        datas.append(data)

    log.debug(f"Retrieved pkg data: {datas}")
    return datas


def create_entry_point_from_template(
    main_module: str,
    working_dir: str,
    entry_points: Mapping[str, Mapping[str, Mapping[str, str]]],
):

    if not entry_points:
        raise Exception("No entry_points provided.")

    console_scripts = {}

    main_entry_points: List[Mapping[str, Any]] = []

    for group, details in entry_points.items():

        if group != "console_scripts":
            continue

        for ep_name, ep_details in details.items():
            console_scripts[ep_name] = ep_details
            if main_module in ep_details["module"]:
                if main_entry_points:
                    log.warning(
                        f"Can't determine unique entry point for module: {main_module}, registering main application will be unpredictable"
                    )
                main_entry_points.append(ep_details)

    template = Path(
        os.path.join(FRKL_PROJECT_META_RESOURCES_FOLDER, "entry_point.py.j2")
    )
    template_string = template.read_text()

    replaced = process_string_template(
        template_string=template_string,
        replacement_dict={
            "scripts": console_scripts,
            "main_entry_point": main_entry_points[0],
        },
    )

    target = Path(os.path.join(working_dir, "cli.py"))
    target.write_text(replaced)

    return [target.resolve().as_posix()]


class PyinstallerBuildRenderer(object):
    def __init__(self, project_metadata: ProjectMetadata):

        self._project_metadata: ProjectMetadata = project_metadata

    def get_exe_name(self):

        return self._project_metadata.metadata["project"]["exe_name"]

    def get_main_module(self):

        return self._project_metadata.metadata["project_main_module"]

    def create_analysis_args(self):

        package_data = self._project_metadata.create_package_data()
        app_details = package_data["app_details"]

        main_module = app_details["main_module"]
        entry_points = package_data["entry_points"]

        hidden_imports = package_data["hidden_imports"]

        hooks_path = None
        block_cipher = None

        tempdir = tempfile.mkdtemp(prefix="pkg_build")
        datas = get_datas(resources_map=package_data["resources"])

        # ep_hooks, auto_imports = get_entry_point_imports_hook(entry_points=entry_points)
        # runtime_hooks = []
        # for filename, hook_string in ep_hooks.items():
        #     path = os.path.join(tempdir, filename)
        #     with io.open(path, "w", encoding="utf-8") as f:
        #         f.write(hook_string)
        #     runtime_hooks.append(path)

        sc = create_entry_point_from_template(
            main_module=main_module, working_dir=tempdir, entry_points=entry_points
        )

        app_details_file = os.path.join(tempdir, "app.json")
        with open(app_details_file, "w") as f:  # type: ignore
            json.dump(app_details, f)
        d = (app_details_file, main_module)
        datas.append(d)

        kwargs = dict(
            scripts=sc,
            pathex=[],
            binaries=[],
            datas=datas,
            hiddenimports=list(hidden_imports),
            hookspath=hooks_path,
            # runtime_hooks=runtime_hooks,
            runtime_hooks=None,
            excludes=["FixTk", "tcl", "tk", "_tkinter", "tkinter", "Tkinter"],
            win_no_prefer_redirects=False,
            win_private_assemblies=False,
            cipher=block_cipher,
            noarchive=False,
        )

        log.debug(f"Created analysis args: {kwargs}")

        return kwargs
