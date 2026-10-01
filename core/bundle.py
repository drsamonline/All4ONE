"""Embedded tool bundle — replaces the external plugins/ folder.

All 45+ tool packs are compiled into a single deterministic ZIP archive
(``bundle/tools.dat``) that ships *inside* the PyInstaller executable.
At runtime the archive is located, loaded entirely from memory via
``zipimport``, and its ``catalog.json`` provides the full tool metadata —
so a released build needs exactly one file: ``utility_suite.exe``.

Archive layout (identical to the source tree, so handler paths like
``file_ops.checksum.run`` keep resolving unchanged):

    catalog.json                 -> {"tools": [ ...metadata dicts... ]}
    <pack>/__init__.py           -> register_tools() adapter
    <pack>/<module>.py           -> handler implementations
    core/extended_ops.py         -> shared expansion-tool engine
    core/handler_factory.py      -> lazy adapter factory

Build side: ``build_single_exe.py`` regenerates the archive from the
source tree before invoking PyInstaller.  Dev side: when no bundle is
present (running from a git checkout), the loader transparently falls
back to scanning the source packages / plugins/ directory.
"""

from __future__ import annotations

import io
import json
import logging
import sys
import zipimport
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Any

logger = logging.getLogger(__name__)

BUNDLE_NAME = "tools.dat"
# Fixed timestamp so repeated builds produce byte-identical archives.
_EPOCH = (1980, 1, 1, 0, 0, 0)


def get_bundle_path() -> Path | None:
    """Locate ``bundle/tools.dat`` next to the executable (frozen) or repo."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        candidates = [
            base / "bundle" / BUNDLE_NAME,
            Path(sys.executable).resolve().parent / "bundle" / BUNDLE_NAME,
        ]
    else:
        root = Path(__file__).resolve().parent.parent
        candidates = [root / "bundle" / BUNDLE_NAME]
    for cand in candidates:
        if cand.is_file():
            return cand
    return None


class BundleLoader:
    """Loads tool packs + metadata from the embedded bundle archive."""

    def __init__(self, bundle_path: str | Path) -> None:
        self.bundle_path = Path(bundle_path)
        self.errors: list[str] = []

    def get_tools(self) -> list[dict[str, Any]]:
        try:
            blob = self.bundle_path.read_bytes()
        except OSError as exc:
            self.errors.append(f"bundle unreadable: {exc}")
            return []
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as zf:
                catalog_raw = zf.read("catalog.json")
        except (KeyError, zipfile.BadZipFile) as exc:
            self.errors.append(f"invalid bundle archive: {exc}")
            return []
        try:
            catalog = json.loads(catalog_raw.decode("utf-8"))
        except ValueError as exc:
            self.errors.append(f"invalid catalog.json: {exc}")
            return []

        # Make the archive importable so handlers resolve lazily from memory.
        try:
            importer = zipimport.zipimporter(str(self.bundle_path))
        except Exception as exc:  # pragma: no cover - defensive
            self.errors.append(f"zipimport init failed: {exc}")
            return []
        # Prime sys.path so nested imports inside packs keep working even if
        # some module later uses importlib with a path-based finder.
        path_str = str(self.bundle_path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

        tools: list[dict[str, Any]] = []
        for entry in catalog.get("tools", []):
            if not isinstance(entry, dict):
                continue
            tool = dict(entry)
            tool.setdefault("dependencies", [])
            tool.setdefault("description", "")
            tools.append(tool)
        logger.info("Loaded %d tools from embedded bundle %s", len(tools), self.bundle_path.name)
        return tools

    def load_pack(self, pack_name: str) -> ModuleType | None:
        """Import a whole pack module from the bundle (used by refresh/dev)."""
        try:
            importer = zipimport.zipimporter(str(self.bundle_path))
            spec = importer.find_spec(pack_name)
            if spec is None or spec.loader is None:
                return None
            module = sys.modules.get(pack_name)
            if module is not None:
                return module
            module = __import__(pack_name)
            return module
        except Exception as exc:
            self.errors.append(f"{pack_name}: {exc}")
            return None


def build_bundle(root: Path, out_path: Path | None = None) -> tuple[Path, int]:
    """Generate the bundle archive from the source tree. Returns (path, tool_count).

    Scans every top-level package that exposes ``register_tools()``, imports
    it, collects the metadata, and writes a deterministic ZIP containing all
    pack sources plus ``catalog.json``.
    """
    root = Path(root).resolve()
    out_path = Path(out_path) if out_path else root / "bundle" / BUNDLE_NAME
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pack_dirs = sorted(
        p.name
        for p in root.iterdir()
        if p.is_dir()
        and (p / "__init__.py").exists()
        and p.name not in {"core", "tests", "backup", "bundle", "dist", "build", "logs", "scripts", "plugins"}
    )

    # Import each pack from the source tree to harvest metadata.
    sys.path.insert(0, str(root))
    catalog_tools: list[dict[str, Any]] = []
    seen_cmds: set[str] = set()
    for pack in pack_dirs:
        for mod_name in list(sys.modules):
            if mod_name == pack or mod_name.startswith(pack + "."):
                sys.modules.pop(mod_name, None)
        try:
            module = __import__(pack)
            register = getattr(module, "register_tools", None)
            if not callable(register):
                logger.warning("pack %s has no register_tools(); skipping", pack)
                continue
            entries = register()
        except Exception as exc:
            raise SystemExit(f"bundle build failed while importing {pack}: {exc}") from exc
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            tool = dict(entry)
            cmd = str(tool.get("cli_command", "")).strip()
            if not cmd or not str(tool.get("handler", "")).strip():
                continue
            if cmd in seen_cmds:
                continue  # registry keeps first registration; mirror that here
            seen_cmds.add(cmd)
            tool["pack"] = pack
            tool.setdefault("dependencies", [])
            catalog_tools.append(tool)

    catalog_json = json.dumps({"tools": catalog_tools}, indent=1, sort_keys=True).encode("utf-8")

    tmp = out_path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr(zipfile.ZipInfo("catalog.json", date_time=_EPOCH), catalog_json)
        for pack in pack_dirs:
            for f in sorted((root / pack).rglob("*.py")):
                if "__pycache__" in f.parts:
                    continue
                arc = f.relative_to(root).as_posix()
                zf.writestr(zipfile.ZipInfo(arc, date_time=_EPOCH), f.read_bytes())
        # Shared engine modules referenced by handler_factory adapters.
        for name in ("extended_ops.py", "handler_factory.py", "capability_checker.py"):
            src = root / "core" / name
            if src.is_file():
                zf.writestr(zipfile.ZipInfo(f"core/{name}", date_time=_EPOCH), src.read_bytes())
        zf.writestr(
            zipfile.ZipInfo("core/__init__.py", date_time=_EPOCH),
            (root / "core" / "__init__.py").read_bytes(),
        )
    tmp.replace(out_path)
    return out_path, len(catalog_tools)
