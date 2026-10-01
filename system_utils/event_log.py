from __future__ import annotations

import argparse
import shutil
import subprocess
import sys


def run(args=None):
    p = argparse.ArgumentParser(description="Query Windows Event Logs.")
    p.add_argument("--log", "-l", default="System")
    p.add_argument("--max-events", type=int, default=20)
    p.add_argument("--level")
    a = p.parse_args(args or [])
    if sys.platform != "win32":
        print("Windows-only tool.")
        return 3
    exe = shutil.which("wevtutil")
    if not exe:
        print("wevtutil not found.")
        return 3
    cmd = [exe, "qe", a.log, "/c:" + str(a.max_events), "/f:text", "/rd:true"]
    try:
        return subprocess.run(cmd, check=False, timeout=20).returncode
    except subprocess.TimeoutExpired:
        print("wevtutil timed out.")
        return 1
