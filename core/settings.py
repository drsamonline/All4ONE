"""Small JSON settings store (favourites, recents, theme).

Deliberately not the Windows registry: the whole point of this app is that
nothing is left behind. Delete the file and it forgets you.
"""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import Any


def config_dir() -> Path:
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "All4one"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "all4one"


DEFAULTS: dict[str, Any] = {
    "theme": "dark",
    "favourites": [],
    "recent": [],
    "last_category": "Files",
    "window": {"w": 1180, "h": 760},
    "confirm_destructive": True,
    "wrap_output": True,
}


class Settings:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (config_dir() / "settings.json")
        self.data: dict[str, Any] = json.loads(json.dumps(DEFAULTS))
        self.load()

    def load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self.data.update(raw)
        except (OSError, ValueError):
            pass

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except OSError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()

    # -- convenience -------------------------------------------------------
    def toggle_favourite(self, tool_id: str) -> bool:
        favs = list(self.data.get("favourites", []))
        if tool_id in favs:
            favs.remove(tool_id)
            on = False
        else:
            favs.append(tool_id)
            on = True
        self.set("favourites", favs)
        return on

    def is_favourite(self, tool_id: str) -> bool:
        return tool_id in self.data.get("favourites", [])

    def push_recent(self, tool_id: str, keep: int = 12) -> None:
        recents = [t for t in self.data.get("recent", []) if t != tool_id]
        recents.insert(0, tool_id)
        self.set("recent", recents[:keep])
