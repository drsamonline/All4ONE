"""Random data file generator (sparse-safe, chunked) for benchmarking tools."""
from __future__ import annotations

import argparse
import datetime
import os
import sys
import secrets

SIZE_SUFFIXES = {"b": 1, "kb": 10**3, "mb": 10**6, "gb": 10**9, "kib": 2**10,
                 "mib": 2**20, "gib": 2**30}


def _parse_size(text):
    text = text.strip().lower()
    for suf in sorted(SIZE_SUFFIXES, key=len, reverse=True):
        if text.endswith(suf):
            try:
                return int(float(text[: -len(suf)].strip()) * SIZE_SUFFIXES[suf])
            except ValueError:
                return None
    try:
        return int(text)
    except ValueError:
        return None


def run(args=None):
    p = argparse.ArgumentParser(description="Generate a cryptographically-random file of a given size.")
    p.add_argument("size", help="Bytes or suffix: 512, 64KB, 5MiB, 2GB ...")
    p.add_argument("-o", "--out", help="Output path (default: rand_<timestamp>.bin).")
    p.add_argument("--chunk", type=int, default=1024 * 1024, help="Chunk size in bytes (default 1 MiB).")
    a = p.parse_args(args or [])

    total = _parse_size(a.size)
    if total is None or total <= 0:
        print(f"Invalid size: {a.size!r}")
        return 2
    if a.chunk < 1:
        print("--chunk must be >= 1")
        return 2

    out = a.out or f"rand_{datetime.datetime.now():%Y%m%d_%H%M%S}.bin"
    written = 0
    try:
        with open(out, "wb") as fh:
            while written < total:
                n = min(a.chunk, total - written)
                fh.write(secrets.token_bytes(n))
                written += n
    except OSError as exc:
        print(f"Write failed: {exc}")
        return 1
    print(f"Wrote {written:,} bytes ({written / 1024 / 1024:.2f} MiB) to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
