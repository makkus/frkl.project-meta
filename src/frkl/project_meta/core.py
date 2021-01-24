# -*- coding: utf-8 -*-

import copy
import importlib
import json
import logging
import os
import sys
import types
from datetime import datetime
from types import ModuleType
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Mapping,
    MutableMapping,
    Optional,
    Set,
    Type,
    Union,
)

from appdirs import AppDirs
from frkl.project_meta.utils import discover_installed_modules


try:
    from importlib_metadata import entry_points
except Exception:
    from importlib.metadata import entry_points


log = logging.getLogger("frkl")


class ProjectMetadata(object):
    """Class to hold all relevant information of a frkl-Python package"""

    def __init__(self, project_main_module: Union[str, types.ModuleType]):

        if isinstance(project_main_module, types.ModuleType):
            project_main_module = project_main_module.__name__

        self._project_main_module: str = project_main_module  # type: ignore
        """The main module for this application"""

        self._runtime_details: Optional[Mapping[str, Any]] = None
        """Details about the current app (whether it's a binary, build-time, etc)."""

        self._build_info: Optional[Mapping[str, Any]] = None
        """Details about the build (if running as pyinstaller binary)."""

        self._metadata: Optional[Mapping[str, str]] = None
        """Metadata relevant for building a package/binary for this application."""

        self._version: Optional[str] = None
        """The version of the package."""

        self._other_metadata_projects: Optional[Mapping[str, ProjectMetadata]] = None
        """A dictionary to hold information about the main dependency packages/modules of this applicaiton."""

        self._other_metadata_project_versions: Optional[Mapping[str, str]] = None
        """A dictionary to hold version information of main dependency packages of this application."""

        self._package_defaults: Optional[Mapping[str, Any]] = None
        """Default values for this package (atribures in the '<main_module>.defaults' module)."""

        self._globals: MutableMapping[str, Any] = {}
        """Global variables for this application."""

        self._singletons: MutableMapping[Type, Any] = {}
        """Global singletons for this application."""

        # if this is distributed as a frozen bundle, we read metadata from a file
        # otherwise it will be read dynamically
        self._check_app_metadata_file()

        # for k, v in globals.items():
        #     self.set_global(k, v)

    @property
    def main_module(self) -> str:
        return self._project_main_module

    def _check_app_metadata_file(self) -> None:

        # we only use that if we are dealing with a pyinstaller binary
        if not hasattr(sys, "frozen"):
            return None

        app_details_file = os.path.join(
            sys._MEIPASS, self.main_module, "app.json"  # type: ignore
        )
        if os.path.exists(app_details_file):
            log.debug(f"'app.json' file exists: {app_details_file}")
            with open(app_details_file, "r") as f:
                app_details = json.load(f)
        else:
            raise Exception(f"No 'app.json' file: {app_details_file}")

        self._metadata = app_details["metadata"]
        self._version = app_details["version"]
        # self._other_metadata_projects = app_details["modules_details"]
        self._build_info = app_details["build_info"]
        self._other_metadata_project_versions = app_details[
            "other_frkl_project_versions"
        ]

    @property
    def metadata(self) -> Mapping[str, Any]:
        """Method to retrieve metadata that is relevant to build a binary for this package."""

        if self._metadata is not None:
            return self._metadata

        if not self.main_module:
            raise Exception(
                "Can't retrieve app details: AppEnvironment not initialized yet."
            )

        try:
            meta = importlib.import_module(f"{self.main_module}._frkl")
        except (Exception):
            # log.debug(
            #     f"Pkg '{self.main_module}' does not have a '_meta' module, returning empty dict..."
            # )
            raise Exception(
                f"Can't retrieve app details: application does noth have a '_frkl' module as child of '{self.main_module}'"
            )

        project_json_file = os.path.join(os.path.dirname(meta.__file__), "_frkl.json")
        with open(project_json_file, "r") as f:
            project_json = json.load(f)

        project_metadata = {}
        project_metadata.update(project_json)

        for k in dir(meta):

            if k.startswith("_"):
                continue

            attr = getattr(meta, k)
            if isinstance(
                attr, (ModuleType, type, Callable, Coroutine)  # type: ignore
            ) or str(attr).startswith("typing."):
                continue

            project_metadata[k] = attr

        project_metadata["project_main_module"] = self._project_main_module

        project_name = project_metadata.get("project", {}).get("project_name", None)

        if not project_name:
            raise Exception(
                "Can't retrieve app details: no 'project_name' key in metadata"
            )

        if "exe_name" not in project_metadata["project"].keys():
            project_metadata["project"]["exe_name"] = None

        if "project_slug" not in project_metadata["project"].keys():
            project_metadata["project"]["project_slug"] = (
                project_metadata["project"]["project_name"]
                .replace("-", "_")
                .replace(".", "_")
                .replace(" ", "_")
            )

        self._metadata = project_metadata
        return self._metadata

    @property
    def exe_name(self) -> Optional[str]:
        return self.metadata["project"]["exe_name"]

    @property
    def project_name(self) -> str:
        return self.metadata["project"]["project_name"]

    @property
    def project_slug(self) -> str:
        return self.metadata["project"]["project_slug"]

    @property
    def runtime_details(self) -> Mapping[str, Any]:
        """Method to get information about the running package.

        This is mainly concerned about application artefact metadata, like build time, etc.
        """

        import pkg_resources

        if self._runtime_details is not None:
            return self._runtime_details

        entry_point = None
        if self.exe_name:
            for cs in pkg_resources.iter_entry_points("console_scripts"):
                if cs.name == self.exe_name:
                    entry_point = {
                        "name": cs.name,
                        "module": cs.module_name,
                        "attr": cs.attrs[0],
                    }
                    break

        app_details: Dict[str, Any] = {}

        app_details["entry_point"] = entry_point
        if not hasattr(sys, "frozen"):
            log.debug("creating app details (not frozen).")

            app_details["app_type"] = "python-env"

            app_details["build_info"] = {}

        else:
            app_details["app_type"] = "binary"
            app_details["build_info"] = self._build_info

        self._runtime_details = app_details
        return self._runtime_details

    @property
    def other_frkl_projects(self) -> Mapping[str, "ProjectMetadata"]:

        if self._other_metadata_projects is not None:
            return self._other_metadata_projects

        if hasattr(sys, "frozen"):
            raise Exception(
                "Querying dependency projects not supported for frozen applications."
            )

        modules = discover_installed_modules()
        self._other_metadata_projects = {}
        for m in modules:
            if m.__name__ == self.main_module:
                continue

            p = ProjectMetadata(project_main_module=m)
            self._other_metadata_projects[p.main_module] = p

        log.debug(
            f"(main) dependencies for main module '{self.main_module}': {self._other_metadata_projects}"
        )
        return self._other_metadata_projects

    @property
    def other_frkl_project_versions(self) -> Mapping[str, str]:

        if self._other_metadata_project_versions is None:
            self._other_metadata_project_versions = {
                p.main_module: p.version for p in self.other_frkl_projects.values()
            }
        return self._other_metadata_project_versions

    @property
    def version(self):

        if self._version is not None:
            return self._version

        m = importlib.import_module(self.main_module)
        try:
            version = getattr(m, "get_version")()
        except (Exception) as e:
            log.debug(f"Can't add version for pkg '{self.main_module}': {e}")
            version = "n/a"

        self._version = version
        return self._version

    def get_pkg_defaults(self) -> Mapping[str, Any]:

        if self._package_defaults is not None:
            return self._package_defaults

        try:
            defaults = importlib.import_module(".".join([self.main_module, "defaults"]))
        except (Exception) as e:
            log.warning(f"Can't retrieve defaults module for '{self.main_module}': {e}")
            return {}

        result = {}
        for k in dir(defaults):
            if k.startswith("_"):
                continue

            attr = getattr(defaults, k)
            if isinstance(attr, (ModuleType, type)) or str(attr).startswith("typing."):
                continue

            result[k] = attr

        self._package_defaults = result

        return self._package_defaults

    def get_pkg_metadata_value(
        self, key: str, default: Optional[Any] = "__raise_exception__"
    ) -> Any:

        if key not in self.metadata.keys():
            if default == "__raise_exception__":
                raise Exception(
                    f"No metadata value '{key}' for project '{self.project_name}' available. This is a bug in the packaging of this app."
                )
            else:
                return default

        value = self.metadata[key]
        return value

    def get_app_dirs(self) -> Optional[AppDirs]:
        """Return 'AppDirs' object for this application."""

        for k, v in self.get_pkg_defaults().items():
            if isinstance(v, AppDirs):
                return v

        return None

    def get_resources_folder(self) -> str:
        """Return the resources folder path for this application."""

        # if "resources" in self.build_meta.keys():
        #     return self.build_meta["resources"]

        for k in self.get_pkg_defaults().keys():
            if k.endswith("RESOURCES_FOLDER"):
                return self.get_pkg_defaults()[k]

        raise Exception(f"Can't determine resources folder for '{self.project_name}'.")

    def set_global(self, key: str, value: Any) -> None:
        """Set a global variable for this application."""

        self._globals[key] = value

    def get_global(self, key: str) -> Any:
        """Retrieve a global variable for this application."""

        return self._globals.get(key, None)

    def register_singleton(self, obj: Any, reg_cls: Optional[Type] = None) -> None:

        if reg_cls is not None:
            if not isinstance(obj, reg_cls) and not issubclass(obj.__class__, reg_cls):
                raise Exception(
                    f"Can't register singleton for class '{reg_cls}': object to register does not sub-class this type."
                )
            _reg_cls = reg_cls
        else:
            _reg_cls = obj.__class__

        if _reg_cls in self._singletons.keys() and self._singletons[_reg_cls] != obj:
            raise Exception(f"Can't add singleton for class '{_reg_cls}': already set")

        self._singletons[_reg_cls] = obj

    def get_singleton(self, cls: Type) -> Any:

        return self._singletons.get(cls, None)

    @property
    def module_path(self):

        m = importlib.import_module(self.main_module)
        return m.__file__

    def find_build_properties(self):

        pyinstaller_data = self.metadata.get("build_properties", {})

        result: Dict[str, Any] = {"entry_points": {}}

        for prop in ["resources", "hidden_imports"]:
            result[prop] = set(pyinstaller_data.get(prop, []))

        result["hidden_imports"].add(f"{self.main_module}.defaults")

        # finding entry points
        for entry_point_group, eps in entry_points().items():

            for ep in eps:
                if not ep.value.startswith(self.main_module):
                    continue

                result["entry_points"].setdefault(entry_point_group, {})[ep.name] = {
                    "module": ep.module,
                    "attr": ep.attr,
                }

        mod_path = self.module_path

        mod_parent = os.path.dirname(mod_path)
        resources_folder = os.path.join(mod_parent, "resources")
        if (
            os.path.exists(resources_folder)
            and resources_folder not in result["resources"]
        ):
            result["resources"].add(resources_folder)

        version_file = os.path.join(mod_parent, "version.txt")
        if os.path.exists(version_file) and version_file not in result["resources"]:
            result["resources"].add(version_file)
        frkl_file = os.path.join(mod_parent, "_frkl.json")
        if os.path.exists(frkl_file) and frkl_file not in result["resources"]:
            result["resources"].add(frkl_file)

        _meta_mod_path = os.path.join(mod_path, "_frkl")
        frkl_file = os.path.join(_meta_mod_path, "_frkl.json")
        if os.path.exists(frkl_file) and frkl_file not in result["resources"]:
            result["resources"].add(frkl_file)

        # runtime_hooks = os.path.join(os.path.dirname(_meta_mod_path), "pyinstaller_hooks")
        # if (
        #     os.path.isdir(runtime_hooks)
        #     and runtime_hooks not in result["hooks_path"]
        # ):
        #     result["hooks_path"].add(runtime_hooks)

        return result

    def create_package_data(self) -> Dict[str, Any]:

        build_properties = self.find_build_properties()

        # hooks_path: Set[str] = set()

        hidden_imports: Set[str] = build_properties["hidden_imports"]

        entry_points: Dict[str, MutableMapping[str, Mapping[str, str]]] = {}
        for group, details in build_properties["entry_points"].items():

            for ep_name, ep_details in details.items():
                if ep_name in entry_points.setdefault(group, {}).keys():
                    raise Exception(
                        f"Duplicate entry point name '{ep_name}' for group '{group}'."
                    )
                entry_points[group][ep_name] = ep_details

                hidden_imports.add(ep_details["module"])

        resources_map = {
            self.metadata["project_main_module"]: build_properties["resources"]
        }
        for name, md in self.other_frkl_projects.items():
            other_build_properties = md.find_build_properties()
            resources_map[name] = other_build_properties["resources"]
            hidden_imports.update(other_build_properties["hidden_imports"])

            for group, details in other_build_properties["entry_points"].items():

                for ep_name, ep_details in details.items():
                    if ep_name in entry_points.setdefault(group, {}).keys():
                        raise Exception(
                            f"Duplicate entry point name '{ep_name}' for group '{group}'."
                        )
                    entry_points[group][ep_name] = ep_details
                    hidden_imports.add(ep_details["module"])

        # runtime_details = self.runtime_details

        app_details = self.to_dict()
        build_time = datetime.utcnow()
        app_details["build_info"] = {"build_time": str(build_time)}

        return {
            "app_details": app_details,
            "hidden_imports": hidden_imports,
            "resources": resources_map,
            "entry_points": entry_points,
        }

    def __repr__(self):

        return f"ProjectMetadata(main_module='{self.main_module}')"

    def to_dict(self):

        proj_meta = copy.deepcopy(self.metadata)

        result = {}
        result["main_module"] = proj_meta.get("project_main_module")
        result["metadata"] = proj_meta
        # result["globals"] = copy.deepcopy(self._globals)
        result["runtime_details"] = copy.deepcopy(self.runtime_details)
        # result["modules_details"] = copy.deepcopy(self.modules_details)
        result["other_frkl_project_versions"] = copy.deepcopy(
            self.other_frkl_project_versions
        )
        result["version"] = self.version

        return result
