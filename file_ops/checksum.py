from __future__ import annotations
import argparse, hashlib
from pathlib import Path


def file_checksum(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args=None):
    p = argparse.ArgumentParser(description="Generate or verify checksums.")
    p.add_argument("path")
    p.add_argument("--algorithm", choices=sorted(hashlib.algorithms_guaranteed), default="sha256")
    p.add_argument("--verify")
    a = p.parse_args(args or [])
    root = Path(a.path)
    if a.verify:
        vf = Path(a.verify)
        if not vf.is_file():
            print("Checksum file not found.")
            return 1
        failed = 0
        for line in vf.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                expected, name = line.split(maxsplit=1)
            except ValueError:
                print(f"Invalid line: {line}")
                failed += 1
                continue
            target = Path(name.strip().lstrip("*"))
            if not target.is_file():
                print(f"MISSING: {target}")
                failed += 1
                continue
            ok = file_checksum(target, a.algorithm).lower() == expected.lower()
            print(f"{'OK' if ok else 'FAILED'}: {target}")
            failed += not ok
        return int(bool(failed))
    files = [root] if root.is_file() else [x for x in root.rglob("*") if x.is_file()] if root.is_dir() else []
    if not files:
        print("Path not found.")
        return 1
    for f in files:
        print(f"{file_checksum(f,a.algorithm)}  {f}")
    return 0
