from __future__ import annotations
import argparse
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Count lines, words, and characters.")
    p.add_argument("file")
    a = p.parse_args(args or [])
    path = Path(a.file)
    if not path.is_file():
        print(
            f"Not a regular file (is it a directory?): {path}" if path.exists() else f"File not found: {path}"
        )
        return 1
    data = path.read_text(encoding="utf-8", errors="replace")
    print(f"Characters: {len(data):,}\nWords: {len(data.split()):,}\nLines: {len(data.splitlines()):,}")
    return 0
