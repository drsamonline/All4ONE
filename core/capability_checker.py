"""Capability/dependency checks used by the registry and GUI.

Two kinds of dependencies exist:

* **Python packages** (``python-docx``, ``openpyxl``, ``Pillow``, ...) are
  checked with :mod:`importlib` against their real module name — never with
  ``shutil.which`` (a package is not an executable on PATH).
* **External programs** (``ffmpeg``, ``gpg``, ``powershell``, ...) are looked
  up on PATH; Windows built-ins report as available on Windows only.

Every dependency also carries a human-readable download hint so the GUI can
tell the user exactly what to install and where from.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from collections.abc import Iterable

# Commands that ship with Windows; they can never be found on Linux/macOS.
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
    "ipconfig",
}

# Python package name -> importable module name.
PYTHON_PACKAGES = {
    "python-docx": "docx",
    "python-pptx": "pptx",
    "python-ldap": "ldap",
    "pillow": "PIL",
    "opencv-python": "cv2",
    "pypdf": "pypdf",
    "pyperclip": "pyperclip",
    "psutil": "psutil",
    "openpyxl": "openpyxl",
    "yaml": "yaml",
    "pyyaml": "yaml",
}

# Where users can download each external dependency (shown in GUI / CLI help).
DOWNLOAD_URLS = {
    "ffmpeg": "https://www.gyan.dev/ffmpeg/builds/ (Windows) | https://ffmpeg.org/download.html (all platforms)",
    "ffprobe": "Bundled with FFmpeg — https://www.gyan.dev/ffmpeg/builds/ (add the bin folder to PATH)",
    "gpg": "https://gnupg.org/download/ (Windows: GnuPG4Win installer)",
    "pdftotext": "Poppler utilities — https://github.com/oschwartz10612/poppler-windows/releases/",
    "qpdf": "https://github.com/qpdf/qpdf/releases (Windows MSI installer)",
    "pdfunite": "Bundled with Poppler — https://github.com/oschwartz10612/poppler-windows/releases/",
    "tesseract": "https://github.com/UB-Mannheim/tesseract/wiki (Windows installer)",
    # pip-installable Python packages
    "python-docx": "pip install python-docx  (https://pypi.org/project/python-docx/)",
    "python-pptx": "pip install python-pptx  (https://pypi.org/project/python-pptx/)",
    "openpyxl": "pip install openpyxl  (https://pypi.org/project/openpyxl/)",
    "Pillow": "pip install Pillow  (https://pypi.org/project/Pillow/)",
    "pyperclip": "pip install pyperclip  (https://pypi.org/project/pyperclip/)",
    "psutil": "pip install psutil  (https://pypi.org/project/psutil/)",
    "python:tkinter": "Included with Python — reinstall Python and tick 'tcl/tk' (https://www.python.org/downloads/)",
}

# Windows built-ins need no download; explain instead.
WINDOWS_ONLY_NOTE = (
    "Built into Windows — these tools run automatically when you launch the "
    "suite on Windows (no download needed)"
)


def download_hint(dependency: str) -> str:
    """Return guidance on how to obtain a missing dependency."""
    key = dependency.strip()
    low = key.lower()
    if low in WINDOWS_COMMANDS:
        return WINDOWS_ONLY_NOTE
    if key in DOWNLOAD_URLS:
        return DOWNLOAD_URLS[key]
    if low in PYTHON_PACKAGES:
        return f"pip install {key}"
    if low == "python":
        return "Install Python from https://www.python.org/downloads/ and add it to PATH"
    return f"Install '{key}' and make sure it is on your PATH — see https://github.com/drsamonline/All4ONE/blob/main/INSTALLATION.md"


class CapabilityChecker:
    def __init__(self) -> None:
        self._cache: dict[str, bool] = {}

    @staticmethod
    def _module_available(module: str) -> bool:
        try:
            return importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            return False

    def _check_one(self, dependency: str) -> bool:
        if dependency in self._cache:
            return self._cache[dependency]
        raw = dependency.strip()
        low = raw.lower()
        if raw.startswith("python:"):
            ok = self._module_available(raw.split(":", 1)[1])
        elif low in PYTHON_PACKAGES:
            # A pip package is imported, not executed — check the module.
            ok = self._module_available(PYTHON_PACKAGES[low])
        elif low in WINDOWS_COMMANDS:
            if sys.platform == "win32":
                ok = shutil.which(raw) is not None or low in {
                    "regedit", "cleanmgr", "ipconfig", "reg", "cmd",
                    "attrib", "taskkill", "control",
                }
            else:
                ok = False
        elif low == "python":
            ok = shutil.which("python") is not None or shutil.which("python3") is not None or True
        else:
            ok = shutil.which(raw) is not None
        self._cache[dependency] = ok
        return ok

    def check_dependencies(self, dependencies: Iterable[str]) -> bool:
        return not self.get_missing(dependencies)

    def get_missing(self, dependencies: Iterable[str]) -> list[str]:
        return [dep for dep in dependencies if not self._check_one(dep)]
