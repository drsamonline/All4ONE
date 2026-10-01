"""One-shot registry description rewriter.

Replaces the auto-generated boilerplate descriptions ("X: performs the x
action with structured, human-readable output.") in every plugin pack's
register_tools() literal with real, per-tool sentences from a curated map
keyed by cli_command (scripts/descriptions_map.py). Tools not present in
the map fall back to a readable sentence built from the tool name, and the
script prints any commands that still used boilerplate so the map can be
extended later.

Run: python scripts/write_descriptions.py
Then: python generate_catalogs.py && python audit.py
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOILER = re.compile(r"performs the .* action with structured")
MAP_FILE = ROOT / "scripts" / "descriptions_map.py"


def load_map():
    if not MAP_FILE.exists():
        return {}
    tree = ast.parse(MAP_FILE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "DESCRIPTIONS":
            return ast.literal_eval(node.value)
    return {}


def fallback(name: str) -> str:
    """Readable sentence from the display name (used only when unmapped)."""
    n = name.strip().rstrip(".")
    return f"{n}: report {n.lower()} details as structured, parseable output."


def rewrite_pack(init_path: Path, mapping: dict) -> int:
    src = init_path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    tools = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "register_tools":
            for stmt in node.body:
                if isinstance(stmt, ast.Return):
                    tools = ast.literal_eval(stmt.value)
    if not tools:
        return 0
    lines = src.splitlines(keepends=True)
    cmd_re = re.compile(r'^\s*"cli_command": "([^"]+)",\s*$')
    desc_re = re.compile(r'^(\s*)"description": "(.*)",\s*$')
    out = list(lines)
    changed = 0
    for i, line in enumerate(lines):
        m = cmd_re.match(line.rstrip("\n"))
        if not m:
            continue
        cmd = m.group(1)
        j = i - 1
        while j >= 0:
            dm = desc_re.match(lines[j].rstrip("\n"))
            if dm:
                old = dm.group(2)
                if BOILER.search(old.replace('\\"', '"')):
                    tool = next((t for t in tools if t.get("cli_command") == cmd), None)
                    name = tool["name"] if tool else cmd
                    new = mapping.get(cmd) or fallback(name)
                    indent = dm.group(1)
                    escaped = new.replace("\\", "\\\\").replace('"', '\\"')
                    out[j] = f'{indent}"description": "{escaped}",\n'
                    changed += 1
                break
            j -= 1
    init_path.write_text("".join(out), encoding="utf-8")
    return changed


def main() -> int:
    sys.dont_write_bytecode = True
    mapping = load_map()
    total = 0
    missing = []
    for init_path in sorted(ROOT.glob("*/__init__.py")):
        if ".git" in init_path.parts or "__pycache__" in init_path.parts:
            continue
        try:
            text = init_path.read_text(encoding="utf-8")
            tree = ast.parse(text)
        except SyntaxError:
            print(f"SKIP (syntax): {init_path}")
            continue
        boiler_cmds = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "register_tools":
                for stmt in node.body:
                    if isinstance(stmt, ast.Return):
                        for t in ast.literal_eval(stmt.value):
                            if BOILER.search(t.get("description", "")):
                                boiler_cmds.append(t.get("cli_command"))
        if boiler_cmds:
            total += rewrite_pack(init_path, mapping)
            missing += [c for c in boiler_cmds if c not in mapping]
    print(f"Rewrote {total} descriptions ({len(mapping)} curated).")
    if missing:
        print(f"Fallback used for {len(missing)} unmapped commands; first 20:")
        for c in missing[:20]:
            print("  ", c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
