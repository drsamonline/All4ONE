from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Synchronize source to destination.")
    p.add_argument("source")
    p.add_argument("destination")
    p.add_argument("--delete", action="store_true", help="Delete destination files not present in source")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(args or [])
    src, dst = Path(a.source), Path(a.destination)
    if not src.is_dir():
        print("Source not found.")
        return 1
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.rglob("*"):
        rel = f.relative_to(src)
        target = dst / rel
        if f.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        try:
            changed = not target.exists() or not filecmp.cmp(f, target, shallow=False)
        except OSError:
            changed = True
        if changed:
            print(f"COPY {f} -> {target}")
            if not a.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)
    if a.delete:
        for f in sorted(dst.rglob("*"), key=lambda x: len(x.parts), reverse=True):
            rel = f.relative_to(dst)
            if not (src / rel).exists():
                print(f"DELETE {f}")
                if not a.dry_run:
                    f.rmdir() if f.is_dir() else f.unlink()
    return 0
