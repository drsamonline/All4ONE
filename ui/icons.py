"""Line icons drawn as SVG at runtime — no image files to ship."""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# 24×24 viewBox, stroke-based paths.
PATHS: dict[str, str] = {
    "home": "M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
    "star": "M12 3l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.8 6.2 20.9l1.1-6.5L2.6 9.8l6.5-.9z",
    "clock": "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2",
    "search": "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.3-4.3",
    "settings": "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 7 19.4a1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.6 1.6 0 0 0 3 14.2H3a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 4.6 7a1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.6 1.6 0 0 0 9 3V3a2 2 0 1 1 4 0v.1A1.6 1.6 0 0 0 15 4.6a1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0 1.1 2.7H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z",
    "grid": "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z",
    "package": "M21 8l-9-5-9 5v8l9 5 9-5zM3 8l9 5 9-5M12 13v9",
    "files": "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5",
    "text": "M5 6h14M5 12h14M5 18h9",
    "data": "M12 8c4.4 0 8-1.3 8-3s-3.6-3-8-3-8 1.3-8 3 3.6 3 8 3zM4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3",
    "key": "M15 9a4 4 0 1 0-3.5 4l-1 1H8v2H6v2H3v-3l7.5-7.5A4 4 0 0 1 15 9z",
    "image": "M4 5h16v14H4zM4 15l4-4 4 4 3-3 5 5M9 9.5a1 1 0 1 0 0-.01",
    "pdf": "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M8 16h8M8 12h4",
    "media": "M4 5h16v14H4zM10 9l5 3-5 3z",
    "document": "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M8 13h8M8 17h5",
    "network": "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM3 12h18M12 3c2.5 2.4 3.8 5.6 3.8 9S14.5 18.6 12 21c-2.5-2.4-3.8-5.6-3.8-9S9.5 5.4 12 3z",
    "system": "M9 18h6M10 21h4M12 3a6 6 0 0 0-3 11.2V16h6v-1.8A6 6 0 0 0 12 3z",
    "disk": "M4 6h16v5H4zM4 13h16v5H4zM7 8.5h.01M7 15.5h.01",
    "code": "M9 7l-5 5 5 5M15 7l5 5-5 5",
    "shield": "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z",
    "numbers": "M5 8h14M5 16h14M9 4l-2 16M17 4l-2 16",
    "sparkles": "M12 3l1.8 4.6L18 9l-4.2 1.4L12 15l-1.8-4.6L6 9l4.2-1.4zM18 15l.9 2.3L21 18l-2.1.7L18 21l-.9-2.3L15 18l2.1-.7z",
    "play": "M8 5l11 7-11 7z",
    "stop": "M7 7h10v10H7z",
    "copy": "M9 9h10v10H9zM5 15V5h10",
    "save": "M5 5h11l3 3v11H5zM8 5v5h7V5M8 19v-5h8v5",
    "folder": "M4 6h6l2 2h8v10H4z",
    "refresh": "M20 12a8 8 0 1 1-2.3-5.7M20 4v4h-4",
    "check": "M5 13l4 4L19 7",
    "alert": "M12 4l9 16H3zM12 10v4M12 17h.01",
    "arrow-left": "M15 6l-6 6 6 6",
    "external": "M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5",
    "moon": "M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5z",
    "sun": "M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4",
    "trash": "M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13M10 11v6M14 11v6",
    "plug": "M9 3v6M15 3v6M6 9h12v3a6 6 0 0 1-12 0zM12 18v3",
}

CATEGORY_ICONS = {
    "Files": "files",
    "Archives": "package",
    "Text": "text",
    "Data": "data",
    "Encoding": "key",
    "Images": "image",
    "PDF": "pdf",
    "Media": "media",
    "Documents": "document",
    "Network": "network",
    "System": "system",
    "Disk": "disk",
    "Developer": "code",
    "Security": "shield",
    "Numbers": "numbers",
    "Generators": "sparkles",
}


def svg(name: str, colour: str, size: int = 20, width: float = 1.7) -> bytes:
    path = PATHS.get(name, PATHS["grid"])
    body = "".join(f'<path d="M{part}" />' for part in path.split("M")[1:])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" '
        f'height="{size}" fill="none" stroke="{colour}" stroke-width="{width}" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    ).encode("utf-8")


@lru_cache(maxsize=512)
def _pixmap(name: str, colour: str, size: int) -> QPixmap:
    renderer = QSvgRenderer(QByteArray(svg(name, colour, size)))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    renderer.render(painter)
    painter.end()
    return pixmap


def icon(name: str, colour: str = "#8b98a9", size: int = 18) -> QIcon:
    return QIcon(_pixmap(name, colour, size))


def pixmap(name: str, colour: str = "#8b98a9", size: int = 18) -> QPixmap:
    return _pixmap(name, colour, size)


def category_icon(category: str) -> str:
    return CATEGORY_ICONS.get(category, "grid")
