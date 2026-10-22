"""Unit tests for core.plugin_installer — real files, no mocks of the filesystem.

Run:  python -B -m tests.test_plugin_installer
Exits non-zero (raising SystemExit) on the first failed check.
"""

from __future__ import annotations

import functools
import json
import sys
import tempfile
import threading
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import plugin_installer as pi


def _make_pack_zip(path: Path, name: str, *, include_init: bool = True) -> None:
    """Write a pack zip shaped like a real plugin pack."""
    with zipfile.ZipFile(path, "w") as archive:
        if include_init:
            archive.writestr(
                f"{name}/__init__.py",
                "def register_tools():\n    return []\n",
            )
        else:
            archive.writestr(f"{name}/other.py", "# no __init__\n")


def _serve(directory: Path) -> tuple[ThreadingHTTPServer, str]:
    """Start a throwaway HTTP server for ``directory``; return (server, base_url)."""
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    host, port = server.server_address[:2]
    return server, f"http://{host}:{port}"


# --------------------------------------------------------------------------- #
def test_parse_manifest_fixture() -> None:
    fixture = {
        "version": "3.0.6",
        "generated": "2026-10-22T00:00:00Z",
        "packs": [
            {
                "name": "audio_tools",
                "title": "Audio Tools",
                "tools": 12,
                "size": 20480,
                "file": "audio_tools.zip",
                "description": "Convert and inspect audio.",
            },
            {"name": "video_tools", "tools": "8"},  # minimal entry: defaults apply
            {"nope": "missing a name"},  # skipped
        ],
    }
    with tempfile.TemporaryDirectory() as td:
        manifest_path = Path(td) / "plugins.json"
        manifest_path.write_text(json.dumps(fixture), encoding="utf-8")
        payload = manifest_path.read_bytes()

        calls: list[str] = []
        original = pi._http_get

        def fake_get(url: str, timeout: float) -> bytes:
            calls.append(url)
            return payload

        pi._http_get = fake_get
        try:
            result = pi.fetch_manifest(timeout=1.0)
        finally:
            pi._http_get = original

        assert result.ok, result.error
        assert result.version == "3.0.6" and result.generated.startswith("2026-10-22")
        assert result.source == pi.MANIFEST_URLS[0], "should use the first URL when it works"
        assert calls == [pi.MANIFEST_URLS[0]], "should stop after the first successful URL"
        assert [p.name for p in result.packs] == ["audio_tools", "video_tools"]
        first = result.packs[0]
        assert (first.title, first.tools, first.size, first.file) == (
            "Audio Tools", 12, 20480, "audio_tools.zip",
        )
        assert first.download_url.endswith("/latest-build/audio_tools.zip")
        second = result.packs[1]
        assert second.title == "video_tools" and second.tools == 8 and second.file == "video_tools.zip"


def test_manifest_falls_back_to_second_url() -> None:
    fixture = json.dumps({"version": "1", "generated": "", "packs": [{"name": "x", "tools": 1}]}).encode()
    calls: list[str] = []
    original = pi._http_get

    def fake_get(url: str, timeout: float) -> bytes:
        calls.append(url)
        if url == pi.MANIFEST_URLS[0]:
            raise pi.urllib.error.HTTPError(url, 404, "Not Found", {}, None)  # type: ignore[arg-type]
        return fixture

    pi._http_get = fake_get
    try:
        result = pi.fetch_manifest(timeout=1.0)
    finally:
        pi._http_get = original
    assert result.ok, result.error
    assert calls == list(pi.MANIFEST_URLS), "must try the fallback URL after a 404"
    assert result.source == pi.MANIFEST_URLS[1]


def test_manifest_offline_is_clean() -> None:
    # A closed local port refuses the connection instantly -> exercises the
    # URLError path exactly as an offline machine would.
    result = pi.fetch_manifest(urls=["http://127.0.0.1:1/plugins.json"], timeout=5.0)
    assert not result.ok
    assert result.packs == []
    assert "network unavailable" in result.error.lower(), result.error


def test_zip_validation() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        good = root / "good.zip"
        _make_pack_zip(good, "demo")
        assert pi.validate_pack_zip(good, "demo") is None

        missing = root / "missing.zip"
        _make_pack_zip(missing, "demo", include_init=False)
        problem = pi.validate_pack_zip(missing, "demo")
        assert problem and "__init__.py" in problem, problem

        wrong_name = root / "wrong.zip"
        _make_pack_zip(wrong_name, "demo")
        assert pi.validate_pack_zip(wrong_name, "other") is not None

        not_zip = root / "not.zip"
        not_zip.write_bytes(b"this is not a zip")
        assert pi.validate_pack_zip(not_zip, "demo") is not None


def test_install_remove_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dest = root / "plugins"
        source = root / "demo.zip"
        _make_pack_zip(source, "demo")

        result = pi.install_from_file(source, dest_dir=dest)
        assert result.ok, result.error
        assert (dest / "demo.zip").is_file()

        installed = pi.list_installed(dest)
        assert [p.name for p in installed] == ["demo"], installed
        assert installed[0].kind == "zip" and installed[0].size > 0

        removed = pi.remove_pack("demo", dest_dir=dest)
        assert removed.ok, removed.error
        assert not (dest / "demo.zip").exists()
        assert pi.list_installed(dest) == []
        assert pi.remove_pack("demo", dest_dir=dest).ok is False  # already gone


def test_install_rejects_bad_inputs() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dest = root / "plugins"

        bad_zip = root / "bad.zip"
        _make_pack_zip(bad_zip, "bad", include_init=False)
        assert pi.install_from_file(bad_zip, dest_dir=dest).ok is False
        assert not (dest / "bad.zip").exists()

        plain_py = root / "plain.py"
        plain_py.write_text("x = 1\n", encoding="utf-8")
        assert pi.install_from_file(plain_py, dest_dir=dest).ok is False

        good_py = root / "goodpack.py"
        good_py.write_text("def register_tools():\n    return []\n", encoding="utf-8")
        assert pi.install_from_file(good_py, dest_dir=dest).ok is True
        assert pi.list_installed(dest)[0].kind == "py"

        text = root / "notes.txt"
        text.write_text("hi", encoding="utf-8")
        assert pi.install_from_file(text, dest_dir=dest).ok is False


def test_download_pack_via_local_server() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        served = root / "served"
        served.mkdir()
        _make_pack_zip(served / "demo.zip", "demo")
        dest = root / "plugins"
        server, base = _serve(served)
        try:
            seen: list[tuple[int, int]] = []
            result = pi.download_pack(
                "demo", dest_dir=dest, url=f"{base}/demo.zip", progress=lambda d, t: seen.append((d, t))
            )
            assert result.ok, result.error
            assert (dest / "demo.zip").is_file()
            assert result.bytes_written > 0
            assert seen and seen[-1][0] == result.bytes_written
            assert all(total >= 0 for _, total in seen)
        finally:
            server.shutdown()

        # A zip that is not a valid <name> pack must be rejected and deleted.
        served_bad = root / "bad"
        served_bad.mkdir()
        _make_pack_zip(served_bad / "demo.zip", "demo", include_init=False)
        dest2 = root / "plugins2"
        server2, base2 = _serve(served_bad)
        try:
            bad = pi.download_pack("demo", dest_dir=dest2, url=f"{base2}/demo.zip")
            assert bad.ok is False and "__init__.py" in bad.error
            assert not (dest2 / "demo.zip").exists(), "rejected download must be removed"
            assert not list(dest2.glob("*.part")), "no partial file should remain"
        finally:
            server2.shutdown()


def test_download_offline_is_clean() -> None:
    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "plugins"
        result = pi.download_pack("demo", dest_dir=dest, url="http://127.0.0.1:1/demo.zip", timeout=5.0)
        assert result.ok is False
        assert "network unavailable" in result.error.lower(), result.error
        assert not dest.exists() or not list(dest.glob("*")), "offline download must leave nothing behind"


def test_remove_refuses_outside_plugins_dir() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dest = root / "plugins"
        dest.mkdir()
        outside = root / "victim.zip"
        outside.write_bytes(b"x")
        for bad_name in ("../victim", "..", "/etc/passwd", "a/b"):
            try:
                pi.remove_pack(bad_name, dest_dir=dest)
            except pi.PluginInstallerError:
                pass
            else:
                raise AssertionError(f"remove_pack accepted dangerous name {bad_name!r}")
        assert outside.exists(), "a path outside the plugins dir must never be touched"


def test_download_refuses_path_traversal() -> None:
    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "plugins"
        try:
            pi.download_pack("../escape", dest_dir=dest)
        except pi.PluginInstallerError:
            pass
        else:
            raise AssertionError("download_pack accepted a path-traversal name")
        try:
            pi.download_pack("demo", dest_dir=dest, file="../../escape.zip")
        except pi.PluginInstallerError:
            pass
        else:
            raise AssertionError("download_pack accepted a path-traversal file name")


def test_plugins_dir_resolution() -> None:
    directory = pi.get_plugins_dir()
    assert directory.name == "plugins", directory
    assert directory.is_dir()
    assert directory.resolve() == (ROOT / "plugins").resolve(), directory


def main() -> None:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"PLUGIN INSTALLER TESTS PASSED ({len(tests)} tests)")


if __name__ == "__main__":
    main()
