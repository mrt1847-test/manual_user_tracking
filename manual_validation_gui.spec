from pathlib import Path

from PyInstaller.building.build_main import Analysis, EXE, PYZ


project_root = Path(SPECPATH)

datas = [(str(project_root / "config.json"), ".")]

for path in (project_root / "tracking_schemas").rglob("*"):
    if path.is_file():
        target_dir = path.parent.relative_to(project_root)
        datas.append((str(path), str(target_dir)))


a = Analysis(
    [str(project_root / "manual_validation_gui.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name="TrackingManualValidator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
