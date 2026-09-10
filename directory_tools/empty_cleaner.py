from __future__ import annotations
import argparse
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Remove empty directories.")
    p.add_argument("directory")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(args or [])
    root = Path(a.directory)
    if not root.is_dir():
        print("Directory not found.")
        return 1
    count = 0
    for d in sorted((x for x in root.rglob("*") if x.is_dir()), key=lambda x: len(x.parts), reverse=True):
        try:
            if not any(d.iterdir()):
                print(f"{'Would remove' if a.dry_run else 'Removing'}: {d}")
                if not a.dry_run:
                    d.rmdir()
                count += 1
        except OSError:
            continue
    print(f"Empty directories: {count}")
    return 0
