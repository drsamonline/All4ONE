"""Shared helpers for tool implementations.

Kept tiny on purpose: tools should read as the operation they perform, not as
boilerplate. Anything a tool needs beyond this belongs in its own body.
"""

from __future__ import annotations

import fnmatch
import hashlib
import os
import platform
import shutil
import stat
import unicodedata
from datetime import datetime
from pathlib import Path

from core.tool import Context, ToolError

IS_WINDOWS = platform.system() == "Windows"


# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
def expand(raw: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(raw).strip().strip('"'))))


def need_path(raw: str, what: str = "Path") -> Path:
    p = expand(raw)
    if not str(raw).strip():
        raise ToolError(f"{what} is empty")
    if not p.exists():
        raise ToolError(f"{what} does not exist: {p}")
    return p


def need_file(raw: str, what: str = "File") -> Path:
    p = need_path(raw, what)
    if not p.is_file():
        raise ToolError(f"{what} is not a file: {p}")
    return p


def need_dir(raw: str, what: str = "Folder") -> Path:
    p = need_path(raw, what)
    if not p.is_dir():
        raise ToolError(f"{what} is not a folder: {p}")
    return p


def out_path(raw: str, default_name: str, folder: Path | None = None) -> Path:
    """Resolve an output path, creating parent folders as needed."""
    text = str(raw).strip()
    if text:
        p = expand(text)
    else:
        p = (folder or Path.cwd()) / default_name
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def unique(p: Path) -> Path:
    """Never silently overwrite: report-1.txt, report-2.txt, ..."""
    if not p.exists():
        return p
    stem, suffix, parent = p.stem, p.suffix, p.parent
    n = 1
    while True:
        candidate = parent / f"{stem}-{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def human_size(num: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(num)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} PB"


def stamp(when: float | None = None) -> str:
    return datetime.fromtimestamp(when or datetime.now().timestamp()).strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------
# Walking
# --------------------------------------------------------------------------
def iter_files(root: Path, recursive: bool = True, pattern: str = "*",
               skip_hidden: bool = False):
    """Yield files under ``root`` matching a glob pattern."""
    if root.is_file():
        yield root
        return
    if recursive:
        for dirpath, dirnames, filenames in os.walk(root):
            if skip_hidden:
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in filenames:
                if skip_hidden and name.startswith("."):
                    continue
                if fnmatch.fnmatch(name.lower(), pattern.lower()):
                    yield Path(dirpath) / name
    else:
        for entry in root.iterdir():
            if entry.is_file() and fnmatch.fnmatch(entry.name.lower(), pattern.lower()):
                yield entry


def count_files(root: Path, recursive: bool = True) -> int:
    return sum(1 for _ in iter_files(root, recursive))


def hash_file(path: Path, algorithm: str = "sha256", chunk: int = 1 << 20) -> str:
    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise ToolError(f"Unknown hash algorithm {algorithm!r}") from exc
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def file_kind(path: Path) -> str:
    """A human label for what a path actually is."""
    try:
        mode = path.lstat().st_mode
    except OSError:
        return "unknown"
    if stat.S_ISLNK(mode):
        return "symlink"
    if path.is_dir():
        return "folder"
    return "file"


# --------------------------------------------------------------------------
# Text
# --------------------------------------------------------------------------
ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def read_text(path: Path, encoding: str = "auto") -> str:
    data = path.read_bytes()
    if encoding and encoding != "auto":
        return data.decode(encoding, errors="replace")
    for candidate in ENCODINGS:
        try:
            return data.decode(candidate)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def write_text(path: Path, text: str, encoding: str = "utf-8", newline: str = "\n") -> Path:
    if newline and newline != "\n":
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", newline)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding=encoding, newline="")
    return path


def slugify(text: str, separator: str = "-", ascii_only: bool = True) -> str:
    text = unicodedata.normalize("NFKD", text)
    if ascii_only:
        text = text.encode("ascii", "ignore").decode("ascii")
    keep = []
    for ch in text:
        keep.append(ch if (ch.isalnum() or ch in " -_.") else separator)
    out = "".join(keep)
    out = " ".join(out.split())
    if separator:
        out = separator.join(part for part in out.replace(separator, " ").split() if part)
    return out.strip(separator) or "untitled"


def safe_name(name: str) -> str:
    """Strip characters Windows will not accept in a filename."""
    cleaned = "".join("_" if ch in '<>:"/\\|?*' or ord(ch) < 32 else ch for ch in name)
    return cleaned.strip(" .") or "file"


# --------------------------------------------------------------------------
# Output & reporting
# --------------------------------------------------------------------------
def report_table(rows: list[dict], columns: list[str] | None = None) -> str:
    """A plain aligned table — readable in a console and copyable."""
    if not rows:
        return "(no rows)"
    cols = columns or list(rows[0].keys())
    widths = {c: max(len(str(c)), *(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    head = "  ".join(str(c).ljust(widths[c]) for c in cols)
    rule = "  ".join("-" * widths[c] for c in cols)
    body = "\n".join("  ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols) for r in rows)
    return f"{head}\n{rule}\n{body}"


def write_csv(path: Path, rows: list[dict], columns: list[str] | None = None) -> Path:
    import csv
    cols = columns or (list(rows[0].keys()) if rows else [])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in cols})
    return path


def require(module: str, dep_key: str):
    """Import an optional dependency or explain how to get it."""
    import importlib

    from core import deps as deps_mod
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        hint = deps_mod.DEPS[dep_key].hint if dep_key in deps_mod.DEPS else module
        raise ToolError(f"This tool needs {module} — {hint}") from exc


def run_command(args: list[str], cwd: Path | None = None,
                timeout: int = 120, ctx: Context | None = None) -> tuple[int, str, str]:
    """Run an external program (never through a shell) and capture output."""
    import subprocess
    if ctx is not None:
        ctx.log(f"$ {' '.join(args)}")
    try:
        proc = subprocess.run(args, cwd=str(cwd) if cwd else None, capture_output=True,
                              text=True, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        raise ToolError(f"Program not found: {args[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ToolError(f"{args[0]} timed out after {timeout}s") from exc
    if proc.stdout and ctx is not None:
        for line in proc.stdout.splitlines()[-40:]:
            ctx.log(line)
    if proc.returncode != 0 and proc.stderr and ctx is not None:
        for line in proc.stderr.splitlines()[-15:]:
            ctx.log(f"! {line}")
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def which(name: str) -> str | None:
    return shutil.which(name)
