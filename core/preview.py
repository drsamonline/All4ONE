"""Best-effort file preview/open support."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".py",
    ".json",
    ".xml",
    ".csv",
    ".log",
    ".ini",
    ".cfg",
    ".yaml",
    ".yml",
    ".toml",
}


def preview_file(path: str | os.PathLike[str], *, max_bytes: int = 200_000) -> str:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    if p.suffix.lower() in TEXT_EXTENSIONS:
        data = p.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="replace")
    return f"{p}\nSize: {p.stat().st_size:,} bytes\nType: {p.suffix.lower() or 'unknown'}\n\nUse Open to launch the system-associated application."


def open_with_default(path: str | os.PathLike[str]) -> None:
    p = str(Path(path).resolve())
    if sys.platform == "win32":
        os.startfile(p)  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", p])
    else:
        subprocess.Popen(["xdg-open", p])
