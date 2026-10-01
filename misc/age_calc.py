from __future__ import annotations

import argparse
import datetime as dt
import time
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Show file age and timestamps.")
    p.add_argument("file")
    a = p.parse_args(args or [])
    f = Path(a.file)
    st = f.stat()
    age = max(0, time.time() - st.st_mtime)
    print(
        f'File: {f}\nModified: {dt.datetime.fromtimestamp(st.st_mtime).isoformat(sep=" ",timespec="seconds")}\nAge: {age/86400:.2f} days ({age/3600:.1f} hours)'
    )
    return 0
