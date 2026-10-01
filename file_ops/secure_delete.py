from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


def _overwrite(path):
    n = path.stat().st_size
    with path.open("r+b", buffering=0) as f:
        remaining = n
        block = os.urandom(min(1024 * 1024, max(1, n))) if n else b""
        while remaining:
            chunk = block if len(block) <= remaining else block[:remaining]
            f.write(chunk)
            remaining -= len(chunk)
        f.flush()
        os.fsync(f.fileno())


def run(args=None):
    p = argparse.ArgumentParser(description="Securely delete files when supported; use with care.")
    p.add_argument("files", nargs="+")
    p.add_argument("--use-sdelete", action="store_true")
    p.add_argument("--passes", type=int, default=1)
    p.add_argument("--yes", action="store_true")
    a = p.parse_args(args or [])
    if not a.yes:
        print("Destructive action blocked. Rerun with --yes.")
        return 2
    for raw in a.files:
        path = Path(raw)
        if not path.is_file():
            print(f"SKIP not a file: {path}")
            continue
        try:
            if a.use_sdelete and shutil.which("sdelete"):
                r = subprocess.run(
                    ["sdelete", "-p", str(max(1, a.passes)), "-accepteula", str(path)], check=False
                )
                returncode = r.returncode
                if returncode:
                    print(f"sdelete failed for {path}")
                    return 1
            else:
                for _ in range(max(1, a.passes)):
                    _overwrite(path)
                path.unlink()
            print(f"Deleted {path}")
        except OSError as e:
            print(f"FAILED {path}: {e}")
            return 1
    return 0
