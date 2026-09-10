"""Configuration management with recursive, backward-compatible defaults."""

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


def get_config_path() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "config.json"


def load_config() -> dict[str, Any]:
    path = get_config_path()
    if not path.exists():
        config = copy.deepcopy(DEFAULT_CONFIG)
        save_config(config)
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
