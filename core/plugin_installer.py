"""Plugin-pack installer: browse, download, install and remove plugin packs.

This module is deliberately pure logic with **no GUI imports** so it can be
unit-tested headlessly and reused from the CLI.  It depends only on the
standard library (``urllib``, ``zipfile``, ``json``, ``shutil``).

Error contract
--------------
Expected failures — offline, a 404, a corrupt archive, a bad file — are
*returned* as result objects (``ManifestResult``, ``DownloadResult``,
``InstallResult``, ``RemoveResult``) and never raised, so the caller can show a
plain message instead of a traceback.  Only a programmer error (an invalid pack
name, a destination outside the plugins directory) raises
:class:`PluginInstallerError`.

Layout
------
Packs live in the same ``plugins/`` directory the rest of the app uses: beside
the executable when frozen (``sys.frozen``/``sys.executable``), otherwise beside
the project root, honouring a custom ``plugins_directory`` in ``config.json``.
Each pack is a ``<name>.zip`` whose archive root contains ``<name>/__init__.py``
(the shape :class:`core.plugin_loader.PluginLoader` imports via ``zipimport``),
or a plain ``<name>.py`` exposing ``register_tools()``.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

# GitHub release assets published by the packaging step.  The first manifest
# URL is the pinned "latest-build" tag the pack zips are uploaded to; the second
# is the generic latest-release redirect used as a fallback if the tag 404s.
MANIFEST_URLS: tuple[str, ...] = (
    "https://github.com/drsamonline/All4ONE/releases/download/latest-build/plugins.json",
    "https://github.com/drsamonline/All4ONE/releases/latest/download/plugins.json",
)
PACK_URL_TEMPLATE = "https://github.com/drsamonline/All4ONE/releases/download/latest-build/{file}"

# Network timeouts are intentionally short: a hung request must never freeze a
# background download thread forever, and offline detection should be quick.
MANIFEST_TIMEOUT = 10.0
DOWNLOAD_TIMEOUT = 30.0
_CHUNK = 64 * 1024
_USER_AGENT = "All4ONE-UtilitySuite-plugin-installer"

# A pack name becomes a filename inside the plugins directory, so keep it to a
# conservative charset — this is the primary defence against path traversal.
_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


class PluginInstallerError(Exception):
    """Raised for programmer errors only (invalid pack name / bad destination).

    Network, HTTP and filesystem failures are returned as result objects and
    never surface as this exception.
    """


# --------------------------------------------------------------------------- #
# Data types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PackInfo:
    """One pack as advertised by the remote manifest."""

    name: str
    title: str = ""
    tools: int = 0
    size: int = 0
    file: str = ""
    description: str = ""

    @property
    def download_url(self) -> str:
        """Absolute URL of this pack's archive."""
        return PACK_URL_TEMPLATE.format(file=self.file or f"{self.name}.zip")


@dataclass(frozen=True)
class InstalledPack:
    """A pack currently present in the plugins directory."""

    name: str
    path: Path
    size: int
    kind: str  # "zip" or "py"


@dataclass
class ManifestResult:
    """Outcome of :func:`fetch_manifest`."""

    ok: bool
    packs: list[PackInfo] = field(default_factory=list)
    version: str = ""
    generated: str = ""
    source: str = ""
    error: str = ""


@dataclass
class DownloadResult:
    """Outcome of :func:`download_pack`."""

    ok: bool
    name: str = ""
    path: Path | None = None
    bytes_written: int = 0
    error: str = ""


@dataclass
class InstallResult:
    """Outcome of :func:`install_from_file`."""

    ok: bool
    name: str = ""
    path: Path | None = None
    error: str = ""


@dataclass
class RemoveResult:
    """Outcome of :func:`remove_pack`."""

    ok: bool
    name: str = ""
    error: str = ""


# --------------------------------------------------------------------------- #
# Directory resolution
# --------------------------------------------------------------------------- #
def _app_base_dir() -> Path:
    """Directory the app considers its home (mirrors :func:`core.config.get_config_path`)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _configured_dir_name() -> str:
    """Read ``plugins_directory`` from ``config.json`` without side effects.

    Read-only on purpose: importing this module must not write a config file.
    Falls back to ``"plugins"`` when the file is missing or malformed.
    """
    try:
        data = json.loads((_app_base_dir() / "config.json").read_text(encoding="utf-8"))
        name = data.get("plugins_directory")
        if isinstance(name, str) and name.strip():
            return name.strip()
    except (OSError, ValueError):
        pass
    return "plugins"


def get_plugins_dir(*, create: bool = True) -> Path:
    """Return the plugins directory, creating it when ``create`` is true.

    Beside the executable when frozen, otherwise beside the project root.
    """
    directory = Path(_configured_dir_name())
    if not directory.is_absolute():
        directory = _app_base_dir() / directory
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def _valid_name(name: str) -> bool:
    return bool(name) and name not in {".", ".."} and _NAME_RE.fullmatch(name) is not None


def _within(path: Path, directory: Path) -> bool:
    """True when ``path`` resolves to a location inside ``directory``."""
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except (ValueError, OSError):
        return False


# --------------------------------------------------------------------------- #
# Installed packs
# --------------------------------------------------------------------------- #
def list_installed(plugins_dir: str | Path | None = None) -> list[InstalledPack]:
    """Return the packs currently present in the plugins directory."""
    directory = Path(plugins_dir) if plugins_dir else get_plugins_dir(create=False)
    packs: list[InstalledPack] = []
    if not directory.is_dir():
        return packs
    for entry in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
        suffix = entry.suffix.lower()
        if not entry.is_file() or suffix not in {".zip", ".py"}:
            continue
        try:
            size = entry.stat().st_size
        except OSError:
            size = 0
        packs.append(
            InstalledPack(name=entry.stem, path=entry, size=size, kind="zip" if suffix == ".zip" else "py")
        )
    return packs


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #
def _describe_error(exc: BaseException) -> str:
    """Turn an urllib/OS exception into a short, user-readable phrase."""
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == 404:
            return "the plugin catalogue was not found on the release server (HTTP 404)"
        return f"the server returned HTTP {exc.code}"
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        return f"network unavailable ({reason})"
    if isinstance(exc, TimeoutError):
        return "the connection timed out"
    text = str(exc).strip()
    return text or exc.__class__.__name__


def _http_get(url: str, timeout: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (fixed https URLs)
        return response.read()


def _http_download(
    url: str,
    dest: Path,
    *,
    timeout: float,
    progress: Callable[[int, int], None] | None,
    expected_size: int,
) -> int:
    """Stream ``url`` to ``dest``, returning the byte count written."""
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    written = 0
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (fixed https URLs)
        total = _as_int(response.headers.get("Content-Length")) or expected_size or 0
        if progress:
            progress(0, total)
        with open(dest, "wb") as handle:
            while True:
                chunk = response.read(_CHUNK)
                if not chunk:
                    break
                handle.write(chunk)
                written += len(chunk)
                if progress:
                    progress(written, total)
    return written


def _as_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


# --------------------------------------------------------------------------- #
# Manifest
# --------------------------------------------------------------------------- #
def _parse_packs(data: object) -> list[PackInfo]:
    if not isinstance(data, dict):
        raise ValueError("manifest root is not a JSON object")
    raw = data.get("packs")
    if not isinstance(raw, list):
        raise ValueError("manifest has no 'packs' list")
    packs: list[PackInfo] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        packs.append(
            PackInfo(
                name=name,
                title=str(item.get("title") or name),
                tools=_as_int(item.get("tools")),
                size=_as_int(item.get("size")),
                file=str(item.get("file") or f"{name}.zip"),
                description=str(item.get("description") or ""),
            )
        )
    return packs


def fetch_manifest(
    *, urls: Iterable[str] | None = None, timeout: float = MANIFEST_TIMEOUT
) -> ManifestResult:
    """Download and parse the plugin manifest.

    Tries each URL in order and returns the first that yields a valid
    manifest.  Returns ``ManifestResult(ok=False, error=...)`` when every URL
    fails (offline, 404, malformed JSON) — it never raises.
    """
    error = "the plugin catalogue could not be loaded"
    for url in urls or MANIFEST_URLS:
        try:
            raw = _http_get(url, timeout)
        except Exception as exc:  # offline, DNS, TLS, HTTP, timeout — all map to one message
            error = _describe_error(exc)
            continue
        try:
            data = json.loads(raw.decode("utf-8"))
            packs = _parse_packs(data)
        except (ValueError, UnicodeDecodeError) as exc:
            error = f"the plugin catalogue is malformed ({exc})"
            continue
        return ManifestResult(
            ok=True,
            packs=packs,
            version=str(data.get("version", "")),
            generated=str(data.get("generated", "")),
            source=url,
        )
    return ManifestResult(ok=False, error=error)


# --------------------------------------------------------------------------- #
# Archive validation
# --------------------------------------------------------------------------- #
def validate_pack_zip(path: str | Path, name: str) -> str | None:
    """Return an error string if ``path`` is not a usable ``<name>`` pack zip."""
    try:
        with zipfile.ZipFile(path) as archive:
            corrupt = archive.testzip()
            if corrupt is not None:
                return f"the archive is corrupt (bad entry: {corrupt})"
            names = set(archive.namelist())
    except (zipfile.BadZipFile, OSError) as exc:
        return f"not a valid zip archive ({exc})"
    if f"{name}/__init__.py" not in names:
        return f"the archive does not contain {name}/__init__.py"
    return None


def _validate_pack_py(path: Path) -> str | None:
    """Return an error string if ``path`` is not a usable ``.py`` pack."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return f"the Python pack could not be read ({exc})"
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return f"the Python pack has a syntax error (line {exc.lineno})"
    if not any(isinstance(node, ast.FunctionDef) and node.name == "register_tools" for node in tree.body):
        return "the Python pack does not define register_tools()"
    return None


# --------------------------------------------------------------------------- #
# Download / install / remove
# --------------------------------------------------------------------------- #
def _safe_unlink(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def download_pack(
    name: str,
    dest_dir: str | Path | None = None,
    progress: Callable[[int, int], None] | None = None,
    *,
    file: str | None = None,
    url: str | None = None,
    expected_size: int = 0,
    timeout: float = DOWNLOAD_TIMEOUT,
) -> DownloadResult:
    """Download a pack archive into the plugins directory.

    The downloaded archive is validated (a real zip containing
    ``<name>/__init__.py``) before it is kept; anything else is deleted.  The
    write goes to a ``.part`` file first, so a failed download never leaves a
    half-written pack behind.  ``progress(done, total)`` is called during the
    transfer; ``total`` is 0 when the server omits ``Content-Length``.
    """
    name = (name or "").strip()
    if not _valid_name(name):
        raise PluginInstallerError(f"invalid pack name: {name!r}")

    directory = Path(dest_dir) if dest_dir else get_plugins_dir()
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return DownloadResult(ok=False, name=name, error=f"cannot create plugins directory ({exc})")
    filename = file or f"{name}.zip"
    if Path(filename).suffix.lower() != ".zip":
        filename = f"{name}.zip"
    target = directory / filename
    if not _within(target, directory):
        raise PluginInstallerError(f"refusing to write outside the plugins directory: {filename!r}")

    tmp = target.with_name(target.name + ".part")
    try:
        written = _http_download(
            url or PACK_URL_TEMPLATE.format(file=filename),
            tmp,
            timeout=timeout,
            progress=progress,
            expected_size=expected_size,
        )
    except Exception as exc:  # offline, DNS, TLS, HTTP, timeout, disk — never escapes
        _safe_unlink(tmp)
        return DownloadResult(ok=False, name=name, error=_describe_error(exc))

    problem = validate_pack_zip(tmp, name)
    if problem:
        _safe_unlink(tmp)
        return DownloadResult(ok=False, name=name, error=problem)

    try:
        os.replace(tmp, target)
    except OSError as exc:
        _safe_unlink(tmp)
        return DownloadResult(ok=False, name=name, error=str(exc))
    return DownloadResult(ok=True, name=name, path=target, bytes_written=written)


def install_from_file(path: str | Path, dest_dir: str | Path | None = None) -> InstallResult:
    """Copy a user-chosen ``.zip``/``.py`` pack into the plugins directory.

    The same validation as a download applies: a ``.zip`` must contain
    ``<name>/__init__.py`` and a ``.py`` must define ``register_tools()``.
    """
    source = Path(path)
    if not source.is_file():
        return InstallResult(ok=False, error=f"file not found: {source}")
    directory = Path(dest_dir) if dest_dir else get_plugins_dir()
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return InstallResult(ok=False, name=source.stem, error=f"cannot create plugins directory ({exc})")
    suffix = source.suffix.lower()
    name = source.stem

    if suffix == ".zip":
        problem = validate_pack_zip(source, name)
    elif suffix == ".py":
        problem = _validate_pack_py(source)
    else:
        return InstallResult(ok=False, name=name, error="choose a .zip pack or a .py pack")
    if problem:
        return InstallResult(ok=False, name=name, error=problem)

    target = directory / f"{name}{suffix}"
    if not _within(target, directory):
        raise PluginInstallerError(f"refusing to write outside the plugins directory: {target.name!r}")
    try:
        shutil.copy2(source, target)
    except OSError as exc:
        return InstallResult(ok=False, name=name, error=str(exc))
    return InstallResult(ok=True, name=name, path=target)


def remove_pack(name: str, dest_dir: str | Path | None = None) -> RemoveResult:
    """Delete an installed pack.

    Refuses (raises :class:`PluginInstallerError`) for a malformed name, and
    never touches a path that resolves outside the plugins directory.
    """
    name = (name or "").strip()
    if not _valid_name(name):
        raise PluginInstallerError(f"invalid pack name: {name!r}")
    directory = Path(dest_dir) if dest_dir else get_plugins_dir(create=False)
    for suffix in (".zip", ".py"):
        target = directory / f"{name}{suffix}"
        if target.is_file() and _within(target, directory):
            try:
                target.unlink()
            except OSError as exc:
                return RemoveResult(ok=False, name=name, error=str(exc))
            return RemoveResult(ok=True, name=name)
    return RemoveResult(ok=False, name=name, error=f"pack '{name}' is not installed")
