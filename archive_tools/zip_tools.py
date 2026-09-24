from __future__ import annotations

import argparse
import os
import zipfile
from pathlib import Path


def create_zip(args=None):
    p = argparse.ArgumentParser(description="Create a ZIP archive.")
    p.add_argument("source")
    p.add_argument("output")
    p.add_argument("--level", type=int, choices=range(10), default=9)
    a = p.parse_args(args or [])
    src, out = Path(a.source), Path(a.output)
    if not src.exists():
        print("Source not found.")
        return 1
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=a.level) as z:
        if src.is_file():
            z.write(src, src.name)
        else:
            for f in src.rglob("*"):
                if f.is_file():
                    z.write(f, f.relative_to(src))
    print(f"Created {out}")
    return 0


def _safe(member: str, dest: Path) -> Path:
    target = (dest / member).resolve()
    root = dest.resolve()
    if os.path.commonpath([str(target), str(root)]) != str(root):
        raise ValueError("Archive contains unsafe path")
    return target


def extract_zip(args=None):
    p = argparse.ArgumentParser(description="Safely extract a ZIP archive.")
    p.add_argument("archive")
    p.add_argument("destination")
    p.add_argument("--overwrite", action="store_true")
    a = p.parse_args(args or [])
    arc, dest = Path(a.archive), Path(a.destination)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(arc) as z:
        for info in z.infolist():
            try:
                target = _safe(info.filename, dest)
            except ValueError as exc:
                print(f"REJECTED {info.filename}: {exc}")
                return 2
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if target.exists() and not a.overwrite:
                print(f"SKIP exists: {target}")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, target.open("wb") as dst:
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    dst.write(chunk)
    print(f"Extracted {arc} -> {dest}")
    return 0
