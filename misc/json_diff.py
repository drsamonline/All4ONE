from __future__ import annotations

import argparse
import json
import re


def _walk(node, path="", out=None):
    if out is None:
        out = []
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{path}.{k}" if path else k
            if isinstance(v, (dict, list)):
                _walk(v, p, out)
            else:
                out.append((p, type(v).__name__, repr(v)[:60]))
    elif isinstance(node, list):
        if not node:
            out.append((f"{path}[]", "empty", "[]"))
        for i, v in enumerate(node[:100]):
            _walk(v, f"{path}[{i}]", out)
    return out


def run(args=None):
    p = argparse.ArgumentParser(description="Diff two JSON documents or print a structural schema.")
    p.add_argument("a", help="First JSON file (or inline JSON string).")
    p.add_argument("b", nargs="?", help="Second JSON file/string to diff against.")
    p.add_argument("--keys", metavar="PATTERN", help="Filter paths by regex when printing a schema.")
    a = p.parse_args(args or [])

    def load(x):
        try:
            return json.loads(open(x, encoding="utf-8").read())
        except FileNotFoundError:
            return json.loads(x)

    da = load(a.a)
    if a.b is None:
        rows = _walk(da)
        pat = re.compile(a.keys, re.I) if a.keys else None
        for path, t, val in rows:
            if pat and not pat.search(path):
                continue
            print(f"{path}\t{t}\t{val}")
        print(f"({len(rows)} leaf values)")
        return 0

    db = load(a.b)
    diffs = []

    def cmp(x, y, path):
        if type(x) is not type(y):
            diffs.append((path, "type", type(x).__name__, type(y).__name__))
            return
        if isinstance(x, dict):
            for k in sorted(set(x) | set(y)):
                if k not in x:
                    diffs.append((f"{path}.{k}", "added", "-", str(y[k])[:50]))
                elif k not in y:
                    diffs.append((f"{path}.{k}", "removed", str(x[k])[:50], "-"))
                else:
                    cmp(x[k], y[k], f"{path}.{k}")
        elif isinstance(x, list):
            for i in range(max(len(x), len(y))):
                if i >= len(x):
                    diffs.append((f"{path}[{i}]", "added", "-", str(y[i])[:50]))
                elif i >= len(y):
                    diffs.append((f"{path}[{i}]", "removed", str(x[i])[:50], "-"))
                else:
                    cmp(x[i], y[i], f"{path}[{i}]")
        elif x != y:
            diffs.append((path or ".", "changed", str(x)[:50], str(y)[:50]))

    cmp(da, db, "")
    if not diffs:
        print("IDENTICAL")
        return 0
    for path, kind, old, new in diffs[:500]:
        print(f"{kind:<8} {path}: {old} -> {new}")
    print(f"({len(diffs)} differences)")
    return 1


# Note: returns exit code 1 when differences are found (useful in scripts).
