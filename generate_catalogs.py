"""Regenerate TOOL_CATALOG.md and EXPANSION_CATALOG.md from the live registry.

Run as ``python generate_catalogs.py`` from the repository root after any
tool add/remove. The catalogs are generated deterministically from the same
AST-literal source used by ``audit.py`` (no interpreter imports, no
``__pycache__`` side effects), so they can never drift from the registry
again. ``audit.py`` verifies the headers stay in sync.
"""
from __future__ import annotations

import sys

# Never litter the source tree with bytecode caches while generating docs.
sys.dont_write_bytecode = True

from pathlib import Path  # noqa: E402

from audit import ROOT, pack_names, source_tools  # noqa: E402

VERSION = (ROOT / "VERSION.txt").read_text(encoding="utf-8").strip()


def build_rows():
    """Return (pack -> [tool dicts], flat list of all tools)."""
    by_pack = {}
    for pack in pack_names():
        by_pack[pack] = source_tools(pack)
    return by_pack


def title_case(name: str) -> str:
    return name.replace("-", " ").title()


def render_tool_catalog(by_pack) -> str:
    total = sum(len(v) for v in by_pack.values())
    lines = [
        f"# Utility Suite {VERSION} — Complete Tool Catalogue",
        "",
        f"Total tools: {total}",
        f"Plugin packs: {len(by_pack)}",
        "",
    ]
    # Group sections by the human-readable tool "category" declared in each
    # pack's register_tools() metadata (matches how the GUI groups tools);
    # fall back to a prettified pack name if a tool has no category.
    def section_for(t, pack):
        return t.get("category") or title_case(pack)

    for pack in sorted(by_pack, key=lambda pk: min(
            (t.get("category", "") or title_case(pk)).lower() for t in by_pack[pk])):
        tools = by_pack[pack]
        lines.append(f"## {section_for(tools[0], pack)}")
        lines.append("")
        lines.append("| Tool | Command | Pack | Dependencies | Description |")
        lines.append("|---|---|---|---|---|")
        for t in sorted(tools, key=lambda x: x["name"].lower()):
            deps = ", ".join(t.get("dependencies", [])) or "—"
            desc = t["description"].replace("|", "\\|")
            lines.append(
                f"| {t['name']} | `{t["cli_command"]}` | `{pack}` | {deps} | {desc} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_expansion_catalog(by_pack) -> str:
    total = sum(len(v) for v in by_pack.values())
    lines = [
        "# Plugin Pack Catalogue",
        "",
        f"**{len(by_pack)} packs / {total} tools**",
        "",
    ]
    for pack in sorted(by_pack):
        lines.append(f"- `{pack}` — {len(by_pack[pack])} tools")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    by_pack = build_rows()
    (ROOT / "TOOL_CATALOG.md").write_text(render_tool_catalog(by_pack), encoding="utf-8")
    (ROOT / "EXPANSION_CATALOG.md").write_text(render_expansion_catalog(by_pack), encoding="utf-8")
    total = sum(len(v) for v in by_pack.values())
    print(f"Generated TOOL_CATALOG.md and EXPANSION_CATALOG.md ({total} tools / {len(by_pack)} packs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
