from __future__ import annotations

import argparse
import shutil
import subprocess


def run(args=None):
    p = argparse.ArgumentParser(description="Extract text from PDF using pdftotext.")
    p.add_argument("pdf")
    p.add_argument("output", nargs="?")
    a = p.parse_args(args or [])
    exe = shutil.which("pdftotext")
    if not exe:
        print("pdftotext not found.")
        return 3
    cmd = [exe, a.pdf, a.output] if a.output else [exe, a.pdf, "-"]
    r = subprocess.run(cmd, check=False)
    return r.returncode
