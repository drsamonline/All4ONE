from __future__ import annotations
import argparse, shutil, time
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Move, copy, or delete files older than N days.")
    p.add_argument("directory")
    p.add_argument("days", type=int)
    p.add_argument("--action", choices=["move", "copy", "delete"], default="move")
    p.add_argument("--dest")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--yes", action="store_true")
    a = p.parse_args(args or [])
    root = Path(a.directory)
    cutoff = time.time() - max(0, a.days) * 86400
    if not root.is_dir():
        print("Directory not found.")
        return 1
    if a.action in {"move", "copy"} and not a.dest:
        print("--dest required.")
        return 2
    if a.action == "delete" and not a.dry_run and not a.yes:
        print("Deletion requires --yes.")
        return 2
    count = 0
    for src in root.rglob("*"):
        if not src.is_file():
            continue
        try:
            old = src.stat().st_mtime < cutoff
        except OSError:
            continue
        if not old:
            continue
        if a.dry_run:
            print(f"Would {a.action}: {src}")
            count += 1
            continue
        try:
            if a.action == "delete":
                src.unlink()
            else:
                dest = Path(a.dest) / (src.relative_to(root))
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest) if a.action == "copy" else shutil.move(src, dest)
            print(f"{a.action.title()}: {src}")
            count += 1
        except OSError as e:
            print(f"FAILED {src}: {e}")
    print(f"Processed {count} files.")
    return 0
