"""Regression test for the registry MERGE in ``core.cli.build_registry``.

The defect this guards: ``build_registry()`` used to be a strict priority chain
that returned as soon as the embedded bundle yielded any tools, so a released
``utility_suite.exe`` (which always carries ``bundle/tools.dat``) never read the
external ``plugins/`` directory.  A pack downloaded through the Plugins panel
landed in ``plugins/`` and was silently ignored.

The fix makes the registry a merge with external packs taking precedence:

    external plugins/ (override)  ->  embedded bundle (baseline)  ->  source tree

This test builds a *tiny throwaway* bundle and a *tiny throwaway* pack zip in
temporary directories (it never touches the real 638 KB ``bundle/tools.dat`` or
the real ``plugins/`` folder) and checks that the external pack is both read and
able to override an embedded command.

Run:  python -B -m tests.test_registry_merge
Exits non-zero (AssertionError) on the first failed check.
"""

from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.bundle as bundle_mod
import core.cli as cli_mod
from core.bundle import BundleLoader
from core.cli import build_registry
from core.plugin_loader import PluginLoader
from core.tool_registry import ToolRegistry

# The external pack provides TWO commands: one that also exists in the embedded
# bundle (so it must override) and one brand-new (so it proves plugins are read).
EXTERNAL_PACK = "ext_pack"
OVERRIDDEN_CMD = "shared-cmd"
NEW_CMD = "ext-new-cmd"

# The throwaway bundle provides three commands, one of which collides with the
# external pack.
BUNDLE_CMDS = ("bundle-only-1", "bundle-only-2", OVERRIDDEN_CMD)
BUNDLE_PACK = "embedded_pack"

# Expected merge size: bundle + external tools - the one overridden collision.
EXPECTED_TOTAL = len(BUNDLE_CMDS) + 2 - 1  # == 4


def _make_bundle(path: Path) -> Path:
    """Write a minimal but valid bundle archive (catalog.json only).

    ``BundleLoader.get_tools`` reads only ``catalog.json``, so no real handler
    modules are needed — this keeps the test self-contained and fast.
    """
    tools = [
        {
            "name": f"Bundled {cmd}",
            "category": "Bundled",
            "description": f"A tool shipped inside the embedded bundle ({cmd}).",
            "handler": f"handlers.run_{cmd.replace('-', '_')}",
            "cli_command": cmd,
            "pack": BUNDLE_PACK,
            "dependencies": [],
        }
        for cmd in BUNDLE_CMDS
    ]
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("catalog.json", json.dumps({"tools": tools}))
    return path


def _make_pack_zip(path: Path, name: str) -> Path:
    """Write a pack zip whose register_tools() returns the external metadata.

    A stub pack with an empty dependency list, so ``CapabilityChecker`` marks
    every tool available and the test needs no external programs/packages.
    """
    source = (
        "def register_tools():\n"
        "    return [\n"
        "        {\n"
        "            'name': 'Shared Command (external)',\n"
        "            'category': 'External',\n"
        "            'description': 'External override of a bundled command.',\n"
        "            'handler': 'handlers.run_shared',\n"
        f"            'cli_command': '{OVERRIDDEN_CMD}',\n"
        "            'dependencies': [],\n"
        "        },\n"
        "        {\n"
        "            'name': 'Brand New Command',\n"
        "            'category': 'External',\n"
        "            'description': 'A command only the external pack provides.',\n"
        "            'handler': 'handlers.run_new',\n"
        f"            'cli_command': '{NEW_CMD}',\n"
        "            'dependencies': [],\n"
        "        },\n"
        "    ]\n"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"{name}/__init__.py", source)
    return path


def _old_build_registry(bundle_path: Path | None, plugins_dir: Path) -> ToolRegistry:
    """The pre-fix logic, reproduced verbatim so we can prove it would fail.

    This is a strict priority chain with an early return on the bundle, so the
    external plugins directory is never consulted once a bundle is present.
    """
    if bundle_path is not None:
        tools = BundleLoader(bundle_path).get_tools()
        if tools:
            return ToolRegistry(tools)
    tools = PluginLoader(plugins_dir).get_tools()
    if tools:
        return ToolRegistry(tools)
    return ToolRegistry([])


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bundle_path = _make_bundle(root / "tools.dat")
        plugins_dir = root / "plugins"
        plugins_dir.mkdir()
        _make_pack_zip(plugins_dir / f"{EXTERNAL_PACK}.zip", EXTERNAL_PACK)

        # Point build_registry() at the throwaway sources without touching the
        # real bundle/ or plugins/. Both lookups are module-level attributes
        # resolved at call time, so monkeypatching them is enough.
        real_get_bundle_path = bundle_mod.get_bundle_path
        real_get_plugins_dir = cli_mod.get_plugins_dir
        bundle_mod.get_bundle_path = lambda: bundle_path
        cli_mod.get_plugins_dir = lambda: plugins_dir
        try:
            reg = build_registry()

            # (a) The brand-new tool from the external pack IS present — this is
            #     the exact regression the fix addresses (plugins were ignored).
            assert reg.get_tool(NEW_CMD) is not None, (
                "external pack tool missing: the plugins/ directory was not read"
            )
            assert reg.get_tool(NEW_CMD)["pack"] == EXTERNAL_PACK

            # (b) The overridden command resolves to the EXTERNAL pack, not the
            #     embedded one — external packs win the first-registration dedup.
            shared = reg.get_tool(OVERRIDDEN_CMD)
            assert shared is not None, OVERRIDDEN_CMD
            assert shared["pack"] == EXTERNAL_PACK, (
                f"expected {OVERRIDDEN_CMD!r} to come from {EXTERNAL_PACK!r}, "
                f"got {shared['pack']!r}"
            )

            # The baseline is still intact for commands the pack did not claim.
            assert reg.get_tool("bundle-only-1")["pack"] == BUNDLE_PACK
            assert reg.get_tool("bundle-only-2")["pack"] == BUNDLE_PACK

            # (c) Total == bundle + external - overridden, and no duplicates.
            assert len(reg.tools) == EXPECTED_TOTAL, (len(reg.tools), EXPECTED_TOTAL)
            assert len(reg.tools) == len(set(reg.tools)), "duplicate commands survived"

            # Guard the fix: the old strict-priority chain would have returned
            # the bundle-only registry, dropping the external pack entirely.
            old = _old_build_registry(bundle_path, plugins_dir)
            assert old.get_tool(NEW_CMD) is None, (
                "old logic unexpectedly read plugins/ — this test would not guard the fix"
            )
            assert old.get_tool(OVERRIDDEN_CMD)["pack"] == BUNDLE_PACK
            assert len(old.tools) == len(BUNDLE_CMDS), len(old.tools)
            assert len(old.tools) != len(reg.tools), "old and new registries must differ"
        finally:
            bundle_mod.get_bundle_path = real_get_bundle_path
            cli_mod.get_plugins_dir = real_get_plugins_dir

    print("REGISTRY MERGE TESTS PASSED")
    print(
        f"  external pack read: {NEW_CMD!r} present; "
        f"{OVERRIDDEN_CMD!r} overridden by {EXTERNAL_PACK!r}"
    )
    print(
        f"  merge count: {EXPECTED_TOTAL} = bundle {len(BUNDLE_CMDS)} + external 2 - overridden 1"
    )


if __name__ == "__main__":
    main()
