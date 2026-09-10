from __future__ import annotations
import argparse, os, tarfile
from pathlib import Path


def create_tar(args=None):
    p = argparse.ArgumentParser(description="Create a compressed TAR archive.")
    p.add_argument("source")
    p.add_argument("output")
    p.add_argument("--format", choices=["gz", "bz2", "xz", "plain"], default="gz")
    a = p.parse_args(args or [])
    mode = {"gz": "w:gz", "bz2": "w:bz2", "xz": "w:xz", "plain": "w"}[a.format]
    src, out = Path(a.source), Path(a.output)
    with tarfile.open(out, mode) as tar:
        tar.add(src, arcname=src.name)
    print(f"Created {out}")
    return 0


def _safe(dest: Path, name: str) -> Path:
    target = (dest / name).resolve()
    root = dest.resolve()
    if os.path.commonpath([str(target), str(root)]) != str(root):
        raise ValueError("Archive contains unsafe path")
    return target


def extract_tar(args=None):
    p = argparse.ArgumentParser(description="Safely extract TAR archives.")
    p.add_argument("archive")
    p.add_argument("destination")
    p.add_argument("--overwrite", action="store_true")
    a = p.parse_args(args or [])
    dest = Path(a.destination)
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(a.archive, "r:*") as tar:
        for member in tar.getmembers():
            if member.issym() or member.islnk():
                print(f"SKIP link: {member.name}")
                continue
            if member.isdev() or member.isfifo():
                print(f"SKIP special file: {member.name}")
                continue
            try:
                target = _safe(dest, member.name)
            except ValueError as exc:
                print(f"REJECTED {member.name}: {exc}")
                return 2
            if target.exists() and not a.overwrite:
                print(f"SKIP exists: {target}")
                continue
            tar.extract(member, dest)
    print(f"Extracted {a.archive} -> {dest}")
    return 0
