"""Tests for the external-dependency catalogue (TASK 2).

The catalogue must be *honest*: it lists exactly the dependencies the packs
really declare, and every entry says what it is, why it is needed and how to
get it.  Nothing here may silently download or execute a binary.

Run:  python -B -m tests.test_dependencies
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

os.environ.setdefault("UTILITY_SUITE_CONFIG_DIR", tempfile.mkdtemp(prefix="us_deps_cfg_"))

from core import dependencies as deps  # noqa: E402
from core.cli import build_registry  # noqa: E402

# Any method that would run something must require explicit user confirmation.
_RUN_METHODS = {"pip", "winget", "choco"}


def _declared_dependencies(tools):
    declared = set()
    for tool in tools:
        for dep in tool.get("dependencies") or []:
            declared.add(dep)
    return declared


def test_catalogue_matches_declared_dependencies():
    """Every dependency a pack names appears in the catalogue — and nothing else."""
    reg = build_registry()
    declared = _declared_dependencies(reg.tools.values())
    catalogue = set(deps.all_dependencies())

    missing = sorted(declared - catalogue)
    assert not missing, f"packs declare dependencies missing from the catalogue: {missing}"

    extra = sorted(catalogue - declared)
    assert not extra, f"catalogue lists dependencies no pack declares: {extra}"

    assert len(catalogue) == 27, len(catalogue)


def test_every_entry_is_complete():
    for name in deps.all_dependencies():
        entry = deps.get(name)
        assert entry is not None
        assert entry.summary.strip(), f"{name} has no summary"
        assert entry.why.strip(), f"{name} has no 'why needed'"
        assert entry.steps, f"{name} has no install steps"
        for step in entry.steps:
            assert step.method in {"path", "builtin", "pip", "winget", "choco", "manual"}
            assert step.label.strip(), f"{name}: step with no label"
            if step.url:
                assert step.url.startswith("https://"), f"{name}: non-https url {step.url}"


def test_check_reports_state_without_raising():
    for name in deps.all_dependencies():
        state = deps.check(name)
        assert set(state) == {"dependency", "installed", "version", "kind", "detail"}
        assert isinstance(state["installed"], bool)
        assert state["version"] is None or isinstance(state["version"], str)
    # 'python' is always satisfied — the suite runs on it.
    assert deps.check("python")["installed"] is True
    # An unknown dependency is reported honestly rather than invented.
    unknown = deps.check("definitely-not-a-real-dependency")
    assert unknown["installed"] is False
    assert unknown["kind"] == "unknown"


def test_install_plan_is_instructions_not_actions():
    """The plan describes how to obtain a dependency; it never fetches one."""
    for name in deps.all_dependencies():
        plan = deps.install_plan(name)
        assert plan["known"] is True
        assert plan["summary"] and plan["why"]
        methods = {s["method"] for s in plan["steps"]}
        assert methods, f"{name} has an empty plan"
        # Any step that runs a package manager must be a user-run command.
        for step in plan["steps"]:
            if step["method"] in _RUN_METHODS:
                assert step["command"], f"{name}: {step['method']} step without a command"
            if step["method"] == "manual":
                assert step["url"].startswith("https://"), f"{name}: manual step needs an https url"
        # Nothing in the catalogue can silently download: there is no method
        # that performs a fetch, and no step claims to.
        assert not (methods & {"auto", "download", "execute"}), methods


def test_install_plan_for_unknown_is_empty_not_fabricated():
    plan = deps.install_plan("definitely-not-a-real-dependency")
    assert plan["known"] is False
    assert plan["steps"] == []
    assert plan["confirm_required"] is False


def test_packs_using_is_derived_from_real_metadata():
    reg = build_registry()
    tools = list(reg.tools.values())
    assert deps.packs_using("ffprobe", tools) == ["audio_tools", "media_metadata", "media_tools", "video_tools"]
    assert deps.packs_using("nobody-uses-this", tools) == []


def test_missing_dependencies_counts_real_tools():
    reg = build_registry()
    missing = deps.missing_dependencies(reg.enabled_tools())
    # A dependency that is genuinely absent blocks the tools that need it.
    if "ffprobe" in missing:
        expected = sum(1 for t in reg.enabled_tools() if "ffprobe" in (t.get("dependencies") or []))
        assert missing["ffprobe"] == expected


def test_no_pack_declares_a_dependency_outside_the_catalogue():
    """A pack whose dependency is not in the catalogue would be un-guideable."""
    reg = build_registry()
    for tool in reg.tools.values():
        for dep in tool.get("dependencies") or []:
            assert deps.is_known(dep), f"{tool['cli_command']} declares unknown dependency {dep!r}"


def main():
    test_catalogue_matches_declared_dependencies()
    test_every_entry_is_complete()
    test_check_reports_state_without_raising()
    test_install_plan_is_instructions_not_actions()
    test_install_plan_for_unknown_is_empty_not_fabricated()
    test_packs_using_is_derived_from_real_metadata()
    test_missing_dependencies_counts_real_tools()
    test_no_pack_declares_a_dependency_outside_the_catalogue()
    print("DEPENDENCY CATALOGUE TESTS PASSED")
    print("  catalogue == the 27 dependencies the packs really declare")
    print("  every entry complete; plans are instructions, never automatic downloads")


if __name__ == "__main__":
    main()
