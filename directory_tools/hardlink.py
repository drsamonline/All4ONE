from __future__ import annotations

import argparse
import hashlib
import os
from collections import defaultdict
from pathlib import Path


def h(path):
    x = hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            x.update(c)
    return x.digest()


def run(args=None):
    p = argparse.ArgumentParser(description="Replace identical files with hardlinks.")
    p.add_argument("directory")
    p.add_argument("--yes", action="store_true")
    p.add_argument("--min-size", type=int, default=1)
    a = p.parse_args(args or [])
    if not a.yes:
        print("Hardlink replacement is destructive to directory structure; rerun with --yes.")
        return 2
    root = Path(a.directory)
    groups = defaultdict(list)
    for f in root.rglob("*"):
        if f.is_file():
            try:
                s = f.stat()
                if s.st_size >= a.min_size:
                    groups[s.st_size].append(f)
            except OSError:
                pass
    changed = 0
    for paths in groups.values():
        hashes = defaultdict(list)
        for f in paths:
            try:
                hashes[h(f)].append(f)
            except OSError:
                pass
        for group in hashes.values():
            if len(group) < 2:
                continue
            keeper = group[0]
            for dup in group[1:]:
                try:
                    if os.stat(keeper).st_dev != os.stat(dup).st_dev:
                        continue
                    tmp = dup.with_suffix(dup.suffix + ".us_tmp")
                    dup.replace(tmp)
                    os.link(keeper, tmp)
                    tmp.replace(dup)
                    changed += 1
                    print(f"Hardlinked {dup} -> {keeper}")
                except OSError as e:
                    print(f"FAILED {dup}: {e}")
    print(f"Created {changed} hardlinks.")
    return 0
