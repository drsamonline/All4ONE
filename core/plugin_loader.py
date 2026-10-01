"""Dynamic plugin-pack loader."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
import zipimport
from pathlib import Path
from types import ModuleType
from typing import Any

logger = logging.getLogger(__name__)


class PluginLoader:
    def __init__(self, plugins_dir: str | Path) -> None:
        self.plugins_dir = Path(plugins_dir)
        if not self.plugins_dir.is_absolute():
            self.plugins_dir = Path.cwd() / self.plugins_dir
        self.loaded_packs: dict[str, ModuleType] = {}
        self.errors: list[str] = []

    def scan(self) -> list[tuple[str, ModuleType]]:
        for old_name in list(self.loaded_packs):
            for module_name in list(sys.modules):
                if module_name == old_name or module_name.startswith(old_name + "."):
                    sys.modules.pop(module_name, None)
        self.loaded_packs.clear()
        self.errors.clear()
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        packs: list[tuple[str, ModuleType]] = []
        for entry in sorted(self.plugins_dir.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_file() and entry.suffix.lower() == ".zip":
                pack_name = entry.stem
                try:
                    importer = zipimport.zipimporter(str(entry))
                    spec = importer.find_spec(pack_name)
                    if spec is None or spec.loader is None:
                        raise ImportError(f"Package {pack_name} not found in archive")
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[pack_name] = module
                    spec.loader.exec_module(module)
                    self.loaded_packs[pack_name] = module
                    packs.append((pack_name, module))
                except Exception as exc:
                    msg = f"{entry.name}: {exc}"
                    self.errors.append(msg)
                    logger.exception("Plugin load failed: %s", msg)
            elif entry.is_file() and entry.suffix.lower() == ".py":
                pack_name = entry.stem
                try:
                    spec = importlib.util.spec_from_file_location(pack_name, entry)
                    if not spec or not spec.loader:
                        raise ImportError("No module loader available")
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[pack_name] = module
                    spec.loader.exec_module(module)
                    self.loaded_packs[pack_name] = module
                    packs.append((pack_name, module))
                except Exception as exc:
                    msg = f"{entry.name}: {exc}"
                    self.errors.append(msg)
                    logger.exception("Plugin load failed: %s", msg)
        return packs

    def get_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for pack_name, module in self.scan():
            register = getattr(module, "register_tools", None)
            if not callable(register):
                logger.warning("Plugin %s has no register_tools()", pack_name)
                continue
            try:
                entries = register()
                if not isinstance(entries, list):
                    raise TypeError("register_tools() must return a list")
                for entry in entries:
                    if not isinstance(entry, dict):
                        logger.warning("Ignoring invalid tool metadata in %s", pack_name)
                        continue
                    tool = dict(entry)
                    tool["pack"] = pack_name
                    tool.setdefault("dependencies", [])
                    tool.setdefault("description", "")
                    tools.append(tool)
            except Exception as exc:
                logger.exception("Tool registration failed in %s: %s", pack_name, exc)
        return tools
