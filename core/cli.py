"""Command line front-end — same tools, same options, no GUI.

    all4one list                       every tool, grouped by category
    all4one search image               find tools
    all4one show hash-file             the options a tool takes
    all4one run hash-file --file a.txt --algo sha256
    all4one run base64-encode --text "hello" --mode encode
    all4one deps                       what optional extras are installed

Option names come from each tool's own field definitions, so the CLI can never
drift from the UI.
"""

from __future__ import annotations

import argparse
import sys

from . import APP_NAME, __version__, registry
from . import deps as deps_mod
from .runner import execute
from .tool import BOOL, MULTI, Tool


def _print_tool_line(t: Tool) -> None:
    ok, why = registry.is_available(t)
    mark = " " if ok else "!"
    print(f" {mark} {t.id:<32} {t.summary}")


def cmd_list(args: argparse.Namespace) -> int:
    tools = registry.all_tools()
    if args.category:
        wanted = [c for c in registry.CATEGORY_NAMES if c.lower() == args.category.lower()]
        if not wanted:
            print(f"No category {args.category!r}. Try: {', '.join(registry.CATEGORY_NAMES)}")
            return 2
        tools = [t for t in tools if t.category == wanted[0]]
    current = None
    for t in tools:
        if t.category != current:
            current = t.category
            print(f"\n{current.upper()}  —  {registry.blurb(current)}")
        _print_tool_line(t)
    print(f"\n{len(tools)} tools. '!' = needs an optional dependency or Windows.")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    hits = registry.search(" ".join(args.terms), limit=args.limit)
    if not hits:
        print("Nothing matched.")
        return 1
    for t in hits:
        _print_tool_line(t)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    t = registry.get(args.tool)
    if not t:
        print(f"No tool {args.tool!r}. Try '{APP_NAME.lower()} search <word>'.")
        return 2
    ok, why = registry.is_available(t)
    print(f"{t.name}  ({t.id})")
    print(f"  category : {t.category}")
    print(f"  summary  : {t.summary}")
    print(f"  ready    : {'yes' if ok else 'no — ' + why}")
    if t.needs:
        print(f"  needs    : {', '.join(t.needs)}")
    if t.destructive:
        print("  warning  : this tool can delete or overwrite data")
    print("  options  :")
    if not t.fields:
        print("    (none)")
    for f in t.fields:
        req = " (required)" if f.required else ""
        default = f" [default: {f.default}]" if str(f.default) != "" else ""
        print(f"    --{f.key:<16} {f.kind:<9} {f.label}{req}{default}")
        if f.help:
            print(f"      {f.help}")
    print(f"\n  run: {APP_NAME.lower()} run {t.id} " +
          " ".join(f"--{f.key} <{f.kind}>" for f in t.fields if f.required))
    return 0


def cmd_deps(_args: argparse.Namespace) -> int:
    rows = deps_mod.status()
    print("OPTIONAL DEPENDENCIES\n")
    for kind, title in (("python", "Python packages"), ("binary", "External programs")):
        print(f"{title}:")
        for row in rows:
            if row["kind"] != kind:
                continue
            mark = "✓" if row["available"] else "✗"
            print(f"  {mark} {row['label']:<38} {'' if row['available'] else row['hint']}")
        print()
    print("Nothing here is required — each one only unlocks the tools that use it.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    t = registry.get(args.tool)
    if not t:
        print(f"No tool {args.tool!r}.")
        return 2
    values: dict[str, object] = {}
    for f in t.fields:
        raw = getattr(args, f.key, None)
        if raw is not None:
            values[f.key] = raw
    if args.set:
        for pair in args.set:
            if "=" not in pair:
                print(f"--set expects key=value, got {pair!r}")
                return 2
            key, _, val = pair.partition("=")
            values[key.strip()] = val
    result = execute(t, values, sink=print)
    return 0 if result.ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=APP_NAME.lower(),
        description=f"{APP_NAME} {__version__} — one portable utility, every tool on its own page.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run without a command to open the desktop app.",
    )
    p.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    sub = p.add_subparsers(dest="command")

    lp = sub.add_parser("list", help="list every tool")
    lp.add_argument("--category", "-c", default="", help="limit to one category")
    lp.set_defaults(func=cmd_list)

    sp = sub.add_parser("search", help="search tools")
    sp.add_argument("terms", nargs="+")
    sp.add_argument("--limit", type=int, default=25)
    sp.set_defaults(func=cmd_search)

    hp = sub.add_parser("show", help="describe one tool and its options")
    hp.add_argument("tool")
    hp.set_defaults(func=cmd_show)

    dp = sub.add_parser("deps", help="show optional dependency status")
    dp.set_defaults(func=cmd_deps)

    rp = sub.add_parser("run", help="run one tool")
    rp.add_argument("tool")
    rp.add_argument("--set", action="append", metavar="KEY=VALUE",
                    help="pass any option as key=value")
    rp.set_defaults(func=cmd_run)

    gp = sub.add_parser("gui", help="open the desktop app")
    gp.set_defaults(func=lambda a: 0)

    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()

    # `run` takes arbitrary --flags, so its options are injected from the
    # tool's own field list before parsing.
    if argv and argv[0] == "run" and len(argv) > 1:
        tool = registry.get(argv[1])
        if tool:
            run_parser = None
            for action in parser._subparsers._actions:  # type: ignore[attr-defined]
                choices = getattr(action, "choices", None)
                if isinstance(choices, dict) and "run" in choices:
                    run_parser = choices["run"]
            if run_parser is not None:
                for f in tool.fields:
                    if f.kind == BOOL:
                        run_parser.add_argument(f"--{f.key}", action=argparse.BooleanOptionalAction,
                                                default=None, help=f.help or f.label)
                    elif f.kind == MULTI:
                        run_parser.add_argument(f"--{f.key}", default=None,
                                                help=f"{f.help or f.label} (comma separated)")
                    else:
                        run_parser.add_argument(f"--{f.key}", default=None,
                                                type=str if f.kind != "int" else int,
                                                help=f.help or f.label)

    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        return launch_gui()
    return int(args.func(args))


def launch_gui() -> int:
    try:
        from ui.app import run  # noqa: PLC0415
    except ImportError as exc:
        print(f"The desktop UI is not available in this build ({exc}).")
        print(f"Use '{APP_NAME.lower()} list' or '{APP_NAME.lower()} run <tool>' instead.")
        return 1
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
