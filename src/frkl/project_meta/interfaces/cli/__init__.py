# -*- coding: utf-8 -*-
import json
from pathlib import Path

import asyncclick as click
from frkl.project_meta.core import ProjectMetadata
from frkl.project_meta.pyinstaller import PyinstallerBuildRenderer


click.anyio_backend = "asyncio"


@click.group()
@click.pass_context
def cli(ctx):

    pass


@cli.command()
@click.argument("main_module", nargs=1)
def update_project_metadata(main_module: str):

    md_obj: ProjectMetadata = ProjectMetadata(project_main_module=main_module)
    md_json = json.dumps(
        md_obj.to_dict(), sort_keys=True, indent=2, separators=(",", ": ")
    )
    renderer = PyinstallerBuildRenderer(md_obj)
    analysis_args = renderer.create_analysis_args()

    aa_json = json.dumps(
        analysis_args, sort_keys=True, indent=2, separators=(",", ": ")
    )

    base_dir = Path(".")

    md_dir = base_dir / ".frkl"

    md_dir.mkdir(parents=True, exist_ok=True)

    md_file = md_dir / "project.json"
    aa_file = md_dir / "pyinstaller-args.json"

    print(f"Writing metadata to: {md_file.as_posix()}")
    md_file.write_text(md_json)
    print(f"Writing build info to: {aa_file.as_posix()}")
    aa_file.write_text(aa_json)


@cli.command()
@click.argument("main_module", nargs=1)
@click.pass_context
def metadata(ctx, main_module: str):

    md_obj: ProjectMetadata = ProjectMetadata(project_main_module=main_module)

    md_json = json.dumps(
        md_obj.to_dict(), sort_keys=True, indent=2, separators=(",", ": ")
    )
    print(md_json)


@cli.command()
@click.argument("main_module", nargs=1)
@click.pass_context
def runtime_info(ctx, main_module: str):

    md_obj: ProjectMetadata = ProjectMetadata(project_main_module=main_module)

    md_json = json.dumps(
        md_obj.runtime_details, sort_keys=True, indent=2, separators=(",", ": ")
    )
    print(md_json)


@cli.command()
@click.argument("main_module", nargs=1)
@click.pass_context
def pyinstaller_args(ctx, main_module: str):

    md_obj: ProjectMetadata = ProjectMetadata(project_main_module=main_module)
    renderer = PyinstallerBuildRenderer(md_obj)
    analysis_args = renderer.create_analysis_args()

    md_json = json.dumps(
        analysis_args, sort_keys=True, indent=2, separators=(",", ": ")
    )
    print(md_json)


if __name__ == "__main__":
    cli()
