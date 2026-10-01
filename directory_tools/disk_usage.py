from __future__ import annotations

import argparse
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Analyze directory disk usage.")
    p.add_argument("directory")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--depth", type=int, default=1)
    a = p.parse_args(args or [])
    root = Path(a.directory)
    if not root.is_dir():
        print("Directory not found.")
        return 1
    rows = []
    for f in root.rglob("*"):
        if f.is_file():
            try:
                rows.append((f.stat().st_size, f))
            except OSError:
                pass
    total = sum(s for s, _ in rows)
    print(f"Total: {total/1024**3:.2f} GiB ({total:,} bytes)")
    for size, f in sorted(rows, reverse=True)[: max(1, a.top)]:
        print(f"{size/1024**2:10.2f} MiB  {f}")
    return 0
