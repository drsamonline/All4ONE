from __future__ import annotations
import argparse, tempfile
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Clean temporary files.")
    p.add_argument("--directory")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(args or [])
    root = Path(a.directory or tempfile.gettempdir())
    files = 0
    bytes_ = 0
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        try:
            size = f.stat().st_size
            if a.dry_run:
                print(f"Would delete: {f}")
            else:
                f.unlink()
            files += 1
            bytes_ += size
        except OSError:
            continue
    print(f"Processed {files} files ({bytes_/1024**2:.2f} MiB).")
    return 0
