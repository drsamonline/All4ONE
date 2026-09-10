from __future__ import annotations
import argparse, shutil, subprocess, sys


def run(args=None):
    p = argparse.ArgumentParser(description="Launch Windows Disk Cleanup.")
    p.add_argument("--sagerun", type=int)
    a = p.parse_args(args or [])
    if sys.platform != "win32":
        print("Windows-only tool.")
        return 3
    exe = shutil.which("cleanmgr")
    if not exe:
        print("cleanmgr not found.")
        return 3
    cmd = [exe]
    if a.sagerun is not None:
        cmd.append(f"/sagerun:{a.sagerun}")
    return subprocess.Popen(cmd).wait()
