from __future__ import annotations

import argparse
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Split a file into numbered binary parts.")
    p.add_argument("file")
    p.add_argument("--size", type=int, default=100 * 1024 * 1024)
    p.add_argument("--output-dir")
    a = p.parse_args(args or [])
    src = Path(a.file)
    if not src.is_file() or a.size <= 0:
        print("Invalid file or size.")
        return 1
    outdir = Path(a.output_dir) if a.output_dir else src.parent
    outdir.mkdir(parents=True, exist_ok=True)
    idx = 0
    with src.open("rb") as f:
        while chunk := f.read(a.size):
            part = outdir / f"{src.name}.part{idx:04d}"
            part.write_bytes(chunk)
            print(part)
            idx += 1
    print(f"Created {idx} parts.")
    return 0
