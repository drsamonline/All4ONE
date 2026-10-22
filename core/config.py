"""Configuration management with recursive, backward-compatible defaults.

Two distinct stores live here:

* ``config.json`` — the *shipped / install* configuration.  Read-only in
  spirit: it carries the defaults a release ships with (plus any tweaks an
  operator made next to the executable).  It is read through
  :func:`load_config`.
* the per-user *preferences* file (see :mod:`core.preferences`) — anything the
  user changes from inside the app that must survive an application update
  (today: which packs are enabled).  It is written to the user's config
  location, never into the install directory.

The schema below is the single source of truth for defaults; a missing key in
an on-disk ``config.json`` always falls back to the value declared here.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "performance": {
        "multithreading": {"enabled": True, "worker_threads": "auto", "max_threads": 16, "io_bound": True},
        "indexing": {"enabled": False, "database_path": "~/.utility_suite/index.db", "update_interval": 3600},
        "hash_duplicate_detection": {
            "enabled": False,
            "algorithm": "sha256",
            "min_file_size": 1024,
            "max_file_size": 1073741824,
        },
        "copy_optimisations": {
            "use_sendfile": True,
            "same_volume_fast_move": True,
            "buffer_size": 1024 * 1024,
        },
        "scan_optimisations": {
            "use_scandir": True,
            "skip_hidden": True,
            "exclude_patterns": [".git", "System Volume Information", "$RECYCLE.BIN"],
            "directory_mtime_check": False,
        },
    },
    # Which tool packs are enabled.  ``disabled`` is the *only* thing that is
    # ever stored: an empty list means "every pack enabled", which is the
    # default, so an existing install behaves identically until the user
    # changes something and a pack added by a future update is enabled by
    # default (it simply is not in anyone's opt-out list).
    "packs": {"disabled": []},
    "plugins_directory": "plugins",
    "log_level": "INFO",
    "log_file": "logs/utility_suite.log",
    "max_log_size_mb": 5,
    "backup_count": 3,
    "ui": {"theme": "dark", "geometry": "1200x760", "remember_geometry": True},
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def app_base_dir() -> Path:
    """Directory the app considers its home.

    Beside the executable when frozen, otherwise the project root.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_config_path() -> Path:
    return app_base_dir() / "config.json"


def load_config() -> dict[str, Any]:
    path = get_config_path()
    if not path.exists():
        config = copy.deepcopy(DEFAULT_CONFIG)
        try:
            save_config(config)
        except OSError:
            # A read-only install directory must not be fatal: the defaults are
            # perfectly usable in memory.
            pass
        return config
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Top-level config must be an object")
        return _deep_merge(DEFAULT_CONFIG, data)
    except (OSError, ValueError, json.JSONDecodeError):
        # Preserve user file; return a safe in-memory default rather than crash.
        return copy.deepcopy(DEFAULT_CONFIG)


def save_config(config: dict[str, Any]) -> None:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def get_setting(key: str, default: Any = None) -> Any:
    value: Any = load_config()
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


# --------------------------------------------------------------------------- #
# External pack directory
# --------------------------------------------------------------------------- #
def _configured_plugins_dir_name() -> str:
    """Read ``plugins_directory`` from ``config.json`` without side effects.

    Read-only on purpose: importing this module must not write a config file.
    Falls back to ``"plugins"`` when the file is missing or malformed.
    """
    try:
        data = json.loads((app_base_dir() / "config.json").read_text(encoding="utf-8"))
        name = data.get("plugins_directory")
        if isinstance(name, str) and name.strip():
            return name.strip()
    except (OSError, ValueError):
        pass
    return "plugins"


def get_plugins_dir(*, create: bool = True) -> Path:
    """Return the external ``plugins/`` directory, creating it when ``create``.

    Beside the executable when frozen, otherwise beside the project root.  All
    packs ship *inside* the executable now; this directory is only consulted as
    an optional override (a developer or power user can drop a pack here to
    replace the built-in copy of the same pack).
    """
    directory = Path(_configured_plugins_dir_name())
    if not directory.is_absolute():
        directory = app_base_dir() / directory
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    return directory
