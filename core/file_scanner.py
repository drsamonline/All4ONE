"""Streaming filesystem helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator


def scan_files(
    root: str | os.PathLike[str],
    exclude_dirs: set[str] | None = None,
    exclude_patterns: list[str] | None = None,
    skip_hidden: bool = True,
) -> Iterator[str]:
    root_path = Path(root)
    excludes = set(exclude_dirs or ())
    patterns = [p.lower() for p in (exclude_patterns or ())]
    for current, dirs, files in os.walk(root_path, topdown=True):
        dirs[:] = [
            d
            for d in dirs
            if d not in excludes
            and not (skip_hidden and d.startswith("."))
            and d not in {"$RECYCLE.BIN", "System Volume Information"}
        ]
        for filename in files:
            if skip_hidden and filename.startswith("."):
                continue
            if any(filename.lower().endswith(p) for p in patterns):
                continue
            yield str(Path(current) / filename)


def get_file_info(path: str | os.PathLike[str]) -> dict[str, object]:
    p = Path(path)
    stat = p.stat()
    return {
        "path": str(p),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "ctime": stat.st_ctime,
        "extension": p.suffix.lower(),
    }
