"""File Integrity Baseline - record a SHA-256 hash to detect later tampering."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def run(args):
    ap = argparse.ArgumentParser(description="Create a SHA-256 integrity baseline for a file.")
    ap.add_argument("path")
    ap.add_argument("--output")
    a = ap.parse_args(args)
    p = Path(a.path)
    if not p.exists():
        print(f"Not found: {p}")
        return 1
    if not p.is_file():
        print(f"Not a regular file (is it a directory?): {p}")
        return 1
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    line = f"{h.hexdigest()}  {p.resolve()}\n"
    if a.output:
        Path(a.output).write_text(line, encoding="utf-8")
        print(f"Wrote integrity baseline: {a.output}")
    else:
        print(line, end="")
    return 0
