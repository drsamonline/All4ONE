"""Line-level text diff built on difflib.unified_diff (no external tools needed)."""
from __future__ import annotations

import argparse
import difflib
import sys


def _read(path):
    if path == "-":
        return sys.stdin.read().splitlines(keepends=True)
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    return [l if l.endswith("\n") else l + "\n" for l in lines]


def run(args=None):
    p = argparse.ArgumentParser(description="Unified/context/summary diff between two text files.")
    p.add_argument("a", help="First file ('-' for stdin).")
    p.add_argument("b", help="Second file ('-' for stdin).")
    p.add_argument("--context", type=int, default=3, metavar="N", help="Context lines (default 3).")
    p.add_argument("--style", choices=("unified", "context"), default="unified")
    p.add_argument("--summary", action="store_true", help="Only print added/removed counts.")
    a = p.parse_args(args or [])

    try:
        la, lb = _read(a.a), _read(a.b)
    except FileNotFoundError as exc:
        print(f"File not found: {exc.filename}")
        return 1

    if a.style == "context":
        out = list(difflib.context_diff(la, lb, fromfile=a.a, tofile=a.b))
    else:
        out = list(difflib.unified_diff(la, lb, fromfile=a.a, tofile=a.b, n=a.context))

    if a.summary:
        adds = sum(1 for l in out if l.startswith("+") and not l.startswith("+++"))
        dels = sum(1 for l in out if l.startswith("-") and not l.startswith("---"))
        print(f"added={adds} removed={dels} changed_lines={adds + dels}")
        return 0 if not out else 1

    if not out:
        print("identical")
        return 0
    sys.stdout.writelines(out)
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
