"""Capability/dependency checks used by the registry and GUI."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from typing import Iterable

WINDOWS_COMMANDS = {
    "powershell",
    "pwsh",
    "cmd",
    "reg",
    "sc",
    "schtasks",
    "wevtutil",
    "pnputil",
    "cleanmgr",
    "regedit",
    "attrib",
    "netsh",
}


class CapabilityChecker:
    def __init__(self) -> None:
        self._cache: dict[str, bool] = {}

    def _check_one(self, dependency: str) -> bool:
        if dependency in self._cache:
            return self._cache[dependency]
        raw = dependency.strip()
        if raw.startswith("python:"):
            ok = importlib.util.find_spec(raw.split(":", 1)[1]) is not None
        elif sys.platform == "win32" and raw.lower() in WINDOWS_COMMANDS:
            ok = shutil.which(raw) is not None or raw.lower() in {"regedit", "cleanmgr"}
        elif sys.platform != "win32" and raw.lower() in WINDOWS_COMMANDS:
            ok = False
        else:
            ok = shutil.which(raw) is not None
        self._cache[dependency] = ok
        return ok

    def check_dependencies(self, dependencies: Iterable[str]) -> bool:
        return not self.get_missing(dependencies)

    def get_missing(self, dependencies: Iterable[str]) -> list[str]:
        return [dep for dep in dependencies if not self._check_one(dep)]
