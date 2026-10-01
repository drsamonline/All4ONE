"""CSV query tool: filter, project and aggregate CSV files using stdlib only."""
from __future__ import annotations

import argparse
import csv
import sys


def _load(path):
    if path == "-":
        return list(csv.DictReader(sys.stdin))
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _coerce(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def run(args=None):
    p = argparse.ArgumentParser(description="Query CSV files: filter rows, pick columns, aggregate.")
    p.add_argument("file", help="CSV file ('-' for stdin).")
    p.add_argument("--columns", help="Comma-separated column names to output.")
    p.add_argument("--where", metavar="COL=VALUE", action="append", default=[],
                   help="Keep rows where COL equals VALUE (repeatable; all must match).")
    p.add_argument("--numeric", metavar="COL", help="Aggregate column (count/min/max/sum/avg).")
    p.add_argument("--stats", action="store_true", help="Print stats instead of rows.")
    p.add_argument("--limit", type=int, default=0, help="Show at most N rows.")
    a = p.parse_args(args or [])

    try:
        rows = _load(a.file)
    except FileNotFoundError:
        print(f"File not found: {a.file}")
        return 1
    except csv.Error as exc:
        print(f"CSV error: {exc}")
        return 1

    conditions = []
    for cond in a.where:
        if "=" not in cond:
            print(f"Invalid --where expression: {cond!r} (expected COL=VALUE)")
            return 2
        col, _, val = cond.partition("=")
        conditions.append((col.strip(), val))
    matched = [r for r in rows if all(r.get(c) == v for c, v in conditions)]

    if a.stats or a.numeric:
        print(f"rows_total={len(rows)} rows_matched={len(matched)}")
        if a.numeric:
            vals = [_coerce(r.get(a.numeric)) for r in matched]
            vals = [v for v in vals if v is not None]
            if not vals:
                print(f"{a.numeric}: no numeric values in matched rows")
                return 0
            print(f"{a.numeric}: count={len(vals)} min={min(vals):g} max={max(vals):g} "
                  f"sum={sum(vals):g} avg={sum(vals) / len(vals):.4f}")
        return 0

    cols = [c.strip() for c in a.columns.split(",")] if a.columns else (list(rows[0].keys()) if rows else [])
    writer = csv.DictWriter(sys.stdout, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    shown = matched[: a.limit] if a.limit > 0 else matched
    for row in shown:
        writer.writerow(row)
    if a.limit > 0 and len(matched) > a.limit:
        print(f"# ... {len(matched) - a.limit} more row(s) hidden by --limit", file=sys.stderr)
    return 0
