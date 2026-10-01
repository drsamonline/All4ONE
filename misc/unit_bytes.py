"""Byte-unit converter: KB/KiB/MB/MiB/GiB/TiB ... with exact and binary variants."""
from __future__ import annotations

import argparse

RATES = {
    "b": 1,
    "kb": 10**3, "kib": 2**10,
    "mb": 10**6, "mib": 2**20,
    "gb": 10**9, "gib": 2**30,
    "tb": 10**12, "tib": 2**40,
    "pb": 10**15, "pib": 2**50,
    "eb": 10**18, "eib": 2**60,
}


def run(args=None):
    p = argparse.ArgumentParser(description="Convert between decimal (KB) and binary (KiB) byte units.")
    p.add_argument("amount", help="Numeric value, optionally suffixed, e.g. '4.5GiB' or '1500 MB'.")
    p.add_argument("--to", metavar="UNIT", help="Target unit (default: show every common unit).")
    a = p.parse_args(args or [])

    tokens = a.amount.replace(",", "").split()
    if len(tokens) == 1:
        # allow attached suffixes like '4.5GiB' / '1500MB'
        text = tokens[0].lower()
        num, unit = text, "b"
        for suf in sorted(RATES, key=len, reverse=True):
            if text.endswith(suf) and text[: -len(suf)]:
                num, unit = text[: -len(suf)], suf
                break
    elif len(tokens) == 2:
        num, unit = tokens
    else:
        print(f"Cannot parse {a.amount!r}. Try '1500', '1500MB' or '4.5 GiB'.")
        return 2
    try:
        value = float(num)
    except ValueError:
        print(f"Not a number: {num!r}")
        return 1
    unit = unit.lower().strip()
    if unit not in RATES:
        print(f"Unknown unit: {unit!r}. Known: {', '.join(sorted(RATES))}")
        return 1

    nbytes = value * RATES[unit]

    def fmt(n):
        return f"{n:,.6f}".rstrip("0").rstrip(".")

    if a.to:
        target = a.to.lower()
        if target not in RATES:
            print(f"Unknown target unit: {a.to!r}")
            return 1
        print(fmt(nbytes / RATES[target]))
        return 0

    print(f"{fmt(nbytes)} bytes")
    for u in ("kb", "kib", "mb", "mib", "gb", "gib", "tb", "tib"):
        print(f"{fmt(nbytes / RATES[u]):>24}  {u.upper()}")
    return 0
