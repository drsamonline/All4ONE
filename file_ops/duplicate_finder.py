from __future__ import annotations
import argparse, hashlib
from collections import defaultdict
from pathlib import Path


def file_hash(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args=None):
    p = argparse.ArgumentParser(description="Find duplicate files using size then content hash.")
    p.add_argument("directory")
    p.add_argument("--algorithm", choices=hashlib.algorithms_guaranteed, default="sha256")
    p.add_argument("--min-size", type=int, default=1)
    p.add_argument("--delete", action="store_true")
    p.add_argument("--yes", action="store_true")
    a = p.parse_args(args or [])
    root = Path(a.directory)
    if not root.is_dir():
        print("Directory not found.")
        return 1
    by_size = defaultdict(list)
    for pth in root.rglob("*"):
        if pth.is_file():
            try:
                by_size[pth.stat().st_size].append(pth)
            except OSError:
                pass
    groups = []
    for size, paths in by_size.items():
        if size < a.min_size or len(paths) < 2:
            continue
        by_hash = defaultdict(list)
        for pth in paths:
            try:
                by_hash[file_hash(pth, a.algorithm)].append(pth)
            except OSError:
                pass
        groups.extend(v for v in by_hash.values() if len(v) > 1)
    print(f"Found {len(groups)} duplicate sets.")
    for group in groups:
        print("\n".join(f"  {p}" for p in group))
        if a.delete:
            if not a.yes:
                print("Deletion requested; rerun with --yes to confirm.")
                continue
            for pth in group[1:]:
                try:
                    pth.unlink()
                    print(f"Deleted {pth}")
                except OSError as e:
                    print(f"FAILED {pth}: {e}")
    return 0
