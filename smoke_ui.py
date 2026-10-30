"""Headless UI smoke test: build the window, walk pages, save screenshots."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtCore import QSize, Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from core import registry  # noqa: E402
from core.settings import Settings  # noqa: E402
from ui.app import _configure  # noqa: E402
from ui.window import MainWindow  # noqa: E402

SHOTS = Path("shots")
SHOTS.mkdir(exist_ok=True)


def grab(window: MainWindow, name: str) -> None:
    window.resize(QSize(1280, 820))
    QApplication.processEvents()
    pixmap = window.grab()
    path = SHOTS / f"{name}.png"
    pixmap.save(str(path))
    print(f"saved {path}  ({pixmap.width()}×{pixmap.height()})")


def main() -> int:
    app = QApplication(sys.argv[:1])
    settings = Settings(Path("/tmp/all4one-test-settings.json"))
    settings.data["theme"] = "dark"
    settings.data["favourites"] = ["hash-file", "pdf-merge", "image-resize"]
    settings.data["recent"] = ["word-count", "ip-calc", "gst-calc"]
    _configure(app, "dark")
    window = MainWindow(settings)
    window.show()
    QApplication.processEvents()

    grab(window, "01-home")

    window.open_category("PDF")
    QApplication.processEvents()
    grab(window, "02-category")

    tool = registry.get("pdf-merge")
    window.open_tool(tool)
    QApplication.processEvents()
    grab(window, "03-tool")

    window.open_dependencies()
    QApplication.processEvents()
    grab(window, "04-deps")

    window.settings.data["theme"] = "light"
    window.theme = "light"
    window.apply_theme()
    window.go_home()
    QApplication.processEvents()
    grab(window, "05-home-light")

    print("UI smoke test passed:", len(registry.all_tools()), "tools")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
