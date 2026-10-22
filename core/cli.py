"""Command-line entry point."""

from __future__ import annotations

import argparse
import logging
import sys

from . import __version__
from .config import get_plugins_dir
from .plugin_loader import PluginLoader
from .preview import open_with_default, preview_file
from .tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


def build_registry() -> ToolRegistry:
    """Build the tool registry by merging every tool source that is present.

    Precedence (highest first):
      1. External ``plugins/`` directory — an optional override.  A pack placed
         here replaces the built-in copy of the same pack (all 45 packs are
         already embedded in the executable; this directory exists so a
         developer or power user can drop in a replacement).  It is loaded
         first so its tools win the first-registration dedup below.
      2. Embedded single-file bundle (``bundle/tools.dat``) — the baseline that
         ships inside released builds; only its commands that an external pack
         has not already provided are added.
      3. Source-tree packages (dev checkout) — fallback, used only when neither
         of the above produced any tools.

    Which packs are *enabled* is a separate, durable user preference applied by
    :class:`~core.tool_registry.ToolRegistry` (see :mod:`core.preferences`).
    """
    from .bundle import BundleLoader, get_bundle_path

    merged: list[dict] = []
    seen: set[str] = set()

    # 1. External plugins/ first: a replacement pack must win the dedup so that
    #    dropping one in genuinely replaces the built-in copy.
    plugins_dir = get_plugins_dir()
    loader = PluginLoader(plugins_dir)
    external_tools = loader.get_tools()
    if loader.errors:
        logger.warning(
            "Plugin load failed for %d pack(s) in %s: %s",
            len(loader.errors),
            plugins_dir,
            "; ".join(loader.errors),
        )
    external_added = 0
    for tool in external_tools:
        cmd = str(tool.get("cli_command", "")).strip()
        if cmd and cmd not in seen:
            seen.add(cmd)
            merged.append(tool)
            external_added += 1

    # 2. Embedded bundle is the baseline: add only the commands not already
    #    registered by an external pack (first registration wins).
    bundle = get_bundle_path()
    bundle_added = 0
    if bundle is not None:
        for tool in BundleLoader(bundle).get_tools():
            cmd = str(tool.get("cli_command", "")).strip()
            if cmd and cmd not in seen:
                seen.add(cmd)
                merged.append(tool)
                bundle_added += 1

    # Observable merge: say nothing when there was nothing to merge.
    if external_added or bundle_added:
        logger.info(
            "Registry merge: %d tool(s) from plugins/ (%s), %d tool(s) from embedded bundle",
            external_added,
            plugins_dir,
            bundle_added,
        )

    if merged:
        return ToolRegistry(merged)

    # 3. Final fallback: import packs straight from the source tree (dev only).
    from pathlib import Path as _P

    root = _P(__file__).resolve().parent.parent
    src_tools: list[dict] = []
    seen: set[str] = set()
    for pack in sorted(
        p.name
        for p in root.iterdir()
        if p.is_dir()
        and (p / "__init__.py").exists()
        and p.name not in {"core", "tests", "backup", "bundle", "dist", "build", "logs", "scripts", "plugins"}
    ):
        try:
            module = __import__(pack)
            entries = module.register_tools()
        except Exception:
            continue
        for entry in entries:
            cmd = str(entry.get("cli_command", "")).strip()
            if cmd and cmd not in seen:
                seen.add(cmd)
                tool = dict(entry)
                tool["pack"] = pack
                src_tools.append(tool)
    return ToolRegistry(src_tools)


def _launch_gui(registry: ToolRegistry) -> int:
    """Start the desktop GUI, degrading to a clear message instead of a raw
    traceback if tkinter isn't installed or no display is available."""
    try:
        from .gui import UtilitySuiteGUI
    except ImportError:
        print("The GUI requires tkinter, which was not found in this Python installation.")
        print("On Windows, tkinter is bundled with the official python.org installer.")
        print("On Linux, install it via your package manager, e.g. 'sudo apt install python3-tk'.")
        print("The CLI remains fully usable: try 'utility_suite list' or 'utility_suite run <tool>'.")
        return 1
    try:
        UtilitySuiteGUI(registry, on_refresh=build_registry).mainloop()
        return 0
    except Exception as exc:  # e.g. tk.TclError: no display name (headless/SSH session)
        print(f"Could not start the GUI: {exc}")
        print("The CLI remains fully usable: try 'utility_suite list' or 'utility_suite run <tool>'.")
        return 1


def _cmd_list(registry: ToolRegistry, category: str | None) -> int:
    groups = registry.list_categories()
    for name, tools in groups.items():
        if category and name.lower() != category.lower():
            continue
        print(f"\n[{name}]")
        for tool in tools:
            state = "AVAILABLE" if tool["available"] else f"UNAVAILABLE: {', '.join(tool['missing_dependencies'])}"
            print(f"  {tool['cli_command']:18} {tool['name']:<30} [{state}]")
    total = len(registry.enabled_tools())
    hidden = len(registry.tools) - total
    print(f"\nTotal tools: {total}")
    if hidden:
        print(f"({hidden} hidden — their packs are disabled; see 'utility_suite packs')")
    return 0


def _cmd_search(registry: ToolRegistry, query: str) -> int:
    for tool in registry.search(query):
        state = "AVAILABLE" if tool["available"] else "UNAVAILABLE"
        print(f"{tool['cli_command']:18} {tool['name']:<30} [{state}]\n  {tool['description']}")
    return 0


def _cmd_packs(registry: ToolRegistry, action: str, name: str | None) -> int:
    if action == "list":
        summaries = registry.pack_summaries()
        if not summaries:
            print("No packs found.")
            return 0
        for s in summaries:
            mark = "enabled " if s["enabled"] else "disabled"
            print(f"  [{mark}] {s['name']:<28} {s['title']:<28} {s['tool_count']:>3} tools, {s['runnable']:>3} runnable")
        enabled = sum(1 for s in summaries if s["enabled"])
        print(f"\n{enabled}/{len(summaries)} packs enabled.")
        return 0
    if action == "reset":
        registry.preferences.reset()
        print("All packs enabled.")
        return 0
    if action in {"enable", "disable"}:
        if not name:
            print(f"Usage: utility_suite packs {action} <pack>")
            return 2
        if name not in registry.all_packs():
            print(f"Unknown pack '{name}'. Run 'utility_suite packs' to list them.")
            return 2
        enabled = action == "enable"
        registry.set_pack_enabled(name, enabled)
        print(f"Pack '{name}' {'enabled' if enabled else 'disabled'}.")
        return 0
    print(f"Unknown packs action '{action}'.")
    return 2


def _cmd_deps(registry: ToolRegistry, only: str | None) -> int:
    from . import dependencies as deps

    if only:
        plan = deps.install_plan(only)
        if not plan["known"]:
            print(f"Unknown dependency '{only}'. Run 'utility_suite deps' to list them all.")
            return 2
        print(f"{plan['dependency']}  ({plan['kind']})")
        print(f"  What it is : {plan['summary']}")
        print(f"  Why needed : {plan['why']}")
        used = deps.packs_using(only, registry.tools.values())
        if used:
            print(f"  Used by    : {', '.join(used)}")
        print(f"  Installed  : {'yes' if plan['installed'] else 'no'}")
        for step in plan["steps"]:
            head = step["label"]
            if step["command"] and step["command"] != head:
                head = f"{head}    $ {step['command']}"
            print(f"  - {head}")
            if step["url"]:
                print(f"      {step['url']}")
            if step["note"]:
                print(f"      {step['note']}")
        return 0

    missing = deps.missing_dependencies(registry.enabled_tools())
    if not missing:
        print("Nothing is missing — every tool in your enabled packs is ready.")
        return 0
    print("Missing dependencies (install them, then re-run; tools unlock automatically):\n")
    for dep, count in sorted(missing.items(), key=lambda kv: (-kv[1], kv[0].lower())):
        plan = deps.install_plan(dep)
        packs = deps.packs_using(dep, registry.tools.values())
        print(f"  {dep}  ({count} tool{'s' if count != 1 else ''}; packs: {', '.join(packs) or '—'})")
        first = plan["steps"][0] if plan["steps"] else None
        if first:
            if first["command"]:
                print(f"      -> {first['command']}")
            elif first["url"]:
                print(f"      -> {first['url']}")
            else:
                print(f"      -> {first['label']}")
        print(f"      detail: utility_suite deps {dep}")
    print("\nPrefer not to install? Disable that pack instead: utility_suite packs disable <pack>")
    return 0


def main(argv: list[str] | None = None) -> int:
    # Everything from "run <tool>" onward belongs to the tool, including flags
    # like --help/-h/--version — split it out before argparse sees it so those
    # flags are forwarded to the tool instead of being consumed by the suite.
    raw = list(sys.argv[1:] if argv is None else argv)
    tool_remainder: list[str] = []
    for i, tok in enumerate(raw):
        if tok == "run" and i + 1 < len(raw) and not raw[i + 1].startswith("-"):
            tool_name, tool_remainder = raw[i + 1], raw[i + 2:]
            raw = raw[:i + 1] + [tool_name, "--"]
            break

    parser = argparse.ArgumentParser(
        prog="utility_suite", description="Utility Suite — one Windows toolbox, 551 tools in 45 packs"
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")
    p_list = sub.add_parser("list", help="List tools")
    p_list.add_argument("--category")
    p_search = sub.add_parser("search", help="Search tools")
    p_search.add_argument("query")
    p_run = sub.add_parser("run", help="Run a tool (remaining arguments go to the tool)")
    p_run.add_argument("tool_name")
    p_run.add_argument("tool_args", nargs=argparse.REMAINDER)
    sub.add_parser("refresh", help="Rescan plugins")
    p_preview = sub.add_parser("preview", help="Preview a text-like file")
    p_preview.add_argument("file_path")
    p_open = sub.add_parser("open", help="Open using the system default application")
    p_open.add_argument("file_path")
    sub.add_parser("gui", help="Launch desktop GUI")
    p_deps = sub.add_parser("deps", help="List missing dependencies and how to install them")
    p_deps.add_argument("dependency", nargs="?", help="Show the install plan for one dependency")
    p_packs = sub.add_parser("packs", help="Enable/disable tool packs")
    p_packs.add_argument("action", nargs="?", default="list", choices=["list", "enable", "disable", "reset"])
    p_packs.add_argument("name", nargs="?", help="Pack name for enable/disable")
    args = parser.parse_args(raw)

    registry = build_registry()
    if not args.command:
        return _launch_gui(registry)
    if args.command == "list":
        return _cmd_list(registry, args.category)
    if args.command == "search":
        return _cmd_search(registry, args.query)
    if args.command == "run":
        # tool_remainder holds everything after "run <tool>" verbatim (flags
        # like --help/-h/--version are forwarded to the tool, not consumed).
        forwarded = [t for t in tool_remainder if t != "--"] or list(args.tool_args)
        return registry.run_tool(args.tool_name, forwarded)
    if args.command == "refresh":
        refreshed = build_registry()
        print(f"Loaded {len(refreshed.enabled_tools())} enabled tools.")
        return 0
    if args.command == "preview":
        try:
            print(preview_file(args.file_path))
            return 0
        except Exception as exc:
            print(f"Preview failed: {exc}")
            return 1
    if args.command == "open":
        try:
            open_with_default(args.file_path)
            return 0
        except Exception as exc:
            print(f"Open failed: {exc}")
            return 1
    if args.command == "gui":
        return _launch_gui(registry)
    if args.command == "deps":
        return _cmd_deps(registry, args.dependency)
    if args.command == "packs":
        return _cmd_packs(registry, args.action, args.name)
    return 0
