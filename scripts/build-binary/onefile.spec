# -*- mode: python -*-
import json

from PyInstaller.building.build_main import Analysis

import pp
import os
import sys

from frkl.project_meta.pyinstaller import PyinstallerBuildRenderer
from frkl.project_meta import get_project_metadata

block_cipher = None

# remove tkinter dependency ( https://github.com/pyinstaller/pyinstaller/wiki/Recipe-remove-tkinter-tcl )
sys.modules["FixTk"] = None

project_dir = os.path.abspath(os.path.join(DISTPATH, "..", ".."))

with open('.frkl/project.json') as f:
    project_metadata = json.load(f)

with open('.frkl/pyinstaller/pyinstaller_args.json') as f:
    analysis_args = json.load(f)

print(project_metadata)
exe_name = project_metadata["metadata"]["project"]["exe_name"]
main_module = project_metadata["main_module"]

print("---------------------------------------------------")
print()
print(f"app name: {exe_name}")
print(f"main_module: {main_module}")
print()
print("app_meta:")
pp(project_metadata)
print()
print("analysis data:")
pp(analysis_args)
print()
print("---------------------------------------------------")

a = a = Analysis(**analysis_args)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

#a.binaries - TOC([('libtinfo.so.5', None, None)]),
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True,
)
