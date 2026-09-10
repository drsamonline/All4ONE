from __future__ import annotations
import argparse, shutil
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Organize files into folders by extension, date, or size.")
    p.add_argument("directory")
    p.add_argument("--by", choices=["extension", "date", "size"], default="extension")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(args or [])
    root = Path(a.directory)
    if not root.is_dir():
        print("Directory not found.")
        return 1
    items = (
        [x for x in root.rglob("*") if x.is_file()]
        if a.recursive
        else [x for x in root.iterdir() if x.is_file()]
    )
    count = 0
    for f in items:
        try:
            if a.by == "extension":
                key = f.suffix.lower().lstrip(".") or "no-extension"
            elif a.by == "date":
                key = __import__("datetime").datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m")
            else:
                n = f.stat().st_size
                key = (
                    "empty"
                    if n == 0
                    else ("small" if n < 1_048_576 else "medium" if n < 100 * 1_048_576 else "large")
                )
            dest = f.parent / key / f.name
            if dest.resolve() == f.resolve():
                continue
            print(f"{'Would move' if a.dry_run else 'Move'}: {f} -> {dest}")
            if not a.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(f), str(dest))
            count += 1
        except OSError as e:
            print(f"FAILED {f}: {e}")
    print(f"Processed {count} files.")
    return 0
