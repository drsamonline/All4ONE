from __future__ import annotations
import shutil, subprocess, sys


def run(args=None):
    if sys.platform != "win32":
        print("Windows-only tool.")
        return 3
    exe = shutil.which("regedit") or r"C:\Windows\regedit.exe"
    return subprocess.Popen([exe]).wait() if exe else 3
