# -*- coding: utf-8 -*-

import logging
import os
import typing
from functools import lru_cache


if typing.TYPE_CHECKING:
    from frkl.project_meta.core import ProjectMetadata

log = logging.getLogger("frkl")

"""Top-level package for frkl.project-meta."""


__author__ = """Markus Binsteiner"""
__email__ = "markus@frkl.io"


def get_version():
    from pkg_resources import DistributionNotFound, get_distribution

    try:
        # Change here if project is renamed and does not equal the package name
        dist_name = __name__
        __version__ = get_distribution(dist_name).version
    except DistributionNotFound:

        try:
            version_file = os.path.join(os.path.dirname(__file__), "version.txt")

            if os.path.exists(version_file):
                with open(version_file, encoding="utf-8") as vf:
                    __version__ = vf.read()
            else:
                __version__ = "unknown"

        except (Exception):
            pass

        if __version__ is None:
            __version__ = "unknown"

    return __version__


@lru_cache(1)
def get_project_metadata() -> "ProjectMetadata":

    try:
        from frkl.project_meta.core import ProjectMetadata

        md_obj: ProjectMetadata = ProjectMetadata(
            project_main_module="frkl.project_meta"
        )
    except Exception as e:
        log.error(f"Can't create ProjectMetadata: {e}")
        raise e

    return md_obj
