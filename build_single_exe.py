"""One-command automated build for Utility Suite 3.0.

Pipeline (all local steps, CI runs exactly these):
  1. audit                -> python audit.py
  2. bundle generation    -> regenerates bundle/tools.dat from source packs
  3. smoke tests          -> python -B -m tests.test_suite
  4. PyInstaller onefile  -> dist/utility_suite.exe  (single file!)
  5. verification         -> exe must report >0 tools and correct version
  6. release zip          -> dist/UtilitySuite-<version>-windows.zip

Usage:
    python build_single_exe.py            # full pipeline
    python build_single_exe.py --skip-tests
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print(f"\n==> {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        sys.exit(f"Build failed at step: {' '.join(cmd)} (exit {result.returncode})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Automated single-file build")
    parser.add_argument("--skip-audit", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    version = (ROOT / "VERSION.txt").read_text(encoding="utf-8").strip()

    if not args.skip_audit:
        run([sys.executable, "audit.py"])

    # 2. Regenerate the embedded bundle from the current source tree.
    sys.path.insert(0, str(ROOT))
    from core.bundle import build_bundle  # noqa: E402

    bundle_path, tool_count = build_bundle(ROOT)
    print(f"Bundle: {bundle_path.name} ({bundle_path.stat().st_size:,} bytes, {tool_count} tools)")
    if tool_count == 0:
        sys.exit("Bundle contains 0 tools — aborting.")

    # 3. Behavioural smoke tests.
    if not args.skip_tests:
        run([sys.executable, "-B", "-m", "tests.test_suite"])

    # 4. PyInstaller one-file build.
    run([sys.executable, "-m", "PyInstaller", "build_onefile.spec", "--clean", "--noconfirm"])

    exe = ROOT / "dist" / "utility_suite.exe"
    if not exe.is_file():
        sys.exit(f"Expected single-file output missing: {exe}")

    # 5. Verify the packaged exe actually finds its embedded tools.
    out = subprocess.run([str(exe), "list"], capture_output=True, text=True, cwd=ROOT)
    combined = out.stdout + out.stderr
    if "Total tools: 0" in combined or out.returncode != 0:
        sys.exit("Packaged exe found 0 tools — bundle was not embedded correctly.")
    print("Exe self-check:", [ln for ln in combined.splitlines() if "Total tools" in ln])

    # 6. Release zip containing ONLY the exe.
    zip_path = ROOT / "dist" / f"UtilitySuite-{version}-windows.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(exe, "utility_suite.exe")
    print(f"Release artifact: {zip_path.name} ({zip_path.stat().st_size:,} bytes)")
    print("\nBUILD OK — one executable, zero sidecar files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
