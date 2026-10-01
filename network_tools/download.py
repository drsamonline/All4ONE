from __future__ import annotations

import argparse
import urllib.error
import urllib.request
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Download a URL with streaming I/O.")
    p.add_argument("url")
    p.add_argument("output", nargs="?")
    a = p.parse_args(args or [])
    if not (a.url.startswith("http://") or a.url.startswith("https://")):
        print(f"Not a valid http:// or https:// URL: {a.url}")
        return 1
    out = Path(a.output or Path(a.url.split("?", 1)[0].rstrip("/")).name or "download.bin")
    req = urllib.request.Request(a.url, headers={"User-Agent": "UtilitySuite/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r, out.open("wb") as f:
            while chunk := r.read(1024 * 1024):
                f.write(chunk)
    except urllib.error.URLError as e:
        print(f"Download failed: {e}")
        return 1
    print(f"Downloaded to {out}")
    return 0
