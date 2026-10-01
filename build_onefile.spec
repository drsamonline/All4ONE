# Author: Dr. Sohil Momin, BHMS
# Utility Suite 3.0 — SINGLE-FILE build.
#
# Everything ships inside ONE utility_suite.exe:
#   * the Python interpreter + core runtime (PyInstaller onefile),
#   * bundle/tools.dat — all 45+ tool packs and the catalog.json metadata,
#     embedded via PyInstaller `datas` and read from the _MEIPASS temp dir
#     at runtime (see core/bundle.py).
# No plugins/ folder, no separate config file, no external databases are
# required for a working release. The exe is fully portable & standalone.
#
# Build with:  python build_single_exe.py        (regenerates the bundle
# first, then invokes PyInstaller with this spec.)
#
# NOTE: PyInstaller executes .spec files with exec(); SPECPATH (the directory
# containing this .spec) is injected by PyInstaller — __file__ is NOT defined.
from pathlib import Path

from PyInstaller.building.build_main import Analysis, EXE, PYZ

ROOT = Path(SPECPATH).resolve()  # noqa: F821 - injected by PyInstaller
BUNDLE = ROOT / "bundle" / "tools.dat"

if not BUNDLE.is_file():
    raise SystemExit(
        f"Missing {BUNDLE} — run 'python build_single_exe.py' instead of "
        "calling PyInstaller directly, so the embedded tool bundle is "
        "generated before packaging."
    )

a = Analysis(
    ["run.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(BUNDLE), "bundle")],  # lands in _MEIPASS/bundle/tools.dat at runtime
    hiddenimports=["tkinter", "tkinter.ttk", "zipimport"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "unittest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="utility_suite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,  # unpack to a temp dir per run -> truly single file
    console=True,         # keep CLI mode working; GUI launches with no args
    disable_windowed_traceback=False,
)
