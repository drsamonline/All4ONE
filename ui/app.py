"""Desktop entry point."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import QApplication

from core import APP_NAME, __version__
from core.settings import Settings

from .theme import stylesheet
from .window import MainWindow


def _configure(app: QApplication, theme: str) -> None:
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("drsamonline")
    app.setStyle("Fusion")

    palette_obj = QPalette()
    palette_obj.setColor(QPalette.Window, Qt.transparent)
    palette_obj.setColor(QPalette.Base, Qt.transparent)
    palette_obj.setColor(QPalette.Text, Qt.white if theme == "dark" else Qt.black)
    app.setPalette(palette_obj)

    font = QFont()
    for family in ("Segoe UI Variable Text", "Segoe UI", "Inter", "Noto Sans", "DejaVu Sans"):
        font.setFamily(family)
        if QFont(family).exactMatch():
            break
    font.setPointSize(10)
    app.setFont(font)
    app.setStyleSheet(stylesheet(theme))


def run(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication.instance() or QApplication(argv)
    settings = Settings()
    theme = str(settings.get("theme", "dark"))
    _configure(app, theme)
    window = MainWindow(settings)
    window.show()
    return app.exec()
