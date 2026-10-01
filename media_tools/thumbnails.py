from __future__ import annotations

import argparse
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Generate image thumbnails with Pillow.")
    p.add_argument("source")
    p.add_argument("--output-dir")
    p.add_argument("--size", type=int, default=256)
    a = p.parse_args(args or [])
    try:
        from PIL import Image
    except ImportError:
        print("Pillow is not installed. Install with: pip install pillow")
        return 3
    src = Path(a.source)
    out = Path(a.output_dir) if a.output_dir else src.parent / "thumbnails"
    out.mkdir(parents=True, exist_ok=True)
    files = (
        [src]
        if src.is_file()
        else [
            f
            for f in src.rglob("*")
            if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
        ]
    )
    for f in files:
        try:
            im = Image.open(f)
            im.thumbnail((a.size, a.size))
            target = out / (f.stem + ".jpg")
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            im.save(target, quality=90, optimize=True)
            print(target)
        except Exception as e:
            print(f"FAILED {f}: {e}")
    return 0
