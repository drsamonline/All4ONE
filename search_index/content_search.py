from __future__ import annotations
import argparse, re
from pathlib import Path

TEXT_EXTS = {
    ".txt",
    ".md",
    ".py",
    ".json",
    ".csv",
    ".xml",
    ".html",
    ".htm",
    ".ini",
    ".cfg",
    ".log",
    ".yaml",
    ".yml",
    ".toml",
    ".sql",
    ".js",
    ".css",
}


def run(args=None):
    p = argparse.ArgumentParser(description="Search text content recursively.")
    p.add_argument("directory")
    p.add_argument("query")
    p.add_argument("--ignore-case", action="store_true")
    p.add_argument("--extensions", help="comma-separated extensions")
    p.add_argument("--limit", type=int, default=200)
    a = p.parse_args(args or [])
    root = Path(a.directory)
    exts = (
        {x if x.startswith(".") else "." + x for x in a.extensions.split(",")} if a.extensions else TEXT_EXTS
    )
    flags = re.IGNORECASE if a.ignore_case else 0
    pat = re.compile(a.query, flags)
    hits = 0
    for f in root.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in exts:
            continue
        try:
            with f.open("r", encoding="utf-8", errors="replace") as h:
                for n, line in enumerate(h, 1):
                    if pat.search(line):
                        print(f"{f}:{n}:{line.rstrip()}")
                        hits += 1
                    if hits >= a.limit:
                        return 0
        except OSError:
            continue
    print(f"Found {hits} matching lines.")
    return 0
