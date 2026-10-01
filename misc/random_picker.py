from __future__ import annotations

import argparse
import random
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Pick a random file from a folder.")
    p.add_argument("directory")
    p.add_argument("--recursive", action="store_true")
    a = p.parse_args(args or [])
    root = Path(a.directory)
    files = [x for x in (root.rglob("*") if a.recursive else root.iterdir()) if x.is_file()]
    if not files:
        print("No files found.")
        return 1
    chosen = random.choice(files)
    print(chosen)
    return 0
