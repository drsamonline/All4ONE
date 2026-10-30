"""The catalogue: import every tool module, validate it, answer questions.

There are no plugin packs any more. A tool module is a file in ``tools/`` that
uses the ``@tool`` decorator; it is discovered, validated and indexed here.
Adding a tool means adding a function — nothing to register, package or enable.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from typing import Iterable

from . import deps
from .tool import Tool, collect


@dataclass(frozen=True)
class Category:
    name: str
    blurb: str


# Order matters: it is the order of the sidebar.
CATEGORIES: tuple[Category, ...] = (
    Category("Files", "Copy, move, rename, compare and inspect files and folders"),
    Category("Archives", "Zip, tar and 7-Zip archives"),
    Category("Text", "Transform, analyse and clean text"),
    Category("Data", "JSON, CSV, XML, YAML and SQLite"),
    Category("Encoding", "Base64, hex, URLs, hashes and checksums"),
    Category("Images", "Resize, convert, watermark and inspect images"),
    Category("PDF", "Merge, split, extract and protect PDFs"),
    Category("Media", "Audio and video conversion with FFmpeg"),
    Category("Documents", "Word, Excel and document conversion"),
    Category("Network", "Ports, DNS, HTTP, IP maths and diagnostics"),
    Category("System", "Windows settings, processes and startup"),
    Category("Disk", "Space, drives and large-file hunting"),
    Category("Developer", "Code, regex, diffs and project checks"),
    Category("Security", "Passwords, encryption and audits"),
    Category("Numbers", "Dates, times, units and calculations"),
    Category("Generators", "IDs, passwords, data and dummy files"),
)

CATEGORY_NAMES = tuple(c.name for c in CATEGORIES)
_BLURB = {c.name: c.blurb for c in CATEGORIES}


class CatalogueError(RuntimeError):
    pass


_tools: list[Tool] | None = None
_by_id: dict[str, Tool] | None = None


def _load() -> list[Tool]:
    global _tools, _by_id
    if _tools is not None:
        return _tools

    from tools import __path__ as tools_path  # noqa: PLC0415

    found: list[Tool] = []
    for info in pkgutil.iter_modules(tools_path):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"tools.{info.name}")
        found.extend(collect(module))

    seen: dict[str, Tool] = {}
    problems: list[str] = []
    for t in found:
        if t.id in seen:
            problems.append(f"duplicate tool id {t.id!r} ({t.name})")
        if t.category not in _BLURB:
            problems.append(f"{t.id}: unknown category {t.category!r}")
        if not t.summary or len(t.summary) < 12:
            problems.append(f"{t.id}: summary too short")
        for key in t.needs:
            if key not in deps.DEPS:
                problems.append(f"{t.id}: unknown dependency key {key!r}")
        seen[t.id] = t

    if problems:
        raise CatalogueError("catalogue problems:\n  " + "\n  ".join(problems))

    _tools = sorted(seen.values(), key=lambda t: (CATEGORY_NAMES.index(t.category), t.name.lower()))
    _by_id = seen
    return _tools


def all_tools() -> list[Tool]:
    return list(_load())


def get(tool_id: str) -> Tool | None:
    _load()
    assert _by_id is not None
    return _by_id.get(tool_id)


def in_category(name: str) -> list[Tool]:
    return [t for t in _load() if t.category == name]


def counts() -> dict[str, int]:
    out = {name: 0 for name in CATEGORY_NAMES}
    for t in _load():
        out[t.category] += 1
    return out


def blurb(category: str) -> str:
    return _BLURB.get(category, "")


def is_available(tool: Tool) -> tuple[bool, str]:
    """Can this tool run here, and if not, why not."""
    if tool.is_windows_only and not deps.IS_WINDOWS:
        return False, "Windows only"
    missing = deps.missing(tool.needs)
    if missing:
        return False, deps.hint_for(missing) or "Missing dependency"
    return True, ""


def search(query: str, limit: int = 60) -> list[Tool]:
    """Ranked search over name, category, summary and keywords."""
    q = (query or "").strip().lower()
    if not q:
        return []
    terms = [t for t in q.split() if t]

    scored: list[tuple[float, Tool]] = []
    for t in _load():
        haystack = " ".join((t.name, t.category, t.summary, t.keywords, t.id)).lower()
        score = 0.0
        for term in terms:
            if term in t.id.lower():
                score += 6
            if term in t.name.lower():
                score += 5
            if t.name.lower().startswith(term):
                score += 4
            if term in t.category.lower():
                score += 2
            if term in haystack:
                score += 1
        if score and all(term in haystack for term in terms):
            scored.append((score, t))
    scored.sort(key=lambda pair: (-pair[0], pair[1].name.lower()))
    return [t for _, t in scored[:limit]]


def suggest(query: str, limit: int = 6) -> list[Tool]:
    return search(query, limit=limit)


def stats() -> dict:
    tools = _load()
    ready = sum(1 for t in tools if is_available(t)[0])
    return {
        "tools": len(tools),
        "categories": len(CATEGORIES),
        "ready": ready,
        "unavailable": len(tools) - ready,
        "windows_only": sum(1 for t in tools if t.is_windows_only),
    }


def iter_all() -> Iterable[Tool]:
    return iter(_load())


def reload() -> None:
    """Drop the cache (used by tests and the dependency refresh button)."""
    global _tools, _by_id
    _tools = None
    _by_id = None
