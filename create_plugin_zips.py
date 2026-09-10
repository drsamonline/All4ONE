from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "plugins"
OUT.mkdir(exist_ok=True)


def pack_names():
    return sorted(
        p.name
        for p in ROOT.iterdir()
        if p.is_dir() and (p / "__init__.py").exists() and p.name not in {"core", "tests"}
    )


def main():
    packs = pack_names()
    expected = set(packs)
    for old in OUT.glob("*.zip"):
        if old.stem not in expected:
            old.unlink()
    for pack in packs:
        src = ROOT / pack
        out = OUT / f"{pack}.zip"
        tmp = out.with_suffix(".tmp")
        with ZipFile(tmp, "w", ZIP_DEFLATED, compresslevel=9) as z:
            for f in sorted(src.rglob("*.py")):
                if "__pycache__" in f.parts:
                    continue
                z.write(f, f.relative_to(ROOT).as_posix())
        tmp.replace(out)
        print(f"{out.name}: {out.stat().st_size:,} bytes")
    print(f"Plugin packs: {len(packs)}")


if __name__ == "__main__":
    main()
