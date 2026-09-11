# Author: Dr. Sohil Momin, BHMS
# Utility Suite 2.1.3
#
# NOTE: PyInstaller executes .spec files with exec(), which does NOT
# define __file__ in the spec's namespace - only a real Python module
# import does that. PyInstaller instead injects SPECPATH (the directory
# containing this .spec file) into the exec namespace for exactly this
# purpose. Using __file__ here fails on every platform with
# "NameError: name '__file__' is not defined" the moment PyInstaller
# tries to build - it is not a Windows-specific failure.
from pathlib import Path
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

ROOT = Path(SPECPATH).resolve()  # noqa: F821 - SPECPATH is injected by PyInstaller

a = Analysis(
    ['run.py'],
    pathex=[str(ROOT)],
    binaries=[],
    # IMPORTANT: plugins/ and config.json are intentionally NOT listed here.
    #
    # PyInstaller's `datas` always land inside the app's internal resource
    # folder (dist/utility_suite/_internal/ for a onedir build), never
    # directly beside the executable. That silently broke plugin discovery:
    # the app looks for "plugins/" next to utility_suite.exe (matching the
    # onedir layout documented in COMPILATION.md - exe, _internal/,
    # plugins/, config.json, logs/, all as siblings) so it can be dropped
    # into, edited, or replaced without rebuilding - but the plugins that
    # actually shipped were buried one level deeper, inside _internal/,
    # where the app never looked. Result: a working build that reported
    # "Total tools: 0" at runtime.
    #
    # The fix is packaging-side, not code-side: plugins/ is copied next to
    # the built executable as a post-build step (see BUILD_WINDOWS.ps1 and
    # .github/workflows/build-windows-exe.yml) so it stays a plain,
    # user-editable sibling folder, exactly as the original blueprint
    # (Section 11.3) specifies. config.json is likewise not bundled - the
    # app creates a fresh one beside the executable on first run.
    datas=[],
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
