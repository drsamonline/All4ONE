"""Recursive directory tree printer with sizes, depth limits and ASCII output."""
from __future__ import annotations

import argparse
import os


def _human(n):
    for unit in ("B", "K", "M", "G", "T"):
        if n < 1024 or unit == "T":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}T"


def run(args=None):
    p = argparse.ArgumentParser(description="Print a directory tree like the classic 'tree' command.")
    p.add_argument("path", nargs="?", default=".", help="Root directory (default: current).")
    p.add_argument("--depth", type=int, default=4, metavar="N", help="Maximum levels to descend.")
    p.add_argument("--dirs", action="store_true", help="Directories only.")
    p.add_argument("--sizes", action="store_true", help="Show file/dir sizes.")
    p.add_argument("--limit", type=int, default=2000, metavar="N", help="Max entries printed.")
    a = p.parse_args(args or [])

    root = os.path.abspath(a.path)
    if not os.path.isdir(root):
        print(f"Not a directory: {root}")
        return 1

    printed = [0]
    shown_total = [0]

    def dir_size(path):
        total = 0
        for dp, _dn, fn in os.walk(path):
            for f in fn:
                try:
                    total += os.path.getsize(os.path.join(dp, f))
                except OSError:
                    pass
        return total

    def walk(path, prefix, level):
        if printed[0] >= a.limit:
            return
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
        except OSError as exc:
            print(f"{prefix}! {exc}")
            return
        if a.dirs:
            entries = [e for e in entries if e.is_dir(follow_symlinks=False)]
        shown_total[0] += len(entries)
        for i, entry in enumerate(entries):
            if printed[0] >= a.limit:
                print(f"{prefix}... (truncated at {a.limit} entries)")
                return
            last = i == len(entries) - 1
            connector = "`-- " if last else "|-- "
            size = ""
            if a.sizes:
                if entry.is_dir(follow_symlinks=False):
                    size = f"  [{_human(dir_size(entry.path))}]"
                else:
                    try:
                        size = f"  [{_human(entry.stat(follow_symlinks=False).st_size)}]"
                    except OSError:
                        size = ""
            print(f"{prefix}{connector}{entry.name}/" if entry.is_dir(follow_symlinks=False)
                  else f"{prefix}{connector}{entry.name}{size}")
            printed[0] += 1
            if entry.is_dir(follow_symlinks=False) and level < a.depth:
                walk(entry.path, prefix + ("    " if last else "|   "), level + 1)

    print(root)
    walk(root, "", 1)
    dirs = sum(1 for dp, dn, fn in os.walk(root) for d in dn) if not a.dirs else shown_total[0]
    files = sum(len(fn) for _, __, fn in os.walk(root))
    print(f"\n{dirs} directories, {files} files (printed {min(printed[0], a.limit)})")
    return 0
