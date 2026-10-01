from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(
        description="Batch rename files using placeholders {name}, {ext}, {counter}, {date}."
    )
    p.add_argument("directory")
    p.add_argument("pattern")
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--recursive", action="store_true")
    a = p.parse_args(args or [])
    root = Path(a.directory)
    if not root.is_dir():
        print("Invalid directory.")
        return 1
    files = sorted(
        (
            [x for x in root.rglob("*") if x.is_file()]
            if a.recursive
            else [x for x in root.iterdir() if x.is_file()]
        ),
        key=lambda x: str(x).lower(),
    )
    plans = []
    for i, f in enumerate(files, a.start):
        date = dt.datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
        name = a.pattern.format(name=f.stem, ext=f.suffix.lstrip("."), counter=i, date=date)
        target = f.with_name(name if Path(name).suffix else name + f.suffix)
        plans.append((f, target))
    targets = [t.resolve() for _, t in plans]
    if len(targets) != len(set(targets)):
        print("Aborted: generated names collide.")
        return 2
    for src, dst in plans:
        print(f"{src} -> {dst}")
        if not a.dry_run and src.resolve() != dst.resolve():
            if dst.exists():
                print(f"SKIP target exists: {dst}")
            else:
                src.rename(dst)
    return 0
