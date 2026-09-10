from __future__ import annotations
import argparse
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Convert text file encoding.")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--from-encoding", default="utf-8")
    p.add_argument("--to-encoding", default="utf-8")
    p.add_argument("--errors", choices=["strict", "replace", "ignore"], default="strict")
    a = p.parse_args(args or [])
    data = Path(a.input).read_text(encoding=a.from_encoding, errors=a.errors)
    Path(a.output).write_text(data, encoding=a.to_encoding, errors=a.errors)
    print(f"Converted {a.input} -> {a.output}")
    return 0
