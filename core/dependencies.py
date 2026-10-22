"""Curated catalogue of the external dependencies the tool packs actually need.

This is the honest, *closed* list: every entry below is a dependency that some
pack in this repository really declares in its ``dependencies`` field, and
nothing else is listed.  The set is checked against the live registry by
``tests/test_dependencies.py``, so it can never silently drift from the packs.

Design rules (see the product brief):

* **Never silently download and run an arbitrary binary.**  :func:`install_plan`
  returns *instructions*, ordered from least to most invasive:

  1. ``path``    — the tool is already on ``PATH``; nothing to do.
  2. ``builtin`` — it ships with Windows; nothing to download.
  3. ``pip``     — a Python package, installed with the interpreter you run.
  4. ``winget`` / ``choco`` — a well-known package-manager command the user
     runs (or explicitly confirms).
  5. ``manual``  — the official vendor download page over HTTPS.

* **Nothing here executes a download.**  The module only reports what to do;
  the GUI shows the command / link and lets the user act.  There is no
  "download and run" path anywhere in the codebase.

* **Never claim a tool will work while its dependency is missing.**  The
  registry consults :func:`check` (through :class:`core.capability_checker.CapabilityChecker`)
  and marks a tool unavailable until the dependency is really present.
"""

from __future__ import annotations

import importlib.metadata
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

# Distribution name to query for a version, for the pip-installable entries.
_DIST_NAME = {
    "Pillow": "Pillow",
    "openpyxl": "openpyxl",
    "python-docx": "python-docx",
    "python-pptx": "python-pptx",
    "python:PIL": "Pillow",
    "python:psutil": "psutil",
    "python:pyperclip": "pyperclip",
    "python:yaml": "PyYAML",
}

# A short argument that makes each external program print its version.
_VERSION_FLAG = {
    "ffmpeg": ["-version"],
    "ffprobe": ["-version"],
    "gpg": ["--version"],
    "pdftotext": ["-v"],
    "pdfunite": ["-v"],
    "qpdf": ["--version"],
}

_VERSION_TIMEOUT = 5


@dataclass(frozen=True)
class InstallStep:
    """One way to obtain a dependency, ordered by preference."""

    method: str  # path | builtin | pip | winget | choco | manual
    label: str
    command: str = ""
    url: str = ""
    note: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"method": self.method, "label": self.label, "command": self.command, "url": self.url, "note": self.note}


@dataclass(frozen=True)
class Dependency:
    """A catalogue entry: what it is, why it is needed, and how to get it."""

    name: str
    kind: str  # "external" | "python-package" | "windows-builtin" | "interpreter"
    summary: str
    why: str
    steps: tuple[InstallStep, ...] = ()
    homepage: str = ""
    packs: tuple[str, ...] = field(default=())

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "summary": self.summary,
            "why": self.why,
            "homepage": self.homepage,
            "packs": list(self.packs),
            "steps": [s.as_dict() for s in self.steps],
        }


def _pip(package: str, url: str) -> InstallStep:
    return InstallStep(
        method="pip",
        label=f"pip install {package}",
        command=f"{_python_exe()} -m pip install {package}",
        url=url,
        note=(
            "Use the same Python you run the suite with.  The packaged "
            "utility_suite.exe carries its own interpreter, so installing into a "
            "different Python will not reach it — in that case disable the pack "
            "instead (the pack is built in, the package is not)."
        ),
    )


def _python_exe() -> str:
    return "py -3" if sys.platform == "win32" else "python3"


CATALOGUE: dict[str, Dependency] = {
    # ------------------------------------------------------------- media
    "ffmpeg": Dependency(
        name="ffmpeg",
        kind="external",
        summary="Command-line audio/video converter and muxer.",
        why="The audio and video packs shell out to ffmpeg to convert, trim, normalise, mux and export media.",
        homepage="https://ffmpeg.org/download.html",
        steps=(
            InstallStep("winget", "winget install --id Gyan.FFmpeg -e", "winget install --id Gyan.FFmpeg -e",
                        "", "Installs the well-known Windows build; open a new terminal afterwards."),
            InstallStep("choco", "choco install ffmpeg -y", "choco install ffmpeg -y", "",
                        "Needs Chocolatey (https://chocolatey.org/install)."),
            InstallStep("manual", "Download from gyan.dev", "",
                        "https://www.gyan.dev/ffmpeg/builds/",
                        "Unzip, then add the 'bin' folder to PATH so ffmpeg and ffprobe are found."),
        ),
    ),
    "ffprobe": Dependency(
        name="ffprobe",
        kind="external",
        summary="Media stream inspector (ships inside the FFmpeg package).",
        why="Audio, video and media-metadata packs call ffprobe to read durations, codecs and stream details.",
        homepage="https://ffmpeg.org/download.html",
        steps=(
            InstallStep("winget", "winget install --id Gyan.FFmpeg -e", "winget install --id Gyan.FFmpeg -e", "",
                        "ffprobe is included with FFmpeg — installing ffmpeg installs ffprobe too."),
            InstallStep("manual", "Download from gyan.dev", "", "https://www.gyan.dev/ffmpeg/builds/",
                        "Add the 'bin' folder to PATH; ffprobe lives beside ffmpeg."),
        ),
    ),
    # ------------------------------------------------------------- documents
    "pdftotext": Dependency(
        name="pdftotext",
        kind="external",
        summary="Poppler PDF-to-text utility.",
        why="The document and PDF packs use pdftotext to pull text out of PDF files.",
        homepage="https://github.com/oschwartz10612/poppler-windows/releases/",
        steps=(
            InstallStep("choco", "choco install poppler -y", "choco install poppler -y", "",
                        "Needs Chocolatey; confirm the package id with 'choco search poppler'."),
            InstallStep("manual", "Poppler for Windows (official build)", "",
                        "https://github.com/oschwartz10612/poppler-windows/releases/",
                        "Unzip and add the 'Library\\bin' folder to PATH."),
        ),
    ),
    "pdfunite": Dependency(
        name="pdfunite",
        kind="external",
        summary="Poppler utility to merge PDF files (ships with Poppler).",
        why="The PDF pack uses pdfunite to merge several PDFs into one.",
        homepage="https://github.com/oschwartz10612/poppler-windows/releases/",
        steps=(
            InstallStep("choco", "choco install poppler -y", "choco install poppler -y", "",
                        "pdfunite is included with Poppler."),
            InstallStep("manual", "Poppler for Windows (official build)", "",
                        "https://github.com/oschwartz10612/poppler-windows/releases/",
                        "Add the 'Library\\bin' folder to PATH."),
        ),
    ),
    "qpdf": Dependency(
        name="qpdf",
        kind="external",
        summary="PDF structural transformation tool.",
        why="The PDF pack uses qpdf to compress, rotate and inspect PDF structure.",
        homepage="https://qpdf.readthedocs.io/en/stable/",
        steps=(
            InstallStep("winget", "winget search qpdf", "winget search qpdf", "",
                        "Run 'winget search qpdf' and install the id it lists, then reopen the terminal."),
            InstallStep("choco", "choco install qpdf -y", "choco install qpdf -y", "",
                        "Needs Chocolatey; confirm the package id with 'choco search qpdf'."),
            InstallStep("manual", "Official qpdf releases", "", "https://github.com/qpdf/qpdf/releases",
                        "Download the Windows installer or zip and put qpdf on PATH."),
        ),
    ),
    # ------------------------------------------------------------- crypto
    "gpg": Dependency(
        name="gpg",
        kind="external",
        summary="GNU Privacy Guard (OpenPGP encryption).",
        why="The security-tools pack uses gpg to encrypt, decrypt and sign files.",
        homepage="https://gnupg.org/download/",
        steps=(
            InstallStep("winget", "winget install --id GnuPG.GnuPG -e", "winget install --id GnuPG.GnuPG -e", "",
                        "Installs GnuPG for Windows."),
            InstallStep("choco", "choco install gnupg -y", "choco install gnupg -y", "",
                        "Needs Chocolatey."),
            InstallStep("manual", "GnuPG for Windows installer", "", "https://gnupg.org/download/",
                        "Install Gpg4win / GnuPG and reopen the terminal."),
        ),
    ),
    # ------------------------------------------------------------- python packages
    "Pillow": Dependency(
        name="Pillow",
        kind="python-package",
        summary="Python imaging library (import name: PIL).",
        why="The image batch and advanced-imaging packs use Pillow to read, resize, convert and watermark images.",
        homepage="https://pypi.org/project/Pillow/",
        steps=(_pip("Pillow", "https://pypi.org/project/Pillow/"),),
    ),
    "python:PIL": Dependency(
        name="python:PIL",
        kind="python-package",
        summary="Python imaging library (Pillow), referenced by import name.",
        why="The multimedia pack imports PIL directly for thumbnail generation.",
        homepage="https://pypi.org/project/Pillow/",
        steps=(_pip("Pillow", "https://pypi.org/project/Pillow/"),),
    ),
    "openpyxl": Dependency(
        name="openpyxl",
        kind="python-package",
        summary="Read/write Microsoft Excel .xlsx workbooks.",
        why="The office-tools pack uses openpyxl to inspect and edit spreadsheets.",
        homepage="https://pypi.org/project/openpyxl/",
        steps=(_pip("openpyxl", "https://pypi.org/project/openpyxl/"),),
    ),
    "python-docx": Dependency(
        name="python-docx",
        kind="python-package",
        summary="Read/write Microsoft Word .docx documents (import name: docx).",
        why="The office-tools pack uses python-docx for Word documents.",
        homepage="https://pypi.org/project/python-docx/",
        steps=(_pip("python-docx", "https://pypi.org/project/python-docx/"),),
    ),
    "python-pptx": Dependency(
        name="python-pptx",
        kind="python-package",
        summary="Read/write Microsoft PowerPoint .pptx decks (import name: pptx).",
        why="The office-tools pack uses python-pptx for presentations.",
        homepage="https://pypi.org/project/python-pptx/",
        steps=(_pip("python-pptx", "https://pypi.org/project/python-pptx/"),),
    ),
    "python:psutil": Dependency(
        name="python:psutil",
        kind="python-package",
        summary="Cross-platform process and system-monitoring library.",
        why="The monitoring pack reads CPU, memory, disk and process data through psutil.",
        homepage="https://pypi.org/project/psutil/",
        steps=(_pip("psutil", "https://pypi.org/project/psutil/"),),
    ),
    "python:pyperclip": Dependency(
        name="python:pyperclip",
        kind="python-package",
        summary="Cross-platform clipboard access library.",
        why="The clipboard pack reads and writes the system clipboard through pyperclip.",
        homepage="https://pypi.org/project/pyperclip/",
        steps=(_pip("pyperclip", "https://pypi.org/project/pyperclip/"),),
    ),
    "python:yaml": Dependency(
        name="python:yaml",
        kind="python-package",
        summary="YAML parser/serialiser (PyYAML).",
        why="The developer-tools pack validates and converts YAML through PyYAML.",
        homepage="https://pypi.org/project/PyYAML/",
        steps=(_pip("PyYAML", "https://pypi.org/project/PyYAML/"),),
    ),
    "python:tkinter": Dependency(
        name="python:tkinter",
        kind="python-package",
        summary="Python's standard Tk GUI toolkit binding.",
        why="The clipboard pack uses tkinter for clipboard access that does not need pyperclip.",
        homepage="https://www.python.org/downloads/",
        steps=(
            InstallStep("manual", "Reinstall Python with the tcl/tk option", "", "https://www.python.org/downloads/",
                        "On Windows tkinter ships with the official python.org installer — tick 'tcl/tk and IDLE'."),
        ),
    ),
    # ------------------------------------------------------------- interpreter
    "python": Dependency(
        name="python",
        kind="interpreter",
        summary="A Python interpreter.",
        why="The package-and-environment pack inspects the Python environment the suite runs on.",
        homepage="https://www.python.org/downloads/",
        steps=(
            InstallStep("builtin", "Already satisfied", "", "",
                        "The suite is itself running on Python, so this dependency is always present."),
        ),
    ),
}

# Windows built-ins: no download, present on Windows only.  Their "how to get"
# is the operating system, so the plan is a single explanatory step.
for _name, _why in {
    "powershell": "many diagnostics, monitoring, shell, security and system packs run PowerShell cmdlets",
    "reg": "the registry and system packs read and write the registry with reg.exe",
    "regedit": "the power-tools pack opens the Registry Editor",
    "sc": "the system-utils pack queries and controls Windows services with sc.exe",
    "schtasks": "the automation and startup packs schedule and inspect tasks with schtasks.exe",
    "wevtutil": "the event and system packs read Windows event logs with wevtutil.exe",
    "pnputil": "the driver and power packs enumerate and manage drivers with pnputil.exe",
    "cleanmgr": "the maintenance pack launches the Disk Cleanup utility",
    "ipconfig": "the network-diagnostics pack reads adapter configuration with ipconfig",
    "nslookup": "the advanced-networking pack resolves DNS names with nslookup",
    "ping": "the advanced-networking pack tests reachability with ping",
}.items():
    CATALOGUE[_name] = Dependency(
        name=_name,
        kind="windows-builtin",
        summary=f"Windows built-in command ({_name}).",
        why=f"Because {_why}.",
        homepage="",
        steps=(
            InstallStep("builtin", "Ships with Windows", "", "",
                        "No download needed — this command is part of Windows and works "
                        "automatically when the suite runs on Windows."),
        ),
    )


def all_dependencies() -> list[str]:
    """Every dependency in the catalogue, sorted case-insensitively."""
    return sorted(CATALOGUE, key=str.lower)


def get(dependency: str) -> Dependency | None:
    """Return the catalogue entry for ``dependency`` (exact key match)."""
    return CATALOGUE.get(dependency)


def is_known(dependency: str) -> bool:
    return dependency in CATALOGUE


def check(dependency: str) -> dict[str, Any]:
    """Report whether ``dependency`` is installed, and its version if detectable.

    Returns a dict: ``{dependency, installed, version, kind, detail}``.  Never
    raises — a missing tool, a slow command or an unreadable version string all
    degrade to ``installed=False`` / ``version=None``.
    """
    from .capability_checker import CapabilityChecker

    entry = CATALOGUE.get(dependency)
    kind = entry.kind if entry else "unknown"
    installed = CapabilityChecker().check_dependencies([dependency])
    version = _detect_version(dependency, kind) if installed else None
    if installed:
        detail = f"Installed{(' — ' + version) if version else ''}."
    else:
        detail = entry.summary if entry else f"'{dependency}' is not installed."
    return {
        "dependency": dependency,
        "installed": installed,
        "version": version,
        "kind": kind,
        "detail": detail,
    }


def _detect_version(dependency: str, kind: str) -> str | None:
    """Best-effort version string for an installed dependency (never raises)."""
    if kind == "python-package" or dependency.startswith("python:"):
        dist = _DIST_NAME.get(dependency)
        if not dist:
            return None
        try:
            return importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            return None
        except Exception:
            return None
    if kind == "interpreter":
        return sys.version.split()[0]
    if kind == "windows-builtin":
        return "built into Windows" if sys.platform == "win32" else None
    exe = shutil.which(dependency)
    if not exe:
        return None
    flags = _VERSION_FLAG.get(dependency, ["--version"])
    for flag in (flags, ["-version"], ["--version"], ["-v"], ["-V"]):
        try:
            proc = subprocess.run(
                [exe, *flag],
                capture_output=True,
                text=True,
                timeout=_VERSION_TIMEOUT,
                shell=False,
            )
        except Exception:
            continue
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        for line in text.splitlines():
            line = line.strip()
            if line:
                return line[:120]
    return None


def install_plan(dependency: str) -> dict[str, Any]:
    """Return the recommended, ordered ways to obtain ``dependency``.

    The returned dict has ``{dependency, kind, summary, why, homepage, steps,
    confirm_required}``.  ``confirm_required`` is True when a step would run a
    download or a package manager — the caller must ask the user first.  An
    unknown dependency yields an empty plan rather than a fabricated one.
    """
    entry = CATALOGUE.get(dependency)
    if entry is None:
        return {
            "dependency": dependency,
            "kind": "unknown",
            "summary": "",
            "why": "",
            "homepage": "",
            "steps": [],
            "confirm_required": False,
            "known": False,
        }
    state = check(dependency)
    steps = list(entry.steps)
    if state["installed"]:
        steps = [
            InstallStep(
                "path",
                "Already installed",
                "",
                "",
                state["detail"],
            ),
            *steps,
        ]
    return {
        "dependency": entry.name,
        "kind": entry.kind,
        "summary": entry.summary,
        "why": entry.why,
        "homepage": entry.homepage,
        "steps": [s.as_dict() for s in steps],
        "confirm_required": entry.kind in {"external", "python-package"} and not state["installed"],
        "known": True,
        "installed": state["installed"],
        "version": state["version"],
    }


def packs_using(dependency: str, tools: Iterable[dict[str, Any]]) -> list[str]:
    """Packs whose tools declare ``dependency`` (derived from real metadata)."""
    packs: set[str] = set()
    for tool in tools:
        deps = tool.get("dependencies") or []
        if dependency in deps:
            packs.add(str(tool.get("pack", "")))
    return sorted(p for p in packs if p)


def missing_dependencies(tools: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Count, per missing dependency, how many tools are blocked by it."""
    from .capability_checker import CapabilityChecker

    checker = CapabilityChecker()
    counts: dict[str, int] = {}
    for tool in tools:
        for dep in tool.get("dependencies") or []:
            if not checker.check_dependencies([dep]):
                counts[dep] = counts.get(dep, 0) + 1
    return counts


def report(tools: Iterable[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Full catalogue as plain dicts, with live state and (optional) pack usage."""
    tools = list(tools or [])
    out: list[dict[str, Any]] = []
    for name in all_dependencies():
        entry = CATALOGUE[name]
        state = check(name)
        record = entry.as_dict()
        record.update(state)
        if tools:
            record["packs"] = packs_using(name, tools)
        out.append(record)
    return out
