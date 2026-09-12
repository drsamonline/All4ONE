from __future__ import annotations
import argparse, shutil, subprocess, sys


def run(args=None):
    p = argparse.ArgumentParser(description="Query or control Windows services.")
    p.add_argument("action", choices=["query", "start", "stop", "pause", "continue"])
    p.add_argument("service_name")
    a = p.parse_args(args or [])
    if sys.platform != "win32":
        print("Windows-only tool.")
        return 3
    exe = shutil.which("sc")
    if not exe:
        print("sc not found.")
        return 3
    try:
        return subprocess.run([exe, a.action, a.service_name], check=False, timeout=20).returncode
    except subprocess.TimeoutExpired:
        print("sc command timed out.")
        return 1
