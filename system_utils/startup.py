from __future__ import annotations
import argparse, shutil, subprocess, sys


def run(args=None):
    p = argparse.ArgumentParser(description="List Windows startup Run keys.")
    p.add_argument("--machine", action="store_true")
    a = p.parse_args(args or [])
    if sys.platform != "win32":
        print("Windows-only tool.")
        return 3
    exe = shutil.which("reg")
    if not exe:
        print("reg not found.")
        return 3
    roots = (
        ["HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"]
        if a.machine
        else [
            "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
        ]
    )
    rc = 0
    for root in roots:
        rc = max(rc, subprocess.run([exe, "query", root], check=False).returncode)
    return rc
