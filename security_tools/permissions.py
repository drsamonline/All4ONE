from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys


def run(args=None):
    p = argparse.ArgumentParser(description="Change basic file permissions.")
    p.add_argument("path")
    p.add_argument("--mode", help="POSIX octal mode, e.g. 644")
    p.add_argument("--read-only", action="store_true")
    p.add_argument("--writable", action="store_true")
    a = p.parse_args(args or [])
    if sys.platform == "win32" and (a.read_only or a.writable):
        if not shutil.which("attrib"):
            print("attrib not found.")
            return 3
        cmd = ["attrib", "+R" if a.read_only else "-R", a.path]
        return subprocess.run(cmd, check=False).returncode
    if a.mode:
        os.chmod(a.path, int(a.mode, 8))
        print(f"Permissions changed: {a.path} -> {a.mode}")
        return 0
    print(f"Mode: {stat.filemode(os.stat(a.path).st_mode)}")
    return 0
