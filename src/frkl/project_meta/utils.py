# -*- coding: utf-8 -*-
import importlib
import logging
import types
from typing import Iterable, Optional, Set

from frkl.project_meta.defaults import PROJECT_META_DEFAULT_IGNORE_MODULES


log = logging.getLogger("frkl")


def discover_installed_modules(
    ignore_modules: Optional[Iterable[str]] = None,
    only_modules: Optional[Iterable[str]] = None,
) -> Set[types.ModuleType]:
    """Method that tries to find all other (relevant) packages/base-modules which are contained in this application.

    Args:
        ignore_modules: a list of modules to ignore (to speed up parsing, defaults to in-build list)
        only_modules: if specified, only modules contained in this list are used (to speed up parsing)

    Results:
        Set[ModuleType]: a set containing all relevant (base) modules that contain a '_frkl' sub-module.
    """

    import pkg_resources

    if ignore_modules is None:
        ignore_modules = PROJECT_META_DEFAULT_IGNORE_MODULES

    installed_packages = pkg_resources.working_set

    metadata_modules: Set[types.ModuleType] = set()
    for i in installed_packages:
        pkg_name = i.key

        if pkg_name in ignore_modules:
            continue

        if only_modules is not None:
            if pkg_name not in only_modules:
                continue

        log.debug(f"querying package: {i}")

        try:
            _pkg_name = pkg_name.replace("-", "_")
            if _pkg_name in metadata_modules:
                continue
            importlib.import_module(f"{_pkg_name}._frkl")
            mod = importlib.import_module(_pkg_name)
            metadata_modules.add(mod)

        except (Exception):
            pass

    return metadata_modules
