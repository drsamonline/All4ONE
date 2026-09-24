from __future__ import annotations

import argparse
import json
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Validate and pretty-print JSON.")
    p.add_argument("file")
    p.add_argument("-o", "--output")
    p.add_argument("--sort-keys", action="store_true")
    a = p.parse_args(args or [])
    data = json.loads(Path(a.file).read_text(encoding="utf-8"))
    text = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=a.sort_keys) + "\n"
    if a.output:
        Path(a.output).write_text(text, encoding="utf-8")
        print(f"Wrote {a.output}")
    else:
        print(text, end="")
    return 0
