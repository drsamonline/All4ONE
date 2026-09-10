# Author: Dr. Sohil Momin
# Utility Suite 2.1.3
from pathlib import Path
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

ROOT = Path(__file__).resolve().parent

a = Analysis(
    ['run.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ROOT / 'plugins'), 'plugins'), (str(ROOT / 'config.json'), '.')],
    hiddenimports=['tkinter', 'tkinter.ttk'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'unittest'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='utility_suite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='utility_suite',
)
