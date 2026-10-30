"""Optional dependencies.

All4one runs on the standard library alone. A tool that needs more declares a
key from this table; if the dependency is missing the tool is shown as
*unavailable* with a plain-language install hint, and everything else keeps
working. No tool can take the app down.
"""

from __future__ import annotations

import importlib.util
import os
import platform
import shutil
from dataclasses import dataclass
from functools import lru_cache

IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"


@dataclass(frozen=True)
class Dependency:
    key: str
    label: str
    kind: str            # "python" or "binary"
    target: str          # module name or executable name
    hint: str
    url: str = ""
    alt: tuple[str, ...] = ()   # alternative executables


DEPS: dict[str, Dependency] = {
    # ---- python packages -------------------------------------------------
    "pillow": Dependency(
        "pillow", "Pillow (image library)", "python", "PIL",
        "pip install pillow", "https://pypi.org/project/pillow/"),
    "pypdf": Dependency(
        "pypdf", "pypdf (PDF library)", "python", "pypdf",
        "pip install pypdf", "https://pypi.org/project/pypdf/"),
    "openpyxl": Dependency(
        "openpyxl", "openpyxl (Excel files)", "python", "openpyxl",
        "pip install openpyxl", "https://pypi.org/project/openpyxl/"),
    "docx": Dependency(
        "docx", "python-docx (Word files)", "python", "docx",
        "pip install python-docx", "https://pypi.org/project/python-docx/"),
    "psutil": Dependency(
        "psutil", "psutil (process & system metrics)", "python", "psutil",
        "pip install psutil", "https://pypi.org/project/psutil/"),
    "win32": Dependency(
        "win32", "pywin32 (Windows APIs)", "python", "win32api",
        "pip install pywin32", "https://pypi.org/project/pywin32/"),
    "send2trash": Dependency(
        "send2trash", "Send2Trash (recycle bin)", "python", "send2trash",
        "pip install Send2Trash", "https://pypi.org/project/Send2Trash/"),
    "cryptography": Dependency(
        "cryptography", "cryptography (strong encryption)", "python", "cryptography",
        "pip install cryptography", "https://pypi.org/project/cryptography/"),
    "pyyaml": Dependency(
        "pyyaml", "PyYAML (YAML parsing)", "python", "yaml",
        "pip install pyyaml", "https://pypi.org/project/PyYAML/"),
    "numpy": Dependency(
        "numpy", "NumPy (numeric arrays)", "python", "numpy",
        "pip install numpy", "https://pypi.org/project/numpy/"),
    "pyperclip": Dependency(
        "pyperclip", "pyperclip (system clipboard)", "python", "pyperclip",
        "pip install pyperclip", "https://pypi.org/project/pyperclip/"),
    # ---- external programs ----------------------------------------------
    "ffmpeg": Dependency(
        "ffmpeg", "FFmpeg (audio & video)", "binary", "ffmpeg",
        "Download FFmpeg from gyan.dev and put ffmpeg.exe on your PATH",
        "https://www.gyan.dev/ffmpeg/builds/"),
    "ffprobe": Dependency(
        "ffprobe", "ffprobe (media metadata)", "binary", "ffprobe",
        "Ships with FFmpeg — put it next to ffmpeg.exe on your PATH",
        "https://www.gyan.dev/ffmpeg/builds/"),
    "tesseract": Dependency(
        "tesseract", "Tesseract (OCR engine)", "binary", "tesseract",
        "Install Tesseract-OCR, then add its folder to PATH",
        "https://github.com/UB-Mannheim/tesseract/wiki"),
    "poppler": Dependency(
        "poppler", "Poppler (pdftotext / pdfinfo)", "binary", "pdftotext",
        "Download poppler for Windows and add its bin folder to PATH",
        "https://github.com/oschwartz10612/poppler-windows/releases",
        alt=("pdftotext.exe",)),
    "pdftoppm": Dependency(
        "pdftoppm", "Poppler (pdftoppm — PDF to images)", "binary", "pdftoppm",
        "Download poppler for Windows and add its bin folder to PATH",
        "https://github.com/oschwartz10612/poppler-windows/releases",
        alt=("pdftoppm.exe",)),
    "qpdf": Dependency(
        "qpdf", "qpdf (PDF structure repair)", "binary", "qpdf",
        "Download qpdf and add it to PATH",
        "https://github.com/qpdf/qpdf/releases"),
    "7z": Dependency(
        "7z", "7-Zip (7z / rar archives)", "binary", "7z",
        "Install 7-Zip and add 7z.exe to PATH",
        "https://www.7-zip.org/download.html", alt=("7z.exe", "7za")),
    "git": Dependency(
        "git", "Git", "binary", "git",
        "Install Git for Windows", "https://git-scm.com/download/win"),
    "pandoc": Dependency(
        "pandoc", "Pandoc (document conversion)", "binary", "pandoc",
        "Install Pandoc", "https://pandoc.org/installing.html"),
    "libreoffice": Dependency(
        "libreoffice", "LibreOffice (Office conversion)", "binary", "soffice",
        "Install LibreOffice", "https://www.libreoffice.org/download/",
        alt=("soffice.exe", "libreoffice")),
}


@lru_cache(maxsize=None)
def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError, AttributeError):
        return False


@lru_cache(maxsize=None)
def _binary_available(names: tuple[str, ...]) -> bool:
    for name in names:
        if shutil.which(name):
            return True
        # PyInstaller onefile builds have a bare PATH; check next to the exe
        import sys
        here = os.path.dirname(os.path.abspath(sys.executable))
        for candidate in (name, name + ".exe"):
            if os.path.isfile(os.path.join(here, candidate)):
                return True
    return False


def is_available(key: str) -> bool:
    dep = DEPS.get(key)
    if dep is None:
        return True
    if dep.kind == "python":
        return _module_available(dep.target)
    names = (dep.target, *dep.alt)
    return _binary_available(tuple(names))


def missing(keys) -> list[str]:
    return [k for k in keys if not is_available(k)]


def status() -> list[dict]:
    """Every known dependency and whether it is present."""
    rows = []
    for key, dep in sorted(DEPS.items(), key=lambda kv: (kv[1].kind, kv[1].label.lower())):
        rows.append({
            "key": key, "label": dep.label, "kind": dep.kind,
            "hint": dep.hint, "url": dep.url, "available": is_available(key),
        })
    return rows


def hint_for(keys) -> str:
    bits = []
    for key in keys:
        dep = DEPS.get(key)
        if dep and not is_available(key):
            bits.append(dep.hint)
    return " · ".join(bits)


def refresh() -> None:
    _module_available.cache_clear()
    _binary_available.cache_clear()
