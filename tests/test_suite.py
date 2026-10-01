import sys
import tempfile

sys.dont_write_bytecode = True
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.cli import build_registry
from core.config import DEFAULT_CONFIG, _deep_merge


def main():
    reg = build_registry()
    assert len(reg.tools) == 551, len(reg.tools)
    assert len({t["cli_command"] for t in reg.tools.values()}) == 551
    assert all(t.get("handler") and t.get("category") for t in reg.tools.values())
    assert (
        _deep_merge(DEFAULT_CONFIG, {"performance": {"multithreading": {"max_threads": 4}}})["performance"][
            "multithreading"
        ]["enabled"]
        is True
    )
    assert (
        _deep_merge(DEFAULT_CONFIG, {"performance": {"multithreading": {"max_threads": 4}}})["performance"][
            "multithreading"
        ]["max_threads"]
        == 4
    )
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "a.txt").write_text("hello world\nhello suite\n", encoding="utf-8")
        (root / "b.txt").write_text("same", encoding="utf-8")
        assert reg.run_tool("count", [str(root / "a.txt")]) == 0
        assert reg.run_tool("checksum", [str(root / "a.txt"), "--algorithm", "sha256"]) == 0
        assert reg.run_tool("filetype", [str(root / "a.txt")]) == 0
        assert reg.run_tool("grep", [str(root), "hello", "--ignore-case"]) == 0
        assert (
            reg.run_tool(
                "splitter", [str(root / "a.txt"), "--size", "5", "--output-dir", str(root / "parts")]
            )
            == 0
        )
        assert reg.run_tool("joiner", [str(root / "parts" / "a.txt.part*"), str(root / "joined.txt")]) == 0
        assert (root / "joined.txt").read_text(encoding="utf-8") == "hello world\nhello suite\n"
    assert reg.run_tool("length-converter", ["1", "km", "m"]) == 0
    assert reg.run_tool("temperature-converter", ["32", "f", "c"]) == 0
    with tempfile.TemporaryDirectory() as td2:
        root2 = Path(td2)
        (root2 / "data.csv").write_text("name,age\nAlice,30\nBob,40\nAlice,30\n", encoding="utf-8")
        (root2 / "a.txt").write_text("same\nleft\n", encoding="utf-8")
        (root2 / "b.txt").write_text("same\nright\n", encoding="utf-8")
        assert reg.run_tool("csv-column-selector", [str(root2 / "data.csv"), "age"]) == 0
        assert reg.run_tool("csv-row-filter", [str(root2 / "data.csv"), "Alice"]) == 0
        assert reg.run_tool("diff-text-files", [str(root2 / "a.txt"), str(root2 / "b.txt")]) == 0
        assert reg.run_tool("patch-preview", [str(root2 / "a.txt")]) == 0
    with tempfile.TemporaryDirectory() as td3:
        root3 = Path(td3)
        import io
        import tarfile
        import zipfile

        bad_zip = root3 / "bad.zip"
        with zipfile.ZipFile(bad_zip, "w") as z:
            z.writestr("../../escape.txt", "owned")
        assert reg.run_tool("zip-extract", [str(bad_zip), str(root3 / "zout")]) != 0
        assert not (root3.parent / "escape.txt").exists()
        bad_tar = root3 / "bad.tar"
        info = tarfile.TarInfo("../../escape.txt")
        data = b"owned"
        info.size = len(data)
        with tarfile.open(bad_tar, "w") as tar:
            tar.addfile(info, io.BytesIO(data))
        assert reg.run_tool("tar-extract", [str(bad_tar), str(root3 / "tout")]) != 0
        assert not (root3.parent / "escape.txt").exists()
        source = root3 / "source.txt"
        source.write_text("alpha\n", encoding="utf-8")
        assert reg.run_tool("renamer", [str(root3), "{name}-x.{ext}"]) == 0
        assert (root3 / "source-x.txt").exists()
    from core.plugin_loader import PluginLoader

    # Legacy external plugins/ layout is gone in 3.0; the empty directory
    # must scan cleanly (deterministic, zero tools) rather than crash.
    loader = PluginLoader(ROOT / "plugins")
    assert loader.get_tools() == []
    # Single-file layout: the embedded bundle must expose the same catalogue.
    from core.bundle import BundleLoader, build_bundle

    bundle_path, count = build_bundle(ROOT)
    assert count == 551, count
    bundle_tools = BundleLoader(bundle_path).get_tools()
    assert len(bundle_tools) == 551
    print("SMOKE TESTS PASSED")
    print(f"{len(reg.tools)} tools validated")


if __name__ == "__main__":
    main()
