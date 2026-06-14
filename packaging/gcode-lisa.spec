# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_submodules


project_root = Path.cwd()
if project_root.name == "packaging":
    project_root = project_root.parent

assets_datas = [
    (str(project_root / "assets"), "assets"),
]

hiddenimports = collect_submodules("PyQt6")

icons_dir = project_root / "assets" / "icons"

if sys.platform.startswith("win"):
    icon_path = icons_dir / "gcode-lisa.ico"
elif sys.platform == "darwin":
    icon_path = icons_dir / "gcode-lisa.icns"
else:
    icon_path = icons_dir / "gcode-lisa-256.png"

if not icon_path.exists():
    raise FileNotFoundError(icon_path)


a = Analysis(
    [str(project_root / "src" / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=assets_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="gcode-lisa",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(icon_path),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="gcode-lisa",
)