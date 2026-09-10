from __future__ import annotations
import sys

sys.dont_write_bytecode = True
import ast, zipfile, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXCLUDE = {"core", "tests"}


def pack_names():
    return sorted(
        p.name
        for p in ROOT.iterdir()
        if p.is_dir() and (p / "__init__.py").exists() and p.name not in EXCLUDE
    )


def source_tools(pack):
    """Read the literal register_tools() return value without importing the pack."""
    tree = ast.parse((ROOT / pack / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "register_tools":
            for stmt in node.body:
                if isinstance(stmt, ast.Return):
                    return ast.literal_eval(stmt.value)
    raise ValueError(f"{pack}: register_tools() literal return not found")


def main():
    problems = []
    packs = pack_names()
    all_tools = []
    py_files = [p for p in ROOT.rglob("*.py") if ".git" not in p.parts and "__pycache__" not in p.parts]
    for p in py_files:
        text = p.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), 1):
            if line.rstrip() != line:
                problems.append(f"TRAILING WHITESPACE {p}:{line_no}")
            if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.I) and p.name != "audit.py":
                problems.append(f"DEAD/WORK NOTE {p}:{line_no}")
        if p.name != "audit.py" and re.search(r"shell\s*=\s*True|os\.system\(", text):
            problems.append(f"UNSAFE EXECUTION PATTERN {p}")
    for p in py_files:
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except Exception as e:
            problems.append(f"SYNTAX {p}: {e}")
    for pack in packs:
        try:
            tools = source_tools(pack)
        except Exception as e:
            problems.append(f"REGISTRATION {pack}: {e}")
            continue
        all_tools += [(pack, t) for t in tools]
        zp = ROOT / "plugins" / f"{pack}.zip"
        if not zp.exists():
            problems.append(f"MISSING ZIP {zp}")
            continue
        try:
            with zipfile.ZipFile(zp) as z:
                names = set(z.namelist())
                expected = {
                    f"{pack}/{p.relative_to(ROOT/pack).as_posix()}"
                    for p in (ROOT / pack).rglob("*.py")
                    if "__pycache__" not in p.parts
                }
                if not expected <= names:
                    problems.append(f"ZIP MISMATCH {pack}: missing {sorted(expected-names)}")
                if any("__pycache__" in n or n.endswith(".pyc") for n in names):
                    problems.append(f"ZIP CACHE {pack}")
        except Exception as e:
            problems.append(f"ZIP INVALID {pack}: {e}")
    names = [t.get("name", "").strip().casefold() for _, t in all_tools]
    descs = [t.get("description", "").strip().casefold() for _, t in all_tools]
    if len(set(names)) != len(names):
        problems.append("Duplicate tool names")
    if len(set(descs)) < len(descs) * 0.70:
        problems.append("Too many repeated descriptions; catalogue needs differentiation")
    for pack, t in all_tools:
        deps = t.get("dependencies", []) or []
        if any(not isinstance(d, str) or not d.strip() for d in deps):
            problems.append(f'Invalid dependency metadata: {pack}/{t.get("name")}')
        handler = t.get("handler", "")
        if handler.startswith("operations.") and not (ROOT / pack / "operations.py").exists():
            problems.append(f"Missing shared operations module: {pack}")
    cmds = [t.get("cli_command") for _, t in all_tools]
    if len(all_tools) > 500:
        problems.append(f"TOOL LIMIT EXCEEDED: {len(all_tools)} > 500")
    if len(all_tools) != 500:
        problems.append(f"EXPECTED 500 TOOLS, FOUND {len(all_tools)}")
    if len(set(cmds)) != len(cmds):
        problems.append("Duplicate CLI commands")
    for pack, t in all_tools:
        for key in ("name", "category", "description", "handler", "cli_command"):
            if not t.get(key):
                problems.append(f'MISSING {key}: {pack}/{t.get("name",t)}')
        handler = t["handler"]
        mod, fn = handler.rsplit(".", 1)
        fp = ROOT / pack / f"{mod}.py"
        if not fp.exists():
            problems.append(f"Missing handler file: {pack}/{handler}")
            continue
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
            defined = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            dynamic = False
            for node in tree.body:
                if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "_HANDLERS" for t in node.targets
                ):
                    try:
                        mapping = ast.literal_eval(node.value)
                        dynamic = fn in mapping
                    except Exception:
                        dynamic = False
            if fn not in defined and not dynamic:
                problems.append(f"Missing handler function: {pack}/{handler}")
        except Exception as e:
            problems.append(f"AST handler error: {pack}/{handler}: {e}")
    # source-tree cache clutter
    if list(ROOT.rglob("__pycache__")):
        problems.append("Build tree contains __pycache__")
    print(f"Packs: {len(packs)}")
    print(f"Tools: {len(all_tools)}/500")
    print(f"Unique commands: {len(set(cmds))}/{len(cmds)}")
    print(f"Python files audited: {len(py_files)}")
    try:
        from .tool_registry import ToolRegistry
    except Exception:
        from core.tool_registry import ToolRegistry
    resolved = 0
    for pack, t in all_tools:
        try:
            ToolRegistry._resolve_handler({**t, "pack": pack})
            resolved += 1
        except Exception as e:
            problems.append(f'RUNTIME HANDLER {pack}/{t.get("handler")}: {e}')
    print(f"Runtime handlers resolved: {resolved}/{len(all_tools)}")
    if problems:
        print("\nAUDIT FAILED")
        for p in problems:
            print(" -", p)
        return 1
    print("AUDIT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
