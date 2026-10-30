"""Developer — regex, diffs, code statistics and git."""

from __future__ import annotations

import difflib
import json
import os
import re
import shutil
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import (human_size, iter_files, need_dir, need_file, out_path,
                    read_text, report_table, run_command, write_text, which)

CODE_EXTENSIONS = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".jsx": "React",
    ".tsx": "React TS", ".java": "Java", ".c": "C", ".h": "C header", ".cpp": "C++",
    ".cs": "C#", ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".sql": "SQL", ".sh": "Shell",
    ".ps1": "PowerShell", ".bat": "Batch", ".md": "Markdown", ".json": "JSON",
    ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML", ".xml": "XML", ".kt": "Kotlin",
    ".swift": "Swift", ".dart": "Dart", ".lua": "Lua", ".r": "R", ".vue": "Vue",
}


@tool(id="regex-tester", name="Regex Tester", category="Developer",
      summary="Test a regular expression live: matches, groups, positions and replacements.",
      keywords="regex regular expression test match groups pattern",
      fields=[F.text("pattern", "Pattern", r"\b(\w+)@(\w+)\.com\b", required=True),
              F.multi("text", "Test text", rows=8),
              F.flag("ignore_case", "Ignore case", True),
              F.flag("multiline", "Multiline (^ and $ per line)", True),
              F.text("replacement", "Replacement to preview", r"\2 at \1")])
def regex_tester(v, ctx):
    flags = 0
    if v["ignore_case"]:
        flags |= re.IGNORECASE
    if v["multiline"]:
        flags |= re.MULTILINE
    try:
        compiled = re.compile(v["pattern"], flags)
    except re.error as exc:
        raise ToolError(f"Invalid pattern: {exc}") from exc
    text = v["text"]
    if not text:
        raise ToolError("Paste some text to test against")
    matches = list(compiled.finditer(text))
    if not matches:
        return "No matches."
    rows = []
    for index, match in enumerate(matches[:200], start=1):
        line = text.count("\n", 0, match.start()) + 1
        rows.append({"#": index, "match": match.group()[:50],
                     "line": line, "span": f"{match.start()}–{match.end()}",
                     "groups": " | ".join(g or "" for g in match.groups())[:40]})
    ctx.log(report_table(rows))
    if v["replacement"]:
        ctx.log("")
        ctx.log("With replacement:")
        ctx.log(compiled.sub(v["replacement"], text)[:1500])
    return f"{len(matches)} match(es)"


@tool(id="diff-text", name="Compare Text", category="Developer",
      summary="A unified diff between two blocks of text or two files.",
      keywords="diff compare text changes unified patch",
      fields=[F.file("file_a", "First file", required=False),
              F.file("file_b", "Second file", required=False),
              F.multi("text_a", "…or first text", rows=6),
              F.multi("text_b", "…or second text", rows=6),
              F.integer("context", "Context lines", 3, minimum=0, maximum=20)])
def diff_text(v, ctx):
    def side(path_key: str, text_key: str, label: str) -> list[str]:
        raw = str(v[path_key] or "").strip()
        if raw:
            return read_text(need_file(raw, label)).splitlines()
        return str(v[text_key] or "").splitlines()

    left = side("file_a", "text_a", "First file")
    right = side("file_b", "text_b", "Second file")
    if not left and not right:
        raise ToolError("Give two files, or two blocks of text")
    diff = list(difflib.unified_diff(left, right, fromfile="first", tofile="second",
                                     lineterm="", n=v["context"]))
    if not diff:
        return "The two sides are identical."
    ctx.log("\n".join(diff[:600]))
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    return f"{added} line(s) added, {removed} removed"


@tool(id="code-stats", name="Code Statistics", category="Developer",
      summary="Lines of code per language, with blank and comment line counts.",
      keywords="lines of code loc statistics languages project count",
      fields=[F.folder("folder", "Project folder"),
              F.flag("skip_hidden", "Skip hidden folders and node_modules", True)])
def code_stats(v, ctx):
    skip_dirs = {"node_modules", ".git", "venv", ".venv", "__pycache__", "dist", "build"}
    totals: dict[str, dict] = {}
    for path in iter_files(need_dir(v["folder"]), True):
        if v["skip_hidden"] and any(part in skip_dirs or part.startswith(".")
                                    for part in path.parts):
            continue
        language = CODE_EXTENSIONS.get(path.suffix.lower())
        if not language:
            continue
        try:
            lines = read_text(path).splitlines()
        except OSError:
            continue
        blank = sum(1 for line in lines if not line.strip())
        comment = sum(1 for line in lines
                      if line.strip().startswith(("#", "//", "/*", "*", "--", ";")))
        entry = totals.setdefault(language, {"language": language, "files": 0, "lines": 0,
                                             "code": 0, "comments": 0, "blank": 0})
        entry["files"] += 1
        entry["lines"] += len(lines)
        entry["blank"] += blank
        entry["comments"] += comment
        entry["code"] += len(lines) - blank - comment
        ctx.check_cancel()
    rows = sorted(totals.values(), key=lambda row: row["lines"], reverse=True)
    ctx.log(report_table(rows, ["language", "files", "lines", "code", "comments", "blank"]))
    return {"languages": len(rows), "files": sum(r["files"] for r in rows),
            "lines": sum(r["lines"] for r in rows),
            "code_lines": sum(r["code"] for r in rows)}


@tool(id="todo-scan", name="TODO Scanner", category="Developer",
      summary="Collect every TODO, FIXME, HACK and XXX comment in a project.",
      keywords="todo fixme hack notes comments scan project",
      fields=[F.folder("folder", "Project folder"),
              F.text("tags", "Tags to find", "TODO,FIXME,HACK,XXX,NOTE"),
              F.save("report", "Save CSV to", required=False)])
def todo_scan(v, ctx):
    from ._util import write_csv
    tags = [tag.strip() for tag in v["tags"].split(",") if tag.strip()]
    pattern = re.compile(r"(" + "|".join(re.escape(tag) for tag in tags) + r")[:\s]*(.{0,120})",
                         re.IGNORECASE)
    rows = []
    for path in iter_files(need_dir(v["folder"]), True):
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        try:
            text = read_text(path)
        except OSError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            match = pattern.search(line)
            if match:
                rows.append({"tag": match.group(1).upper(), "line": number,
                             "file": path.name, "note": match.group(2).strip()[:80]})
    if not rows:
        return "No TODO-style comments found."
    ctx.log(report_table(rows[:200], ["tag", "line", "file", "note"]))
    if v["report"].strip():
        target = write_csv(out_path(v["report"], "todos.csv"), rows)
        ctx.output(str(target))
    return f"{len(rows)} note(s) across {len({r['file'] for r in rows})} file(s)"


@tool(id="python-syntax-check", name="Check Python Syntax", category="Developer",
      summary="Compile Python files to find syntax errors, with the exact line.",
      fields=[F.folder("folder", "Folder of Python files", required=False),
              F.file("file", "…or one file", required=False)])
def python_syntax_check(v, ctx):
    paths: list[Path] = []
    if str(v["file"] or "").strip():
        paths = [need_file(v["file"])]
    elif str(v["folder"] or "").strip():
        paths = [p for p in iter_files(need_dir(v["folder"]), True, "*.py")]
    else:
        raise ToolError("Choose a file or a folder")
    if not paths:
        raise ToolError("No Python files found")
    bad = []
    for path in paths:
        ctx.check_cancel()
        try:
            source = read_text(path)
            compile(source, str(path), "exec")
        except SyntaxError as exc:
            bad.append({"file": path.name, "line": exc.lineno or 0,
                        "error": str(exc.msg)[:70]})
            ctx.log(f"✕ {path.name}:{exc.lineno} — {exc.msg}")
        except (OSError, ValueError) as exc:
            bad.append({"file": path.name, "line": 0, "error": str(exc)[:70]})
    if not bad:
        return f"All {len(paths)} file(s) compile cleanly."
    return f"{len(bad)} of {len(paths)} file(s) have problems"


@tool(id="python-import-check", name="Check Python Imports", category="Developer",
      summary="Verify that every import in a Python file can actually be resolved.",
      fields=[F.file("file", "Python file", filters="Python (*.py)")])
def python_import_check(v, ctx):
    import ast
    import importlib.util
    path = need_file(v["file"], "Python file")
    try:
        tree = ast.parse(read_text(path))
    except SyntaxError as exc:
        raise ToolError(f"Syntax error first: line {exc.lineno} — {exc.msg}") from exc
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module.split(".")[0])
    missing = []
    for module in sorted(modules):
        if module in ("__future__",):
            continue
        if importlib.util.find_spec(module) is None:
            missing.append(module)
    ctx.log(f"{len(modules)} import(s): {', '.join(sorted(modules))}")
    if missing:
        ctx.log(f"! not installed: {', '.join(missing)}")
        return {"checked": len(modules), "missing": missing}
    return {"checked": len(modules), "missing": [], "status": "all resolvable"}


@tool(id="python-outline", name="Python File Outline", category="Developer",
      summary="Every class and function in a Python file, with line numbers and docstrings.",
      fields=[F.file("file", "Python file", filters="Python (*.py)")])
def python_outline(v, ctx):
    import ast
    path = need_file(v["file"], "Python file")
    try:
        tree = ast.parse(read_text(path))
    except SyntaxError as exc:
        raise ToolError(f"Syntax error: line {exc.lineno} — {exc.msg}") from exc
    rows = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            rows.append({"kind": "function", "name": node.name, "line": node.lineno,
                         "doc": (ast.get_docstring(node) or "").split("\n")[0][:50]})
        elif isinstance(node, ast.ClassDef):
            rows.append({"kind": "class", "name": node.name, "line": node.lineno,
                         "doc": (ast.get_docstring(node) or "").split("\n")[0][:50]})
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    rows.append({"kind": "  method", "name": child.name, "line": child.lineno,
                                 "doc": (ast.get_docstring(child) or "").split("\n")[0][:40]})
    if not rows:
        return "No top-level functions or classes."
    ctx.log(report_table(rows, ["kind", "name", "line", "doc"]))
    return f"{len(rows)} definition(s) in {path.name}"


@tool(id="html-validate", name="Check HTML Structure", category="Developer",
      summary="Find unclosed, mismatched and deprecated tags in an HTML file.",
      fields=[F.file("file", "HTML file", filters="HTML (*.html *.htm)")])
def html_validate(v, ctx):
    path = need_file(v["file"], "HTML file")
    text = read_text(path)
    void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
            "meta", "param", "source", "track", "wbr", "!doctype"}
    stack: list[tuple[str, int]] = []
    problems: list[dict] = []
    for match in re.finditer(r"<(/?)([a-zA-Z!][\w!-]*)([^>]*)>", text):
        closing, tag, rest = match.group(1), match.group(2).lower(), match.group(3)
        line = text.count("\n", 0, match.start()) + 1
        if tag in void or rest.rstrip().endswith("/"):
            continue
        if closing:
            if not stack:
                problems.append({"line": line, "problem": f"stray </{tag}>"})
            elif stack[-1][0] == tag:
                stack.pop()
            else:
                problems.append({"line": line,
                                 "problem": f"</{tag}> closes <{stack[-1][0]}> from line {stack[-1][1]}"})
                if any(open_tag == tag for open_tag, _ in stack):
                    while stack and stack[-1][0] != tag:
                        stack.pop()
                    if stack:
                        stack.pop()
        else:
            stack.append((tag, line))
    for tag, line in stack:
        problems.append({"line": line, "problem": f"<{tag}> never closed"})
    if not problems:
        return f"{path.name} looks structurally sound."
    ctx.log(report_table(problems[:60], ["line", "problem"]))
    return f"{len(problems)} structural problem(s)"


@tool(id="minify", name="Minify CSS / JS / HTML", category="Developer",
      summary="Strip comments and whitespace from CSS, JavaScript or HTML to shrink it.",
      fields=[F.file("file", "Source file", filters="Web (*.css *.js *.html *.htm)"),
              F.choice("kind", "Language", ["Auto-detect", "CSS", "JavaScript", "HTML"],
                       "Auto-detect"),
              F.save("output", "Save minified as", required=True)])
def minify(v, ctx):
    path = need_file(v["file"])
    text = read_text(path)
    kind = v["kind"]
    if kind == "Auto-detect":
        kind = {"css": "CSS", "js": "JavaScript"}.get(path.suffix.lower().lstrip("."), "HTML")
    if kind == "CSS":
        out = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        out = re.sub(r"\s+", " ", out)
        out = re.sub(r"\s*([{}:;,>])\s*", r"\1", out)
    elif kind == "JavaScript":
        out = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        out = re.sub(r"(?m)^\s*//.*$", "", out)
        out = re.sub(r"\n\s*\n+", "\n", out)
        out = re.sub(r"[ \t]{2,}", " ", out)
    else:
        out = re.sub(r"<!--(?!\[if).*?-->", "", text, flags=re.S)
        out = re.sub(r">\s+<", "><", out)
        out = re.sub(r"\s{2,}", " ", out)
    out = out.strip()
    target = write_text(out_path(v["output"], path.stem + ".min" + path.suffix), out)
    ctx.output(str(target))
    before, after = len(text), len(out)
    return (f"{path.name}: {human_size(before)} → {human_size(after)} "
            f"({(1 - after / max(before, 1)) * 100:.0f}% smaller)")


@tool(id="sql-format", name="Format SQL", category="Developer",
      summary="Put a SQL query back into readable lines with keywords upper-cased.",
      fields=[F.multi("text", "SQL", rows=8),
              F.file("file", "…or read a .sql file", required=False),
              F.flag("uppercase", "Upper-case keywords", True)])
def sql_format(v, ctx):
    path = str(v["file"] or "").strip()
    text = read_text(need_file(path)) if path else v["text"]
    if not text.strip():
        raise ToolError("Paste some SQL, or choose a file")
    keywords = ["SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT",
                "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "JOIN", "ON",
                "UNION ALL", "UNION", "INSERT INTO", "VALUES", "UPDATE", "SET",
                "DELETE FROM", "CREATE TABLE", "ALTER TABLE", "DROP TABLE", "WITH"]
    out = re.sub(r"\s+", " ", text.strip())
    for keyword in sorted(keywords, key=len, reverse=True):
        pattern = r"\b" + keyword.replace(" ", r"\s+") + r"\b"
        out = re.sub(pattern, "\n" + keyword, out, flags=re.IGNORECASE)
    out = re.sub(r",\s*", ",\n  ", out)
    if v["uppercase"]:
        for keyword in sorted(keywords, key=len, reverse=True):
            out = re.sub(r"\b" + keyword + r"\b", keyword, out)
    out = "\n".join(line.strip() for line in out.splitlines() if line.strip())
    ctx.log(out)
    return f"{len(out.splitlines())} line(s)"


@tool(id="markdown-lint", name="Markdown Check", category="Developer",
      summary="Spot broken links, skipped heading levels, long lines and stray HTML.",
      fields=[F.file("file", "Markdown file", filters="Markdown (*.md *.markdown)")])
def markdown_lint(v, ctx):
    path = need_file(v["file"], "Markdown file")
    text = read_text(path)
    problems = []
    lines = text.splitlines()
    previous_level = 0
    for number, line in enumerate(lines, start=1):
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if previous_level and level > previous_level + 1:
                problems.append({"line": number, "problem": f"heading jumps from h{previous_level} to h{level}"})
            previous_level = level
        if len(line) > 120:
            problems.append({"line": number, "problem": f"line is {len(line)} characters"})
        for target in re.findall(r"\]\(([^)]+)\)", line):
            if target.startswith(("http", "#", "mailto:")):
                continue
            if not (path.parent / target.split("#")[0]).exists():
                problems.append({"line": number, "problem": f"missing link target: {target}"})
        if re.search(r"<(?!/?(br|hr|img|details|summary|div|p|sup|sub)\b)[a-z]+", line):
            problems.append({"line": number, "problem": "raw HTML tag"})
    if not problems:
        return f"{path.name}: no problems found."
    ctx.log(report_table(problems[:80], ["line", "problem"]))
    return f"{len(problems)} issue(s)"


@tool(id="semver", name="Compare or Bump Versions", category="Developer",
      summary="Compare two semantic versions, or bump one by major, minor or patch.",
      fields=[F.text("version", "Version", "1.4.2", required=True),
              F.choice("action", "Action", ["Compare", "Bump"], "Compare"),
              F.text("other", "Other version", "1.5.0"),
              F.choice("bump", "Bump", ["major", "minor", "patch"], "patch")])
def semver(v, ctx):
    pattern = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([\w.]+))?$")
    def parse(text: str) -> tuple[int, int, int, str]:
        match = pattern.match(text.strip())
        if not match:
            raise ToolError(f"{text!r} is not a semantic version like 1.4.2")
        return int(match.group(1)), int(match.group(2)), int(match.group(3)), match.group(4) or ""
    current = parse(v["version"])
    if v["action"] == "Compare":
        if not v["other"].strip():
            raise ToolError("Give a second version to compare with")
        other = parse(v["other"])
        if current[:3] == other[:3]:
            verdict = "equal"
        else:
            verdict = "higher" if current[:3] > other[:3] else "lower"
        return {"version": v["version"], "other": v["other"], "result": verdict,
                "difference": "same" if verdict == "equal" else verdict}
    major, minor, patch, _ = current
    if v["bump"] == "major":
        bumped = f"{major + 1}.0.0"
    elif v["bump"] == "minor":
        bumped = f"{major}.{minor + 1}.0"
    else:
        bumped = f"{major}.{minor}.{patch + 1}"
    return {"from": v["version"], "to": bumped, "bump": v["bump"]}


@tool(id="cron-explain", name="Explain a Cron Expression", category="Developer",
      summary="Turn a cron schedule into plain English, with the next few run times.",
      fields=[F.text("expression", "Cron expression", "0 9 * * 1-5", required=True)])
def cron_explain(v, ctx):
    parts = v["expression"].split()
    if len(parts) != 5:
        raise ToolError("A cron expression has five fields: minute hour day month weekday")
    minute, hour, day, month, weekday = parts
    names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    bits = []
    bits.append("every minute" if minute == "*" else
                f"at minute {minute}" if "," not in minute and "-" not in minute and "/" not in minute
                else f"at minutes {minute}")
    bits.append("of every hour" if hour == "*" else
                f"of hour {hour}" if "," not in hour and "-" not in hour else f"of hours {hour}")
    if day != "*":
        bits.append(f"on day {day} of the month")
    if month != "*":
        bits.append(f"in month {month}")
    if weekday != "*":
        if weekday == "1-5":
            bits.append("on weekdays")
        elif weekday == "0,6" or weekday == "6,0":
            bits.append("at weekends")
        elif weekday.isdigit():
            bits.append(f"on {names[int(weekday) % 7]}")
        else:
            bits.append(f"on weekday field {weekday}")
    sentence = "Runs " + " ".join(bits) + "."
    ctx.log(sentence)
    try:
        from datetime import datetime, timedelta
        runs = []
        moment = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1)
        def matches(when: datetime) -> bool:
            def field_ok(spec: str, value: int, names_list=None) -> bool:
                if spec == "*":
                    return True
                for chunk in spec.split(","):
                    if "-" in chunk:
                        low, _, high = chunk.partition("-")
                        if int(low) <= value <= int(high):
                            return True
                    elif chunk.isdigit() and int(chunk) == value:
                        return True
                return False
            return (field_ok(minute, when.minute) and field_ok(hour, when.hour)
                    and field_ok(day, when.day) and field_ok(month, when.month)
                    and field_ok(weekday, (when.weekday() + 1) % 7))
        for _ in range(20000):
            if len(runs) >= 5:
                break
            if matches(moment):
                runs.append(moment.strftime("%Y-%m-%d %H:%M"))
            moment += timedelta(minutes=1)
        if runs:
            ctx.log("Next runs:")
            for run in runs:
                ctx.log(f"  {run}")
    except Exception:  # noqa: BLE001 - the explanation is the important part
        pass
    return sentence


@tool(id="git-status", name="Git Status", category="Developer",
      summary="Working tree state of a repository: branch, changes and sync position.",
      needs=("git",),
      fields=[F.folder("folder", "Repository folder")])
def git_status(v, ctx):
    root = need_dir(v["folder"])
    code, out, err = run_command(["git", "-C", str(root), "status", "--short", "--branch"],
                                 ctx=ctx, timeout=60)
    if code != 0:
        raise ToolError(f"Not a git repository, or git failed: {err.strip()[:200]}")
    lines = [line for line in out.splitlines() if line.strip()]
    return {"branch_line": lines[0] if lines else "",
            "changed_files": len(lines) - 1,
            "details": lines[1:40]}


@tool(id="git-log", name="Git Log", category="Developer",
      summary="Recent commits with author, date and message, as a table or a changelog.",
      needs=("git",),
      fields=[F.folder("folder", "Repository folder"),
              F.integer("count", "Commits", 20, minimum=1, maximum=500),
              F.choice("format", "Format", ["Table", "Changelog", "One line per commit"], "Table")])
def git_log(v, ctx):
    root = need_dir(v["folder"])
    code, out, err = run_command(["git", "-C", str(root), "log", f"-{v['count']}",
                                  "--date=short",
                                  "--pretty=format:%h|%an|%ad|%s"], timeout=120)
    if code != 0:
        raise ToolError(f"git log failed: {err.strip()[:200]}")
    commits = [line.split("|", 3) for line in out.splitlines() if "|" in line]
    if v["format"] == "Changelog":
        text = "\n".join(f"- {parts[3]} ({parts[0]}, {parts[2]})" for parts in commits)
        ctx.log(text)
        return f"{len(commits)} commit(s) formatted as a changelog"
    if v["format"] == "One line per commit":
        ctx.log("\n".join(f"{parts[0]} {parts[3]}" for parts in commits))
        return f"{len(commits)} commit(s)"
    rows = [{"hash": parts[0], "author": parts[1], "date": parts[2], "message": parts[3][:60]}
            for parts in commits]
    ctx.log(report_table(rows, ["hash", "date", "author", "message"]))
    return f"{len(commits)} commit(s)"


@tool(id="git-branches", name="Git Branches", category="Developer",
      summary="Local and remote branches, with the current one marked.",
      needs=("git",),
      fields=[F.folder("folder", "Repository folder"),
              F.flag("merged_only", "Only branches merged into the current one", False)])
def git_branches(v, ctx):
    root = need_dir(v["folder"])
    args = ["git", "-C", str(root), "branch", "-a", "--sort=-committerdate"]
    if v["merged_only"]:
        args.append("--merged")
    code, out, err = run_command(args, timeout=60)
    if code != 0:
        raise ToolError(f"git branch failed: {err.strip()[:200]}")
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    for line in lines[:100]:
        ctx.log(line)
    return f"{len(lines)} branch(es)"


@tool(id="git-diff", name="Git Diff", category="Developer",
      summary="Uncommitted changes in a repository, with a per-file summary.",
      needs=("git",),
      fields=[F.folder("folder", "Repository folder"),
              F.flag("staged", "Show staged changes instead", False),
              F.flag("stat_only", "Summary only", True)])
def git_diff(v, ctx):
    root = need_dir(v["folder"])
    args = ["git", "-C", str(root), "diff"]
    if v["staged"]:
        args.append("--cached")
    if v["stat_only"]:
        args.append("--stat")
    code, out, err = run_command(args, timeout=120)
    if code != 0:
        raise ToolError(f"git diff failed: {err.strip()[:200]}")
    if not out.strip():
        return "No changes."
    ctx.log(out[:4000])
    return f"{len(out.splitlines())} line(s) of diff"


@tool(id="env-file", name="Check a .env File", category="Developer",
      summary="Parse a .env file, show its keys and flag empty or duplicated values.",
      fields=[F.file("file", ".env file", filters="All files (*)")])
def env_file(v, ctx):
    path = need_file(v["file"])
    rows = []
    seen: dict[str, int] = {}
    for number, line in enumerate(read_text(path).splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            rows.append({"line": number, "key": stripped[:30], "issue": "no = sign"})
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        seen[key] = seen.get(key, 0) + 1
        issue = ""
        if not value.strip():
            issue = "empty value"
        elif seen[key] > 1:
            issue = "duplicate key"
        elif any(ch.isupper() for ch in key) is False and key != key.lower():
            issue = "mixed case"
        rows.append({"line": number, "key": key, "issue": issue})
    ctx.log(report_table(rows[:120], ["line", "key", "issue"]))
    problems = sum(1 for row in rows if row["issue"])
    return f"{len(rows)} key(s), {problems} worth checking"


@tool(id="requirements-check", name="Check requirements.txt", category="Developer",
      summary="Which packages in a requirements file are installed, missing or outdated.",
      fields=[F.file("file", "requirements.txt", filters="Text (*.txt)")])
def requirements_check(v, ctx):
    import importlib.metadata as metadata
    path = need_file(v["file"])
    rows = []
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "-")):
            continue
        match = re.match(r"([A-Za-z0-9_.\-]+)\s*(.*)", stripped)
        if not match:
            continue
        name, spec = match.group(1), match.group(2)
        try:
            installed = metadata.version(name)
            status = "installed"
        except metadata.PackageNotFoundError:
            installed = ""
            status = "MISSING"
        rows.append({"package": name, "required": spec or "any",
                     "installed": installed, "status": status})
    if not rows:
        return "No packages listed in that file."
    ctx.log(report_table(rows, ["package", "required", "installed", "status"]))
    missing = sum(1 for row in rows if row["status"] == "MISSING")
    return f"{len(rows)} package(s), {missing} missing"


@tool(id="colour-convert", name="Convert Colours", category="Developer",
      summary="Convert between HEX, RGB, HSL and CMYK, with the WCAG contrast ratio.",
      fields=[F.color("colour", "Colour", "#3b82f6"),
              F.color("against", "Contrast against", "#ffffff")])
def colour_convert(v, ctx):
    def to_rgb(text: str) -> tuple[int, int, int]:
        value = text.strip().lstrip("#")
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        if len(value) != 6:
            raise ToolError(f"{text!r} is not a hex colour")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))

    rgb = to_rgb(v["colour"])
    other = to_rgb(v["against"])
    r, g, b = (channel / 255 for channel in rgb)
    high, low = max(r, g, b), min(r, g, b)
    lightness = (high + low) / 2
    if high == low:
        hue = saturation = 0.0
    else:
        delta = high - low
        saturation = delta / (2 - high - low) if lightness > 0.5 else delta / (high + low)
        if high == r:
            hue = ((g - b) / delta) % 6
        elif high == g:
            hue = (b - r) / delta + 2
        else:
            hue = (r - g) / delta + 4
        hue *= 60

    def luminance(colour: tuple[int, int, int]) -> float:
        channels = []
        for value in colour:
            scaled = value / 255
            channels.append(scaled / 12.92 if scaled <= 0.03928
                            else ((scaled + 0.055) / 1.055) ** 2.4)
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    first, second = luminance(rgb), luminance(other)
    ratio = (max(first, second) + 0.05) / (min(first, second) + 0.05)
    c, m, y = (1 - channel / 255 for channel in rgb)
    black = 1 - max(c, m, y)
    result = {
        "hex": "#%02x%02x%02x" % rgb,
        "rgb": f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})",
        "hsl": f"hsl({hue:.0f}, {saturation * 100:.0f}%, {lightness * 100:.0f}%)",
        "cmyk": f"{c * 100:.0f}%, {m * 100:.0f}%, {y * 100:.0f}%, {black * 100:.0f}%",
        "contrast_ratio": f"{ratio:.2f}:1",
        "wcag_normal_text": "AA pass" if ratio >= 4.5 else "AA fail",
        "wcag_large_text": "AA pass" if ratio >= 3 else "AA fail",
    }
    ctx.log(report_table([{"format": k, "value": str(val)} for k, val in result.items()]))
    return result


@tool(id="line-length-report", name="Long Line Report", category="Developer",
      summary="Files and lines that exceed a width limit — for style clean-up.",
      fields=[F.folder("folder", "Project folder"),
              F.integer("max_length", "Maximum line length", 100, minimum=20, maximum=500),
              F.text("pattern", "Only files matching", "*.py"),
              F.flag("recursive", "Include subfolders", True)])
def line_length_report(v, ctx):
    root = need_dir(v["folder"])
    offenders = []
    total = 0
    for path in iter_files(root, v["recursive"], v["pattern"] or "*"):
        try:
            text = read_text(path)
        except OSError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            total += 1
            if len(line) > v["max_length"]:
                offenders.append({"file": path.name, "line": number,
                                  "length": len(line), "text": line[:60]})
    if not offenders:
        return f"No line over {v['max_length']} characters in {total} line(s)."
    offenders.sort(key=lambda row: row["length"], reverse=True)
    ctx.log(report_table(offenders[:80], ["length", "file", "line", "text"]))
    return f"{len(offenders)} line(s) over {v['max_length']} characters"


@tool(id="encoding-detect", name="Detect File Encoding", category="Developer",
      summary="Work out whether a file is UTF-8, UTF-16, Windows-1252 or Latin-1, and if it has a BOM.",
      fields=[F.file("file", "File")])
def encoding_detect(v, ctx):
    path = need_file(v["file"])
    raw = path.read_bytes()[:65536]
    bom = None
    for marker, name in ((b"\xef\xbb\xbf", "UTF-8 BOM"), (b"\xff\xfe", "UTF-16 LE BOM"),
                         (b"\xfe\xff", "UTF-16 BE BOM")):
        if raw.startswith(marker):
            bom = name
            break
    detected = ""
    for candidate in ("utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            raw.decode(candidate)
            detected = candidate
            break
        except UnicodeDecodeError:
            continue
    high_bytes = sum(1 for byte in raw if byte > 127)
    newlines = {"CRLF": raw.count(b"\r\n"), "LF": raw.count(b"\n") - raw.count(b"\r\n")}
    return {"file": path.name, "byte_order_mark": bom or "none",
            "likely_encoding": detected or "binary",
            "non_ascii_bytes": high_bytes,
            "line_endings": {k: val for k, val in newlines.items() if val},
            "binary": high_bytes > len(raw) * 0.3}


@tool(id="indentation-report", name="Indentation Report", category="Developer",
      summary="Tabs or spaces, how wide, and whether a file is internally consistent.",
      fields=[F.folder("folder", "Folder"),
              F.text("pattern", "Only files matching", "*.py"),
              F.flag("recursive", "Include subfolders", True)])
def indentation_report(v, ctx):
    root = need_dir(v["folder"])
    rows = []
    for path in iter_files(root, v["recursive"], v["pattern"] or "*"):
        try:
            lines = read_text(path).splitlines()
        except OSError:
            continue
        tabs = sum(1 for line in lines if line.startswith("\t"))
        spaces = sum(1 for line in lines if line.startswith(" "))
        widths = {len(line) - len(line.lstrip(" ")) for line in lines if line.startswith(" ")}
        step = min((w for w in widths if w), default=0)
        style = "tabs" if tabs > spaces else "spaces" if spaces else "none"
        mixed = tabs > 0 and spaces > 0
        rows.append({"file": path.name, "style": style, "indent": step or "",
                     "mixed": "MIXED" if mixed else ""})
    if not rows:
        return "No matching files."
    ctx.log(report_table(rows[:100], ["file", "style", "indent", "mixed"]))
    mixed = sum(1 for row in rows if row["mixed"])
    return f"{len(rows)} file(s), {mixed} mixing tabs and spaces"
