"""Static release audit for Utility Suite (exit-code contract below).

Run as ``python audit.py`` from the repository root.

Exit-code contract (CI gate - see .github/workflows/build-windows-exe.yml):
    0  -> "AUDIT PASSED" : tree is release-clean and all 500 tools validate.
    1  -> "AUDIT FAILED" : at least one problem listed on stdout; the build
                          /release pipeline MUST treat this as fatal.

The exit code is propagated via ``raise SystemExit(main())`` at the bottom of
this file; ``main()`` returns 1 whenever ``problems`` is non-empty. Do not
wrap or swallow that return value, or CI will silently pass broken releases.

NOTE: this module intentionally reports findings only - it never mutates the
working tree (e.g. it will not delete stray ``__pycache__`` directories), so
operators must clean caches themselves before expecting a PASS.
"""
from __future__ import annotations

import sys

# Set before importing anything else so that merely *running* the audit can
# never litter the source tree with bytecode caches (which its own
# "__pycache__ clutter" check would then flag as a failure).
sys.dont_write_bytecode = True
import ast
import re
import subprocess
import zipfile
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
    """Run every release gate check and report findings on stdout.

    Returns:
        int: 0 if the tree is release-clean ("AUDIT PASSED"), or 1 with each
            problem listed ("AUDIT FAILED"). The caller contract is that this
            return value becomes the process exit code (see module docstring);
            CI relies on non-zero here to block broken builds.
    """
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
    # source-tree cache clutter. Only TRACKED files count: audit.py itself
    # imports the plugin loader at runtime, which drops __pycache__ dirs next
    # to the sources it imports. Including those untracked, gitignored build
    # artifacts made this gate fail spuriously on every plain `python audit.py`
    # run (it could only ever pass under `python -B`). Tracked .pyc files are
    # still caught, and ZIP CACHE / release checks below remain unchanged.
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True
    ).stdout.splitlines()
    if any("__pycache__" in line or line.endswith(".pyc") for line in tracked):
        problems.append("Build tree contains tracked __pycache__/.pyc files")

    # Version-string consistency: VERSION.txt is the single source of
    # truth. This check exists because a stale hardcoded version in
    # core/__init__.py once shipped silently (the built exe reported
    # "2.1.2" when the release was actually "2.1.3") - catch that class
    # of bug here instead of relying on a human to notice.
    version_file = (ROOT / "VERSION.txt")
    if version_file.exists():
        expected_version = version_file.read_text(encoding="utf-8").strip()

        def read_literal(path, pattern):
            """Return the first regex match inside a source file, or None."""
            if not path.exists():
                return None
            m = re.search(pattern, path.read_text(encoding="utf-8"))
            return m.group(1) if m else None

        # Every version literal in the tree must match VERSION.txt. This is
        # deliberately *not* an import-based check: importing core would drop
        # __pycache__ dirs into the source tree mid-run (and audit.py sets
        # sys.dont_write_bytecode for exactly that reason). The one import
        # based check below (handler resolution) was the class of bug that
        # once made this audit self-sabotage.
        checked = {
            "core/__init__.py's __version__": read_literal(
                ROOT / "core" / "__init__.py", r'__version__\s*=\s*"([^"]+)"'
            ),
            'config.json "application.version"': read_literal(
                ROOT / "config.json", r'"version"\s*:\s*"([^"]+)"'
            ),
            "build.spec header": read_literal(
                ROOT / "build.spec", r"# Utility Suite (\d+\.\d+\.\d+)"
            ),
        }
        for label, actual in checked.items():
            if actual != expected_version:
                problems.append(
                    f"VERSION MISMATCH: VERSION.txt says '{expected_version}' but "
                    f"{label} is '{actual}'"
                )
    else:
        problems.append("VERSION.txt is missing")

    # build.spec packaging-layout guard: plugins/ and config.json must
    # never be re-added to Analysis(datas=...) - PyInstaller places
    # `datas` inside _internal/, not beside the executable, which
    # previously caused a built exe to silently report "Total tools: 0"
    # because the app looks for plugins/ as a sibling of the exe
    # (see CHANGELOG.md [2.1.3] for the full story).
    spec_file = ROOT / "build.spec"
    if spec_file.exists():
        spec_text = spec_file.read_text(encoding="utf-8")
        if re.search(r"datas\s*=\s*\[[^\]]*['\"]plugins['\"]", spec_text):
            problems.append(
                "build.spec bundles 'plugins' via Analysis(datas=...) again - this buries it "
                "inside _internal/ where the app can't find it. Copy plugins/ next to the built "
                "exe as a post-build step instead (see BUILD_WINDOWS.ps1)."
            )
    else:
        problems.append("build.spec is missing")

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
    # Propagate main()'s 0/1 verdict as the process exit code so CI
    # (`python audit.py`) fails the build on any AUDIT FAILED finding.
    raise SystemExit(main())
