"""Tests for per-pack enable/disable (TASK 1).

Covers:
* the default state — every pack enabled, so an existing install is unchanged;
* a disabled pack's tools are absent from listing/search and refused by
  ``get_tool`` / ``run_tool`` (with a clear message, not a crash);
* re-enabling restores them;
* the choice persists across a registry reload;
* ``pack_summaries`` carries name/title/count/enabled/runnable;
* the preference is written to the user's config location, not the install dir.

Run:  python -B -m tests.test_packs
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.dont_write_bytecode = True

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Point the durable preferences file at a throwaway directory BEFORE importing
# core, so the test never touches the real user profile.
_CFG = tempfile.mkdtemp(prefix="us_packs_cfg_")
os.environ["UTILITY_SUITE_CONFIG_DIR"] = _CFG

from core import preferences as prefs  # noqa: E402
from core.cli import build_registry  # noqa: E402

VICTIM = "file_ops"          # a self-contained pack with no external dependencies
VICTIM_TOOL = "checksum"     # one of its tools


def _fresh_prefs():
    path = Path(_CFG) / "preferences.json"
    if path.exists():
        path.unlink()


def test_default_all_enabled():
    _fresh_prefs()
    reg = build_registry()
    assert len(reg.tools) == 551, len(reg.tools)
    assert reg.enabled_packs() == reg.all_packs(), "every pack must be enabled by default"
    assert len(reg.all_packs()) == 45, len(reg.all_packs())
    assert reg.is_pack_enabled(VICTIM) is True
    assert reg.get_tool(VICTIM_TOOL) is not None
    assert len(reg.enabled_tools()) == 551
    # An empty opt-out list is the whole stored state.
    assert reg.preferences.disabled_packs() == ()


def test_preferences_location_is_user_dir_not_install_dir():
    _fresh_prefs()
    reg = build_registry()
    reg.set_pack_enabled(VICTIM, False)
    written = Path(_CFG) / "preferences.json"
    assert written.exists(), "preferences must be written to the user config dir"
    # ...and never into the install directory.
    assert prefs.preferences_path() == written
    assert prefs.preferences_path() != ROOT / "config.json"
    # The install-dir config.json is untouched by a preference change.
    import json

    install_cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    assert install_cfg.get("packs", {}).get("disabled", []) == []


def test_disable_hides_and_refuses():
    _fresh_prefs()
    reg = build_registry()
    assert reg.get_tool(VICTIM_TOOL) is not None

    reg.set_pack_enabled(VICTIM, False)

    # absent from listing
    listed = {t["cli_command"] for tools in reg.list_categories().values() for t in tools}
    assert VICTIM_TOOL not in listed
    # absent from search
    assert all(t["cli_command"] != VICTIM_TOOL for t in reg.search("checksum"))
    assert all(t["cli_command"] != VICTIM_TOOL for t in reg.search(""))
    # refused by get_tool (no crash)
    assert reg.get_tool(VICTIM_TOOL) is None
    # refused by run_tool with a clear message
    captured: list[str] = []
    rc = reg.run_tool(VICTIM_TOOL, [], output=captured.append)
    assert rc == 4, rc
    message = "\n".join(captured).lower()
    assert "disabled" in message and VICTIM in message, message
    # and the enabled tool count drops by exactly the pack's size
    pack_size = sum(1 for t in reg.tools.values() if t["pack"] == VICTIM)
    assert len(reg.enabled_tools()) == 551 - pack_size


def test_reenable_restores():
    _fresh_prefs()
    reg = build_registry()
    reg.set_pack_enabled(VICTIM, False)
    assert reg.get_tool(VICTIM_TOOL) is None
    reg.set_pack_enabled(VICTIM, True)
    assert reg.is_pack_enabled(VICTIM) is True
    assert reg.get_tool(VICTIM_TOOL) is not None
    assert len(reg.enabled_tools()) == 551


def test_choice_persists_across_reload():
    _fresh_prefs()
    reg = build_registry()
    reg.set_pack_enabled(VICTIM, False)

    # A brand-new registry (as the GUI's on_refresh builds) sees the choice.
    reloaded = build_registry()
    assert reloaded.is_pack_enabled(VICTIM) is False
    assert reloaded.get_tool(VICTIM_TOOL) is None
    assert VICTIM in reloaded.disabled_packs()
    assert VICTIM not in reloaded.enabled_packs()

    # And so does a fresh PackPreferences instance reading the file directly.
    direct = prefs.PackPreferences()
    assert direct.is_enabled(VICTIM) is False

    reloaded.set_pack_enabled(VICTIM, True)
    assert build_registry().is_pack_enabled(VICTIM) is True


def test_pack_summaries():
    _fresh_prefs()
    reg = build_registry()
    summaries = reg.pack_summaries()
    assert len(summaries) == 45
    for s in summaries:
        assert set(s) == {"name", "title", "tool_count", "enabled", "runnable"}, s
        assert s["tool_count"] >= 1
        assert isinstance(s["enabled"], bool)
        assert 0 <= s["runnable"] <= s["tool_count"]
    by_name = {s["name"]: s for s in summaries}
    assert by_name[VICTIM]["title"] == "File Operations"
    assert by_name[VICTIM]["enabled"] is True
    # runnable counts tools whose dependencies are installed right now
    file_ops_tools = [t for t in reg.tools.values() if t["pack"] == VICTIM]
    assert by_name[VICTIM]["runnable"] == sum(1 for t in file_ops_tools if t["available"])

    reg.set_pack_enabled(VICTIM, False)
    assert {s["name"]: s for s in reg.pack_summaries()}[VICTIM]["enabled"] is False


def test_disabled_pack_reflected_in_run_for_real_tool():
    """End-to-end: a disabled pack's tool cannot be executed."""
    _fresh_prefs()
    reg = build_registry()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "a.txt"
        f.write_text("hello\n", encoding="utf-8")
        assert reg.run_tool(VICTIM_TOOL, [str(f)]) == 0

        reg.set_pack_enabled(VICTIM, False)
        captured: list[str] = []
        rc = reg.run_tool(VICTIM_TOOL, [str(f)], output=captured.append)
        assert rc == 4
        assert "disabled" in "\n".join(captured).lower()

        reg.set_pack_enabled(VICTIM, True)
        assert reg.run_tool(VICTIM_TOOL, [str(f)]) == 0


def main():
    test_default_all_enabled()
    test_preferences_location_is_user_dir_not_install_dir()
    test_disable_hides_and_refuses()
    test_reenable_restores()
    test_choice_persists_across_reload()
    test_pack_summaries()
    test_disabled_pack_reflected_in_run_for_real_tool()
    print("PACK ENABLE/DISABLE TESTS PASSED")
    print("  default = all 45 packs enabled; disabled pack's tools hidden and refused")
    print("  re-enable restores; choice persists across a registry reload")


if __name__ == "__main__":
    main()
