"""Command-line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path
from . import __version__

from .config import get_config_path, load_config
from .plugin_loader import PluginLoader
from .preview import open_with_default, preview_file
from .tool_registry import ToolRegistry


def build_registry() -> ToolRegistry:
    config = load_config()
    plugins_dir = Path(config.get("plugins_directory", "plugins"))
    if not plugins_dir.is_absolute():
        plugins_dir = get_config_path().parent / plugins_dir
    return ToolRegistry(PluginLoader(plugins_dir).get_tools())


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="utility_suite", description="Utility Suite — modular Windows utility workstation"
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")
    p_list = sub.add_parser("list", help="List tools")
    p_list.add_argument("--category")
    p_search = sub.add_parser("search", help="Search tools")
    p_search.add_argument("query")
    p_run = sub.add_parser("run", help="Run a tool")
    p_run.add_argument("tool_name")
    p_run.add_argument("tool_args", nargs=argparse.REMAINDER)
    sub.add_parser("refresh", help="Rescan plugins")
    p_preview = sub.add_parser("preview", help="Preview a text-like file")
    p_preview.add_argument("file_path")
    p_open = sub.add_parser("open", help="Open using the system default application")
    p_open.add_argument("file_path")
    sub.add_parser("gui", help="Launch desktop GUI")
    args = parser.parse_args(argv)

    registry = build_registry()
    if not args.command:
        return _launch_gui(registry)
    if args.command == "list":
        groups = registry.list_categories()
        for category, tools in groups.items():
            if args.category and category.lower() != args.category.lower():
                continue
            print(f"\n[{category}]")
            for tool in tools:
                state = (
                    "AVAILABLE"
                    if tool["available"]
                    else f"UNAVAILABLE: {', '.join(tool['missing_dependencies'])}"
                )
                print(f"  {tool['cli_command']:18} {tool['name']:<30} [{state}]")
        print(f"\nTotal tools: {len(registry.tools)}")
        return 0
    if args.command == "search":
        for tool in registry.search(args.query):
            state = "AVAILABLE" if tool["available"] else "UNAVAILABLE"
            print(f"{tool['cli_command']:18} {tool['name']:<30} [{state}]\n  {tool['description']}")
        return 0
    if args.command == "run":
        return registry.run_tool(args.tool_name, args.tool_args)
    if args.command == "refresh":
        refreshed = build_registry()
        print(f"Loaded {len(refreshed.tools)} tools from plugins.")
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
    return 0
