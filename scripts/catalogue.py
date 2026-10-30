"""Generate TOOL_CATALOG.md from the live registry — never hand-edited."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import __version__, deps, registry  # noqa: E402

KIND_LABEL = {
    "text": "text", "password": "secret", "multiline": "multiline", "int": "number",
    "float": "number", "choice": "choice", "multi": "multi", "bool": "toggle",
    "file": "file", "files": "files", "dir": "folder", "save": "save as",
    "color": "colour", "slider": "slider",
}


def escape(text: str) -> str:
    return text.replace("|", "\\|")


def main() -> int:
    tools = registry.all_tools()
    stats = registry.stats()
    lines: list[str] = []
    lines.append("# All4one — Complete Tool Catalogue\n")
    lines.append(f"*{stats['tools']} tools · {stats['categories']} categories · "
                 f"version {__version__} · generated from the live registry by "
                 f"`scripts/catalogue.py` — do not edit by hand.*\n")
    lines.append("Every tool below is a working implementation with its own options and its "
                 "own page in the app. The **Options** column is the exact set of controls "
                 "that page shows.\n")
    lines.append("| Category | Tools |")
    lines.append("|---|---|")
    counts = registry.counts()
    for category in registry.CATEGORY_NAMES:
        lines.append(f"| {category} | {counts[category]} |")
    lines.append("")

    for category in registry.CATEGORY_NAMES:
        items = registry.in_category(category)
        if not items:
            continue
        lines.append(f"\n## {category}\n")
        lines.append(f"*{registry.blurb(category)} · {len(items)} tools*\n")
        lines.append("| Tool | Command | Options | Needs | Description |")
        lines.append("|---|---|---|---|---|")
        for tool in items:
            options = ", ".join(
                f"`{field.key}` ({KIND_LABEL.get(field.kind, field.kind)}"
                f"{'' if not field.required else ', required'})"
                for field in tool.fields) or "—"
            needs = ", ".join(tool.needs) or ("Windows" if tool.is_windows_only else "—")
            if tool.destructive:
                needs = (needs + " · " if needs != "—" else "") + "changes data"
            lines.append(f"| **{escape(tool.name)}** | `{tool.id}` | {escape(options)} | "
                         f"{escape(needs)} | {escape(tool.summary)} |")
        lines.append("")

    # Machine-independent by design: whether a dependency happens to be
    # installed on the machine that ran the generator must not change the file.
    lines.append("\n## Optional dependencies\n")
    lines.append("| Dependency | Type | Unlocks | Install |")
    lines.append("|---|---|---|---|")
    for key in sorted(deps.DEPS):
        dep = deps.DEPS[key]
        count = sum(1 for tool in tools if key in tool.needs)
        if not count:
            continue
        lines.append(f"| {dep.label} | {dep.kind} | {count} tools | `{dep.hint}` |")
    lines.append("\nNothing in this table is required: the app and "
                 f"{sum(1 for t in tools if not t.needs)} tools run on the standard library "
                 "alone.\n")

    target = ROOT / "TOOL_CATALOG.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {target} ({len(tools)} tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
