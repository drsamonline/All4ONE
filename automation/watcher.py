from __future__ import annotations

import argparse
import time
from pathlib import Path


def _snapshot(root):
    return {
        str(p.relative_to(root)): (p.stat().st_mtime, p.stat().st_size)
        for p in root.rglob("*")
        if p.is_file()
    }


def run(args=None):
    p = argparse.ArgumentParser(description="Watch a directory for file changes.")
    p.add_argument("directory")
    p.add_argument("--interval", type=float, default=2.0)
    p.add_argument("--once", action="store_true")
    a = p.parse_args(args or [])
    root = Path(a.directory).resolve()
    if not root.is_dir():
        print("Directory not found.")
        return 1
    before = _snapshot(root)
    print(f"Watching {root} ...")
    while True:
        time.sleep(max(0.2, a.interval))
        after = _snapshot(root)
        for k in sorted(after.keys() - before.keys()):
            print(f"ADDED   {k}")
        for k in sorted(before.keys() - after.keys()):
            print(f"REMOVED {k}")
        for k in sorted(after.keys() & before.keys()):
            if after[k] != before[k]:
                print(f"CHANGED {k}")
        before = after
        if a.once:
            break
    return 0
