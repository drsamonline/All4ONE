#!/usr/bin/env python3
"""Emit per-pack plugin archives and the plugin manifest.

For every top-level tool pack (a directory containing ``__init__.py`` that is
not one of the reserved build directories) this writes::

    dist/plugins/<pack>.zip      one archive per pack, loadable by PluginLoader
    dist/plugins.json            machine-readable manifest of every pack

The archives are deliberately shaped so that ``core.plugin_loader.PluginLoader``
can import them directly: each zip holds the pack's ``*.py`` files under a
top-level ``<pack>/`` folder, so ``zipimport.zipimporter(zip).find_spec(<pack>)``
resolves ``<pack>/__init__.py`` exactly as the loader expects.  Packs whose
handlers import shared engine modules from ``core/`` also carry a copy of those
modules so the pack can be imported standalone.

All archives use a fixed timestamp (1980-01-01) and a pinned create_system /
external_attr, so repeated builds of the same sources are byte-identical.

Usage::

    python tools/make_plugin_zips.py                     # into ./dist
    python tools/make_plugin_zips.py --out build/plugins # custom output dir
    python tools/make_plugin_zips.py --no-manifest       # zips only

The module is importable: ``build_single_exe.py`` calls ``generate()``.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

# Fixed archive timestamp + attributes -> byte-identical repeat builds.
_EPOCH = (1980, 1, 1, 0, 0, 0)
_EXTERNAL_ATTR = 0o644 << 16

# Directories that are never tool packs even though they may hold __init__.py.
RESERVED = {
    "core",
    "tests",
    "backup",
    "bundle",
    "dist",
    "build",
    "logs",
    "scripts",
    "plugins",
    ".github",
    "docs",
    "tools",
}

# Shared engine modules a pack needs to import standalone (mirrors the set the
# embedded bundle ships).  Only added to packs that actually reference ``core``.
SHARED_CORE_MODULES = (
    "__init__.py",
    "handler_factory.py",
    "extended_ops.py",
    "capability_checker.py",
)

_CORE_REF = re.compile(r"^\s*(?:from|import)\s+core(?:\s|\.|$)", re.MULTILINE)


def repo_root() -> Path:
    """Return the repository root (the parent of this script's ``tools/`` dir)."""
    return Path(__file__).resolve().parent.parent


def discover_packs(root: Path) -> list[str]:
    """Return the sorted names of every tool pack under *root*."""
    packs = [
        p.name
        for p in root.iterdir()
        if p.is_dir() and (p / "__init__.py").is_file() and p.name not in RESERVED
    ]
    return sorted(packs)


def _pack_py_files(root: Path, pack: str) -> list[Path]:
    """Every ``*.py`` file of a pack, cache-free, in deterministic order."""
    return sorted(
        f
        for f in (root / pack).rglob("*.py")
        if "__pycache__" not in f.parts
    )


def pack_needs_core(root: Path, pack: str) -> bool:
    """True when any of the pack's sources import a ``core`` module."""
    for f in _pack_py_files(root, pack):
        try:
            if _CORE_REF.search(f.read_text(encoding="utf-8", errors="replace")):
                return True
        except OSError:
            continue
    return False


def _zip_entry(zf: zipfile.ZipFile, arcname: str, data: bytes) -> None:
    info = zipfile.ZipInfo(arcname, date_time=_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3  # pin so Windows/Linux hosts produce identical bytes
    info.external_attr = _EXTERNAL_ATTR
    zf.writestr(info, data)


def build_pack_zip(root: Path, pack: str, out_dir: Path) -> Path:
    """Write ``out_dir/<pack>.zip`` for one pack and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{pack}.zip"
    tmp_path = out_path.with_suffix(".zip.tmp")

    entries: list[tuple[str, bytes]] = []
    for f in _pack_py_files(root, pack):
        arc = f"{pack}/{f.relative_to(root / pack).as_posix()}"
        entries.append((arc, f.read_bytes()))
    if pack_needs_core(root, pack):
        for name in SHARED_CORE_MODULES:
            src = root / "core" / name
            if src.is_file():
                entries.append((f"core/{name}", src.read_bytes()))
    entries.sort(key=lambda item: item[0])

    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for arc, data in entries:
            _zip_entry(zf, arc, data)
    tmp_path.replace(out_path)
    return out_path


def _load_pack_module(root: Path, pack: str):
    """Import a pack from the source tree, fresh, and return the module."""
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    for name in list(sys.modules):
        if name == pack or name.startswith(pack + "."):
            sys.modules.pop(name, None)
    return __import__(pack)


def _dominant_category(tools: list[dict[str, Any]], pack: str) -> str:
    counts: dict[str, int] = {}
    for tool in tools:
        cat = str(tool.get("category", "")).strip()
        if cat:
            counts[cat] = counts.get(cat, 0) + 1
    if counts:
        return max(counts, key=lambda c: (counts[c], c))
    return pack.replace("_", " ").title()


def _describe(names: list[str]) -> str:
    """A short, factual one-liner derived from the pack's own tool names."""
    n = len(names)
    if n == 0:
        return "No tools registered."
    if n <= 3:
        return f"{n} tool{'s' if n != 1 else ''}: {', '.join(names)}."
    return f"{n} tools: {', '.join(names[:3])} and {n - 3} more."


def collect_pack_info(root: Path, out_dir: Path, pack: str) -> dict[str, Any]:
    """Import *pack*, count its tools, and build its manifest entry."""
    module = _load_pack_module(root, pack)
    register = getattr(module, "register_tools", None)
    if not callable(register):
        raise RuntimeError(f"pack {pack!r} has no register_tools()")
    tools = register()
    if not isinstance(tools, list):
        raise RuntimeError(f"pack {pack!r} register_tools() did not return a list")
    names = [str(t.get("name", "")).strip() for t in tools if isinstance(t, dict)]
    zip_path = out_dir / f"{pack}.zip"
    return {
        "name": pack,
        "title": _dominant_category([t for t in tools if isinstance(t, dict)], pack),
        "tools": len(tools),
        "size": zip_path.stat().st_size,
        "file": f"{pack}.zip",
        "description": _describe(names),
    }


def read_version(root: Path) -> str:
    version_file = root / "VERSION.txt"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def build_manifest(
    root: Path,
    out_dir: Path,
    packs: list[str],
    generated: str | None = None,
) -> dict[str, Any]:
    """Build the manifest dict (packs sorted by name)."""
    entries = [collect_pack_info(root, out_dir, pack) for pack in sorted(packs)]
    entries.sort(key=lambda e: e["name"])
    return {
        "version": read_version(root),
        "generated": generated or _dt.date.today().isoformat(),
        "packs": entries,
    }


def write_manifest(manifest: dict[str, Any], manifest_path: Path) -> Path:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    manifest_path.write_text(text, encoding="utf-8")
    return manifest_path


def generate(
    root: Path | None = None,
    out_dir: Path | None = None,
    manifest_path: Path | None = None,
    write_manifest_file: bool = True,
    generated: str | None = None,
) -> dict[str, Any]:
    """Build every pack zip (and the manifest). Returns the manifest dict.

    ``out_dir`` defaults to ``<root>/dist/plugins`` and the manifest defaults
    to ``<root>/dist/plugins.json``.
    """
    root = Path(root) if root else repo_root()
    out_dir = Path(out_dir) if out_dir else root / "dist" / "plugins"
    manifest_path = Path(manifest_path) if manifest_path else root / "dist" / "plugins.json"

    # Importing packs must never litter the source tree with __pycache__.
    prev_dont_write = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        packs = discover_packs(root)
        for pack in packs:
            build_pack_zip(root, pack, out_dir)
        manifest = build_manifest(root, out_dir, packs, generated=generated)
        if write_manifest_file:
            write_manifest(manifest, manifest_path)
    finally:
        sys.dont_write_bytecode = prev_dont_write

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit per-pack plugin archives + manifest")
    parser.add_argument("--root", type=Path, default=None, help="repository root")
    parser.add_argument("--out", type=Path, default=None, help="zip output directory")
    parser.add_argument("--manifest", type=Path, default=None, help="manifest path")
    parser.add_argument("--date", default=None, help="override the manifest 'generated' date (ISO)")
    parser.add_argument("--no-manifest", action="store_true", help="write zips only")
    args = parser.parse_args(argv)

    root = args.root.resolve() if args.root else repo_root()
    out_dir = args.out.resolve() if args.out else root / "dist" / "plugins"
    manifest_path = args.manifest.resolve() if args.manifest else root / "dist" / "plugins.json"

    manifest = generate(
        root=root,
        out_dir=out_dir,
        manifest_path=manifest_path,
        write_manifest_file=not args.no_manifest,
        generated=args.date,
    )

    total_tools = sum(p["tools"] for p in manifest["packs"])
    total_bytes = sum(p["size"] for p in manifest["packs"])
    print(f"Plugin packs: {len(manifest['packs'])}  ·  tools: {total_tools}")
    for entry in manifest["packs"]:
        print(f"  {entry['file']:<34} {entry['tools']:>3} tools  {entry['size']:>8,} bytes")
    print(f"Zips written to: {out_dir}")
    print(f"Total zip size:  {total_bytes:,} bytes")
    if not args.no_manifest:
        print(f"Manifest:        {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
