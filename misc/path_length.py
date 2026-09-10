from __future__ import annotations
import argparse
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Find paths longer than a specified threshold.")
    p.add_argument("directory", nargs="?", default=".")
    p.add_argument("--max", type=int, default=260)
    a = p.parse_args(args or [])
    hits = [str(x) for x in Path(a.directory).rglob("*") if len(str(x)) > a.max]
    print(f"Found {len(hits)} paths over {a.max} characters:")
    [print(x) for x in hits]
    return 0
