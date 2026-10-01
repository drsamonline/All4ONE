"""INI file reader/writer using configparser (stdlib), with JSON export."""
from __future__ import annotations

import argparse
import configparser
import json
import sys


def run(args=None):
    p = argparse.ArgumentParser(description="Inspect INI files or set values from the command line.")
    p.add_argument("file", help="Path to the .ini file.")
    p.add_argument("--get", metavar="SECTION.KEY", help="Print a single value.")
    p.add_argument("--set", metavar="SECTION.KEY=VALUE", action="append", default=[],
                   help="Set a value and write the file back (repeatable).")
    p.add_argument("--json", action="store_true", help="Dump the whole file as JSON.")
    a = p.parse_args(args or [])

    cp = configparser.ConfigParser()
    if not cp.read(a.file, encoding="utf-8"):
        print(f"File not found or unreadable: {a.file}")
        return 1

    if a.get:
        section, _, key = a.get.partition(".")
        try:
            print(cp.get(section, key))
        except (configparser.NoSectionError, configparser.NoOptionError) as exc:
            print(f"Not found: {exc}")
            return 1
        return 0

    changed = False
    for assign in a.set:
        path, _, val = assign.partition("=")
        section, _, key = path.partition(".")
        if not section or not key:
            print(f"Invalid --set expression: {assign!r} (expected SECTION.KEY=VALUE)")
            return 2
        if not cp.has_section(section):
            cp.add_section(section)
        cp.set(section, key, val)
        changed = True

    if changed:
        with open(a.file, "w", encoding="utf-8") as fh:
            cp.write(fh)
        print(f"Updated {a.file} ({len(a.set)} key(s)).", file=sys.stderr)
        return 0

    if a.json:
        json.dump({s: dict(cp[s]) for s in cp.sections()}, sys.stdout, indent=2)
        print()
        return 0

    for section in cp.sections():
        print(f"[{section}]")
        for key, val in cp.items(section):
            print(f"  {key} = {val}")
    return 0
