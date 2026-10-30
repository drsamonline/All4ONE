"""Release audit — the gate every build must pass.

Checks the catalogue's integrity, the version string everywhere it appears,
repository hygiene and that every tool module imports cleanly. Behavioural
testing lives in ``tests/sweep.py``.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILURES: list[str] = []
NOTES: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        NOTES.append(f"PASS  {message}")
    else:
        FAILURES.append(message)


def audit_catalogue() -> None:
    from core import deps, registry
    from core.tool import KINDS

    tools = registry.all_tools()
    check(len(tools) > 100, f"catalogue loaded ({len(tools)} tools)")

    ids = [tool.id for tool in tools]
    check(len(ids) == len(set(ids)), "tool ids are unique")
    check(all(re.fullmatch(r"[a-z0-9][a-z0-9-]*", tool.id) for tool in tools),
          "tool ids are kebab-case")
    check(all(tool.category in registry.CATEGORY_NAMES for tool in tools),
          "every tool belongs to a known category")
    check(all(len(tool.summary) >= 20 for tool in tools),
          "every tool has a descriptive summary")
    check(len({tool.summary for tool in tools}) == len(tools),
          "no two tools share a summary")
    check(all(tool.fields or tool.id in {"system-info", "uptime", "temp-path", "disk-space",
                                         "local-interfaces", "defender-status",
                                         "firewall-status", "bitlocker-status", "users-list",
                                         "power-plans", "fonts-list", "printers-list",
                                         "disk-health", "partition-list", "volume-info",
                                         "usb-devices", "shadow-copies", "windows-updates",
                                         "startup-items", "services-list", "scheduled-tasks",
                                         "installed-programs", "drivers-list", "pdf-bookmarks",
                                         "duplicate-images", "file-count", "folder-summary",
                                         "cleanup-report", "recycle-bin", "file-shred"}
                for tool in tools),
          "every tool either has options or is deliberately option-free")
    check(all(field.kind in KINDS for tool in tools for field in tool.fields),
          "all field kinds are valid")
    check(all(key in deps.DEPS for tool in tools for key in tool.needs),
          "all dependency keys are known")
    check(all(len(tool.fields) == len({f.key for f in tool.fields}) for tool in tools),
          "no duplicate option keys within a tool")

    from collections import Counter
    duplicates = [summary for summary, count in Counter(t.summary for t in tools).items()
                  if count > 1]
    check(not duplicates, "summaries are unique across the catalogue")


def audit_version() -> None:
    from core import __version__

    version_file = ROOT / "VERSION"
    check(version_file.exists(), "VERSION file exists")
    if version_file.exists():
        check(version_file.read_text(encoding="utf-8").strip() == __version__,
              f"VERSION matches core.__version__ ({__version__})")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    check(__version__ in readme, "README mentions the current version")

    from core import registry
    stats = registry.stats()
    check(f"{stats['tools']} tools" in readme or str(stats["tools"]) in readme,
          "README states the current tool count")


def audit_repository() -> None:
    check((ROOT / ".gitignore").exists(), ".gitignore exists")
    if (ROOT / ".gitignore").exists():
        content = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in ("__pycache__", "*.pyc", "build/", "dist/"):
            check(pattern in content, f".gitignore covers {pattern}")

    try:
        listed = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                                text=True, timeout=60)
        tracked = listed.stdout.splitlines()
        bad = [name for name in tracked if name.endswith(".pyc") or "__pycache__" in name]
        check(not bad, "git is not tracking build artefacts")
    except (OSError, subprocess.SubprocessError):
        NOTES.append("SKIP  git not available, artefact tracking not verified")


def audit_imports() -> None:
    import pkgutil
    import tools as tools_package

    modules = [info.name for info in pkgutil.iter_modules(tools_package.__path__)
               if not info.name.startswith("_")]
    check(len(modules) >= 10, f"tool modules discovered ({len(modules)})")
    for name in modules:
        try:
            __import__(f"tools.{name}")
        except Exception as exc:  # noqa: BLE001
            FAILURES.append(f"tools.{name} failed to import: {exc}")


DOCS = ("README.md", "USER_GUIDE.md", "INSTALLATION.md", "DEVELOPER_GUIDE.md",
        "BUILDING.md", "CHANGELOG.md", "SECURITY.md", "AUTHORS.md", "TOOL_CATALOG.md")


def audit_docs() -> None:
    from core import registry

    for name in DOCS:
        check((ROOT / name).exists(), f"{name} exists")

    landing = ROOT / "docs" / "index.html"
    check(landing.exists(), "docs/index.html (landing page) exists")
    if landing.exists():
        html = landing.read_text(encoding="utf-8")
        stats = registry.stats()
        check(str(stats["tools"]) in html, "landing page states the current tool count")
        check(__import__("core").__version__ in html, "landing page states the current version")
        counts = registry.counts()
        missing = [name for name in registry.CATEGORY_NAMES if f">{name}</span>" not in html]
        check(not missing, "landing page lists every category")
        check(all(f">{counts[name]}</span>" in html or str(counts[name]) in html
                  for name in registry.CATEGORY_NAMES),
              "landing page category counts match the registry")
        for shot in ("home-dark.png", "tool-page.png", "category.png", "home-light.png",
                     "dependencies.png"):
            check((ROOT / "docs" / "screenshots" / shot).exists(),
                  f"landing page screenshot {shot} exists")

    catalogue = ROOT / "TOOL_CATALOG.md"
    check(catalogue.exists(), "TOOL_CATALOG.md exists")
    if catalogue.exists():
        text = catalogue.read_text(encoding="utf-8")
        missing = [tool.id for tool in registry.all_tools() if f"`{tool.id}`" not in text]
        check(not missing, f"catalogue documents every tool ({len(missing)} missing)")
    check((ROOT / "LICENSE").exists(), "LICENSE exists")


def main() -> int:
    # Hygiene first: importing the tools would create __pycache__ and mask it.
    audit_repository()
    audit_catalogue()
    audit_version()
    audit_imports()
    audit_docs()

    for note in NOTES:
        print(note)
    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for failure in FAILURES:
            print(f"  ✕ {failure}")
        return 1
    print(f"\nAudit passed: {len(NOTES)} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
