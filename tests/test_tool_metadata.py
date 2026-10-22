"""Tests for the optional per-tool metadata that drives the conditional UI.

Every field is *optional*: a tool without ``accepts`` / ``produces`` /
``destructive`` keeps today's behaviour (the GUI shows every control).  The
curated table is applied with ``setdefault`` semantics, so a pack may declare
its own values and they win.

Run:  python -B -m tests.test_tool_metadata
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

os.environ.setdefault("UTILITY_SUITE_CONFIG_DIR", tempfile.mkdtemp(prefix="us_meta_cfg_"))

from core.cli import build_registry  # noqa: E402
from core.tool_registry import TOOL_METADATA, apply_tool_metadata  # noqa: E402

VALID_ACCEPTS = {"file", "folder", "text", "none"}
VALID_PRODUCES = {"file", "text", "none"}


def test_table_is_well_formed():
    for cmd, meta in TOOL_METADATA.items():
        assert isinstance(cmd, str) and cmd
        assert set(meta) <= {"accepts", "produces", "destructive"}, (cmd, meta)
        if "accepts" in meta:
            assert meta["accepts"] in VALID_ACCEPTS, (cmd, meta["accepts"])
        if "produces" in meta:
            assert meta["produces"] in VALID_PRODUCES, (cmd, meta["produces"])
        if "destructive" in meta:
            assert meta["destructive"] is True, "destructive is only ever set when true"


def test_every_key_is_a_real_tool():
    reg = build_registry()
    unknown = sorted(cmd for cmd in TOOL_METADATA if cmd not in reg.tools)
    assert not unknown, f"metadata keys that match no tool: {unknown}"


def test_absent_fields_stay_absent():
    """A tool with no entry keeps every field absent (=> old GUI behaviour)."""
    reg = build_registry()
    populated = {t["cli_command"] for t in reg.tools.values() if t["cli_command"] in TOOL_METADATA}
    for tool in reg.tools.values():
        if tool["cli_command"] in populated:
            continue
        assert "accepts" not in tool, tool["cli_command"]
        assert "produces" not in tool, tool["cli_command"]
        assert "destructive" not in tool, tool["cli_command"]


def test_pack_metadata_wins():
    """An explicit value on the tool entry is never overwritten."""
    tool = {"cli_command": "checksum", "accepts": "folder", "produces": "file"}
    out = apply_tool_metadata(dict(tool))
    assert out["accepts"] == "folder"
    assert out["produces"] == "file"


def test_applied_metadata_is_valid():
    reg = build_registry()
    for tool in reg.tools.values():
        if "accepts" in tool:
            assert tool["accepts"] in VALID_ACCEPTS, tool["cli_command"]
        if "produces" in tool:
            assert tool["produces"] in VALID_PRODUCES, tool["cli_command"]
        if "destructive" in tool:
            assert tool["destructive"] is True


def test_population_count_is_reported():
    """The metadata is populated for a real, non-trivial subset — and we know how big."""
    reg = build_registry()
    populated = sum(1 for t in reg.tools.values() if any(k in t for k in ("accepts", "produces", "destructive")))
    assert populated == len(TOOL_METADATA)
    assert 250 <= populated < 551, populated  # honest subset, not the whole catalogue


def main():
    test_table_is_well_formed()
    test_every_key_is_a_real_tool()
    test_absent_fields_stay_absent()
    test_pack_metadata_wins()
    test_applied_metadata_is_valid()
    test_population_count_is_reported()
    print("TOOL METADATA TESTS PASSED")
    print(f"  {len(TOOL_METADATA)}/551 tools carry accepts/produces/destructive metadata")
    print("  absent fields stay absent (old behaviour); pack-declared values win")


if __name__ == "__main__":
    main()
