from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Export third-party Windows drivers with pnputil.")
    p.add_argument("dest")
    a = p.parse_args(args or [])
    if sys.platform != "win32":
        print("Windows-only tool.")
        return 3
    exe = shutil.which("pnputil")
    if not exe:
        print("pnputil not found.")
        return 3
    Path(a.dest).mkdir(parents=True, exist_ok=True)
    try:
        return subprocess.run([exe, "/export-driver", "*", a.dest], check=False, timeout=120).returncode
    except subprocess.TimeoutExpired:
        print("Driver export timed out.")
        return 1
