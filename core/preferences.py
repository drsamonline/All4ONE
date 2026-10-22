"""Per-user preferences that must survive an application update.

Why this module exists
----------------------
``config.json`` lives next to the executable.  On a normal Windows install that
directory can be read-only (``C:\\Program Files\\...``), and a new release
replaces the whole install directory anyway.  Anything the *user* chooses —
today, which tool packs are enabled — therefore cannot live there, or it would
be either unwritable or silently wiped by the next update.

So the durable copy lives in the user's config location:

    Windows   %APPDATA%\\UtilitySuite\\preferences.json
    macOS     ~/Library/Application Support/UtilitySuite/preferences.json
    Linux     $XDG_CONFIG_HOME/utility_suite/preferences.json  (or ~/.config/...)

The file records the packs a user has turned **off** (an explicit opt-out
list).  An empty list means "everything on", which is the default, so:

* an existing install is unchanged until the user touches something, and
* a pack added by a future update is enabled by default (it is in nobody's
  opt-out list).

Writes are atomic (write a temp file, then ``os.replace``), so an interrupted
save can never leave a truncated preferences file behind.  If the user
directory is somehow unwritable, the same ``disabled`` list is mirrored into
``config.json`` as a last resort rather than being dropped.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from . import config as _config

#: Environment override, chiefly so tests (and portable installs) can point the
#: preferences file at a throwaway directory instead of the real user profile.
CONFIG_DIR_ENV = "UTILITY_SUITE_CONFIG_DIR"

_SCHEMA_VERSION = 1


def user_config_dir() -> Path:
    """Return the per-user configuration directory for Utility Suite."""
    override = os.environ.get(CONFIG_DIR_ENV)
    if override and override.strip():
        return Path(override.strip()).expanduser()

    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "UtilitySuite"
        return Path.home() / "AppData" / "Roaming" / "UtilitySuite"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "UtilitySuite"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "utility_suite"


def preferences_path() -> Path:
    """Absolute path of the preferences file (the file may not exist yet)."""
    return user_config_dir() / "preferences.json"


def _seed_disabled_from_config() -> list[str]:
    """Read the install-dir ``packs.disabled`` list, used only to seed a first run.

    A pre-existing install may carry an operator's ``config.json`` with a
    ``packs.disabled`` entry; honour it the first time, then keep the durable
    copy in the user file from then on.
    """
    try:
        data = json.loads(_config.get_config_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    packs = data.get("packs")
    if not isinstance(packs, dict):
        return []
    disabled = packs.get("disabled")
    if isinstance(disabled, list):
        return [str(name).strip() for name in disabled if str(name).strip()]
    return []


class PackPreferences:
    """The persisted set of packs the user has disabled.

    Every method is safe to call in a headless process; nothing here imports
    tkinter or touches the network.
    """

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path) if path is not None else preferences_path()
        self._disabled: set[str] = set()
        self._mirror_to_config = False
        self.load()

    # ------------------------------------------------------------------ load
    def load(self) -> None:
        """(Re)read the preferences file, seeding from config.json on first run."""
        if self.path.exists():
            self._disabled = self._read_file(self.path)
            self._mirror_to_config = False
            return
        self._disabled = set(_seed_disabled_from_config())
        self._mirror_to_config = not self.path.exists()
        # Persist the seeded value so the durable copy exists from the start.
        if self._disabled or self._mirror_to_config:
            self._save()

    @staticmethod
    def _read_file(path: Path) -> set[str]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return set()
        if not isinstance(data, dict):
            return set()
        disabled = data.get("disabled_packs")
        if not isinstance(disabled, list):
            return set()
        return {str(name).strip() for name in disabled if str(name).strip()}

    # ------------------------------------------------------------------ save
    def _save(self) -> None:
        payload = {
            "schema_version": _SCHEMA_VERSION,
            "disabled_packs": sorted(self._disabled),
        }
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, self.path)
            self._mirror_to_config = False
            return
        except OSError:
            pass
        # Last resort: the user directory is not writable. Mirror the choice
        # into config.json so it is not silently lost (best effort).
        try:
            data = _config.load_config()
            data.setdefault("packs", {})["disabled"] = sorted(self._disabled)
            _config.save_config(data)
            self._mirror_to_config = True
        except OSError:
            self._mirror_to_config = False

    # ------------------------------------------------------------------ api
    def disabled_packs(self) -> tuple[str, ...]:
        return tuple(sorted(self._disabled))

    def is_enabled(self, pack: str) -> bool:
        return pack not in self._disabled

    def set_enabled(self, pack: str, enabled: bool) -> None:
        """Enable or disable a pack and persist the change."""
        name = str(pack).strip()
        if not name:
            return
        changed = False
        if enabled and name in self._disabled:
            self._disabled.discard(name)
            changed = True
        elif not enabled and name not in self._disabled:
            self._disabled.add(name)
            changed = True
        if changed:
            self._save()

    def set_disabled(self, names: list[str] | tuple[str, ...]) -> None:
        """Replace the whole opt-out set (used by the CLI)."""
        self._disabled = {str(n).strip() for n in names if str(n).strip()}
        self._save()

    def reset(self) -> None:
        """Re-enable every pack (empty opt-out list) and persist."""
        self._disabled.clear()
        self._save()
