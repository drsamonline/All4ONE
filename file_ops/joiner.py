from __future__ import annotations

import argparse
import glob
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Join binary parts in lexical order.")
    p.add_argument("pattern")
    p.add_argument("output")
    p.add_argument("--overwrite", action="store_true")
    a = p.parse_args(args or [])
    parts = [Path(x) for x in sorted(glob.glob(a.pattern))]
    if not parts:
        print("No parts found.")
        return 1
    out = Path(a.output)
    if out.exists() and not a.overwrite:
        print("Output exists; use --overwrite.")
        return 2
    with out.open("wb") as dst:
        for part in parts:
            with part.open("rb") as src:
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    dst.write(chunk)
    print(f"Joined {len(parts)} parts into {out}")
    return 0
