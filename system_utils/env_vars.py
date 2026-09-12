from __future__ import annotations
import argparse, os, sys


def run(args=None):
    p = argparse.ArgumentParser(description="View or set environment variables.")
    p.add_argument("name", nargs="?")
    p.add_argument("--set", dest="value")
    p.add_argument("--system", action="store_true")
    a = p.parse_args(args or [])
    if not a.name:
        for k in sorted(os.environ):
            print(f"{k}={os.environ[k]}")
        return 0
    if a.value is None:
        print(os.environ.get(a.name, "<not set>"))
        return 0
    if a.system and sys.platform == "win32":
        import subprocess

        try:
            subprocess.run(["setx", "/M", a.name, a.value], check=False, timeout=15)
        except subprocess.TimeoutExpired:
            print("setx timed out.")
            return 1
    else:
        os.environ[a.name] = a.value
        print(f"{a.name}={a.value}")
    return 0
