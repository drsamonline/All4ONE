from __future__ import annotations
import argparse
from pathlib import Path

JUNK_EXTENSIONS = {".tmp", ".bak", ".old", ".chk", ".dmp", ".~", ".cache"}


def run(args=None):
    p = argparse.ArgumentParser(description="Find common junk files.")
    p.add_argument("directory", nargs="?", default=".")
    p.add_argument("--min-size", type=int, default=0)
    a = p.parse_args(args or [])
    found = []
    for f in Path(a.directory).rglob("*"):
        if f.is_file() and f.suffix.lower() in JUNK_EXTENSIONS:
            try:
                if f.stat().st_size >= a.min_size:
                    found.append(f)
            except OSError:
                pass
    print(f"Found {len(found)} candidate junk files.")
    [print(f"  {x}") for x in found]
    return 0
