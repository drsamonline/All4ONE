from __future__ import annotations
import argparse
from pathlib import Path

MAGIC_DB = [
    (b"\x89PNG", "PNG image"),
    (b"\xff\xd8\xff", "JPEG image"),
    (b"GIF87a", "GIF image"),
    (b"GIF89a", "GIF image"),
    (b"%PDF", "PDF document"),
    (b"PK\x03\x04", "ZIP archive"),
    (b"PK\x05\x06", "Empty ZIP archive"),
    (b"MZ", "Windows PE executable"),
    (b"\x7fELF", "ELF executable"),
    (b"Rar!\x1a\x07", "RAR archive"),
    (b"\x1f\x8b", "GZIP archive"),
    (b"BZh", "BZIP2 archive"),
    (b"\xfd7zXZ\x00", "XZ archive"),
]


def run(args=None):
    p = argparse.ArgumentParser(description="Identify a file type from magic bytes.")
    p.add_argument("file")
    a = p.parse_args(args or [])
    path = Path(a.file)
    if not path.is_file():
        print(
            f"Not a regular file (is it a directory?): {path}" if path.exists() else f"File not found: {path}"
        )
        return 1
    with path.open("rb") as f:
        head = f.read(32)
    for magic, desc in MAGIC_DB:
        if head.startswith(magic):
            print(f"{a.file}: {desc}")
            return 0
    print(f"{a.file}: Unknown type")
    return 0
