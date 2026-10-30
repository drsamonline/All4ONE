"""Build the single-file binary.

    python build.py                audit -> sweep -> PyInstaller onefile -> zip
    python build.py --skip-tests   skip the sweep (audit still runs)

Produces, in dist/:
    All4one.exe                       the portable binary (Windows)
    All4one-<version>-windows.zip     the release download
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
APP = "All4one"

# Qt modules this app never touches — excluding them keeps the binary lean.
EXCLUDES = [
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtWebChannel", "PySide6.QtWebSockets", "PySide6.QtQuick", "PySide6.QtQuick3D",
    "PySide6.QtQml", "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.QtCharts",
    "PySide6.QtDataVisualization", "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
    "PySide6.QtBluetooth", "PySide6.QtNfc", "PySide6.QtPositioning", "PySide6.QtSql",
    "PySide6.QtTest", "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtPdf",
    "PySide6.QtSerialPort", "PySide6.QtSensors", "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets",
    "PySide6.QtNetworkAuth", "PySide6.QtRemoteObjects", "PySide6.QtScxml", "PySide6.QtStateMachine",
    "tkinter", "unittest", "pydoc", "doctest", "test",
]


def read_version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def step(title: str) -> None:
    print(f"\n=== {title} " + "=" * max(0, 60 - len(title)))


def run(args: list[str], **kwargs) -> None:
    print("$", " ".join(args))
    subprocess.run(args, check=True, cwd=ROOT, **kwargs)


def make_icon() -> Path | None:
    """Draw the app icon at build time — no binary asset in the repository."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    size = 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([8, 8, size - 8, size - 8], radius=56, fill=(109, 140, 255, 255))
    unit = (size - 64) // 4
    for row in range(2):
        for column in range(2):
            x = 40 + column * (unit + 24)
            y = 40 + row * (unit + 24)
            draw.rounded_rectangle([x, y, x + unit, y + unit], radius=14,
                                   outline=(255, 255, 255, 235), width=13)
    ico = assets / "all4one.ico"
    image.save(ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    image.save(assets / "all4one.png")
    return ico


def write_version_info(version: str) -> Path:
    parts = (version.split(".") + ["0", "0", "0"])[:4]
    numbers = ", ".join(str(int(part)) if part.isdigit() else "0" for part in parts)
    content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({numbers}), prodvers=({numbers}),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)
  ),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'Dr. Sohil Momin'),
      StringStruct('FileDescription', 'All4one — one portable utility'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('InternalName', 'All4one'),
      StringStruct('LegalCopyright', 'PolyForm Noncommercial 1.0.0'),
      StringStruct('OriginalFilename', 'All4one.exe'),
      StringStruct('ProductName', 'All4one'),
      StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    target = BUILD / "version_info.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def main() -> int:
    skip_tests = "--skip-tests" in sys.argv
    version = read_version()
    print(f"All4one {version} — building the single-file binary")

    step("Clean working tree")
    for cache in ROOT.rglob("__pycache__"):
        if ".git" not in cache.parts:
            shutil.rmtree(cache, ignore_errors=True)
    for stray in ROOT.rglob("*.pyc"):
        if ".git" not in stray.parts:
            stray.unlink(missing_ok=True)
    print("removed __pycache__ and .pyc files")

    step("Audit")
    run([sys.executable, "scripts/audit.py"])

    if not skip_tests:
        step("Behavioural sweep")
        run([sys.executable, "tests/sweep.py"])

    step("Catalogue and landing page")
    run([sys.executable, "scripts/catalogue.py"])
    run([sys.executable, "scripts/landing.py"])

    step("Icon and version resource")
    icon = make_icon()
    version_file = write_version_info(version)

    step("PyInstaller onefile")
    DIST.mkdir(exist_ok=True)
    args = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
        "--windowed" if os.name == "nt" else "--console",
        "--name", APP,
        "--collect-submodules", "tools",
        "--collect-submodules", "core",
        "--collect-submodules", "ui",
        "--add-data", f"{ROOT / 'TOOL_CATALOG.md'}{os.pathsep}.",
        "--distpath", str(DIST), "--workpath", str(BUILD / "pyinstaller"),
        "--specpath", str(BUILD),
    ]
    for module in EXCLUDES:
        args += ["--exclude-module", module]
    if icon and os.name == "nt":
        args += ["--icon", str(icon)]
    if os.name == "nt" and version_file.exists():
        args += ["--version-file", str(version_file)]
    args.append(str(ROOT / "main.py"))
    run(args)

    step("Verify the binary")
    binary = DIST / (APP + (".exe" if os.name == "nt" else ""))
    if not binary.exists():
        raise SystemExit(f"build failed: {binary} was not produced")
    listing = subprocess.run([str(binary), "list"], capture_output=True, text=True, timeout=180)
    if listing.returncode != 0 or "tools" not in listing.stdout.lower():
        raise SystemExit(f"the built binary did not respond to 'list':\n{listing.stderr[:600]}")
    tool_count = listing.stdout.count("  ")
    print(f"binary responds to 'list' ({len(listing.stdout.splitlines())} lines, "
          f"{binary.stat().st_size / 1_048_576:.0f} MB)")

    step("Package the release zip")
    suffix = "windows" if os.name == "nt" else sys.platform
    archive = DIST / f"All4one-{version}-{suffix}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(binary, binary.name)
        bundle.writestr("README-FIRST.txt",
                        "All4one " + version + "\n\n"
                        "Run All4one.exe. Nothing to install: no installer, no registry\n"
                        "entries, no background service. Keep it in any folder or on a\n"
                        "USB stick.\n\n"
                        "The window opens with every tool available. 'Dependencies' in\n"
                        "the app lists the optional extras (FFmpeg, Tesseract, Pillow and\n"
                        "so on) and what each one unlocks — none of them are required.\n\n"
                        "Command line, same binary:\n"
                        "    All4one.exe list\n"
                        "    All4one.exe search pdf\n"
                        "    All4one.exe show pdf-merge\n"
                        "    All4one.exe run hash-file --file report.pdf\n")
    print(f"\nDone.\n  {binary}\n  {archive} "
          f"({archive.stat().st_size / 1_048_576:.0f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
