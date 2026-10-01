from __future__ import annotations

import argparse
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Display a hexadecimal file view.")
    p.add_argument("file")
    p.add_argument("--bytes", type=int, default=256)
    p.add_argument("--offset", type=int, default=0)
    a = p.parse_args(args or [])
    path = Path(a.file)
    if not path.is_file():
        print(
            f"Not a regular file (is it a directory?): {path}" if path.exists() else f"File not found: {path}"
        )
        return 1
    with path.open("rb") as f:
        f.seek(max(0, a.offset))
        data = f.read(max(0, a.bytes))
    for off in range(0, len(data), 16):
        chunk = data[off : off + 16]
        hx = " ".join(f"{b:02x}" for b in chunk)
        ascii_ = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"{a.offset+off:08x}  {hx:<47}  {ascii_}")
    return 0
