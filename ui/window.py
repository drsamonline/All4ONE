"""The application shell: sidebar, navigation history and theme handling."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QCursor, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core import APP_NAME, APP_TAGLINE, __version__, registry
from core.settings import Settings

from . import icons
from .pages import DependenciesPage, HomePage, SettingsPage, ToolListPage, ToolPage
from .theme import icon_colour, palette, stylesheet
from .widgets import Divider, icon_button, icon_label


class Sidebar(QWidget):
    def __init__(self, window: "MainWindow") -> None:
        super().__init__()
        self.window = window
        self.setObjectName("Sidebar")
        self.setFixedWidth(252)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 14)
        layout.setSpacing(10)

        # brand
        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        mark = QFrame()
        mark.setFixedSize(34, 34)
        theme = window.theme
        mark.setStyleSheet(f"background:{palette(theme)['accent']}; border-radius:10px;")
        mark_layout = QHBoxLayout(mark)
        mark_layout.setContentsMargins(0, 0, 0, 0)
        mark_layout.addWidget(icon_label("grid", "#ffffff", 18), 0, Qt.AlignCenter)
        brand_row.addWidget(mark)

        brand_column = QVBoxLayout()
        brand_column.setSpacing(0)
        name = QLabel(APP_NAME)
        name.setObjectName("Brand")
        version = QLabel(f"v{__version__}  ·  no plugins")
        version.setObjectName("BrandSub")
        brand_column.addWidget(name)
        brand_column.addWidget(version)
        brand_row.addLayout(brand_column, 1)
        layout.addLayout(brand_row)

        layout.addSpacing(6)

        # search
        self.search = QLineEdit()
        self.search.setObjectName("Search")
        self.search.setPlaceholderText("Search tools    Ctrl+K")
        self.search.textChanged.connect(self.window.on_search_typing)
        self.search.returnPressed.connect(self.window.on_search_enter)
        layout.addWidget(self.search)

        layout.addSpacing(2)

        # primary nav
        self.nav_buttons: dict[str, QPushButton] = {}
        for key, label, icon_name in (("home", "Home", "home"),
                                      ("favourites", "Favourites", "star"),
                                      ("recent", "Recently used", "clock")):
            button = QPushButton(f"  {label}")
            button.setObjectName("NavItem")
            button.setCheckable(True)
            button.setCursor(QCursor(Qt.PointingHandCursor))
            button.setIcon(icons.icon(icon_name, icon_colour(theme, "text_dim"), 15))
            button.setIconSize(QSize(15, 15))
            button.clicked.connect(lambda _=False, k=key: self.window.open_nav(k))
            self.nav_buttons[key] = button
            layout.addWidget(button)

        layout.addSpacing(4)
        caption = QLabel("CATEGORIES")
        caption.setObjectName("BrandSub")
        caption.setContentsMargins(10, 4, 0, 2)
        layout.addWidget(caption)

        # category list (scrolls independently)
        self.category_holder = QVBoxLayout()
        self.category_holder.setSpacing(1)
        holder_widget = QWidget()
        holder_widget.setLayout(self.category_holder)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setWidget(holder_widget)
        layout.addWidget(area, 1)

        layout.addWidget(Divider(name="SidebarDivider"))

        footer = QHBoxLayout()
        footer.setSpacing(4)
        deps_button = QPushButton("  Dependencies")
        deps_button.setObjectName("NavItem")
        deps_button.setCursor(QCursor(Qt.PointingHandCursor))
        deps_button.setIcon(icons.icon("plug", icon_colour(theme, "text_dim"), 15))
        deps_button.clicked.connect(self.window.open_dependencies)
        footer.addWidget(deps_button, 1)

        settings_button = icon_button("settings", "Settings", theme)
        settings_button.clicked.connect(self.window.open_settings)
        footer.addWidget(settings_button)

        self.theme_button = icon_button("sun" if theme == "dark" else "moon",
                                        "Switch theme", theme)
        self.theme_button.clicked.connect(self.window.toggle_theme)
        footer.addWidget(self.theme_button)
        layout.addLayout(footer)

        self.counts = registry.counts()
        self.rebuild_categories()

    def rebuild_categories(self) -> None:
        while self.category_holder.count():
            item = self.category_holder.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        theme = self.window.theme
        counts = registry.counts()
        for category in registry.CATEGORY_NAMES:
            button = QPushButton(f"  {category}")
            button.setObjectName("NavItem")
            button.setCheckable(True)
            button.setCursor(QCursor(Qt.PointingHandCursor))
            button.setIcon(icons.icon(icons.category_icon(category),
                                      icon_colour(theme, "text_dim"), 15))
            button.setIconSize(QSize(15, 15))
            button.setToolTip(f"{counts[category]} tools — {registry.blurb(category)}")
            button.clicked.connect(lambda _=False, c=category: self.window.open_category(c))
            self.category_holder.addWidget(button)
        self.category_holder.addStretch(1)

    def set_active(self, key: str) -> None:
        for name, button in self.nav_buttons.items():
            button.setChecked(name == key)

    def focus_search(self) -> None:
        self.search.setFocus()
        self.search.selectAll()


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__()
        self.settings = settings or Settings()
        self.theme = str(self.settings.get("theme", "dark"))
        if self.theme not in ("dark", "light"):
            self.theme = "dark"

        self.setWindowTitle(f"{APP_NAME} — {APP_TAGLINE}")
        self.setMinimumSize(980, 640)
        geometry = self.settings.get("window", {}) or {}
        self.resize(int(geometry.get("w", 1240)), int(geometry.get("h", 800)))
        self.setWindowIcon(QIcon(icons.pixmap("grid", palette(self.theme)["accent"], 64)))

        root = QWidget()
        root.setObjectName("Root")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar(self)
        layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentArea")
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        self.history: list[tuple[str, Any]] = []
        self.current: tuple[str, Any] = ("home", None)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(220)
        self._search_timer.timeout.connect(self._run_search)

        QShortcut(QKeySequence("Ctrl+K"), self, activated=self.sidebar.focus_search)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.sidebar.focus_search)
        QShortcut(QKeySequence("Escape"), self, activated=self._escape)

        self.apply_theme(rebuild=False)
        self.go_home()

    # -- theme -------------------------------------------------------------
    def apply_theme(self, rebuild: bool = True) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet(self.theme))
        self.setWindowIcon(QIcon(icons.pixmap("grid", palette(self.theme)["accent"], 64)))
        if rebuild:
            self.sidebar.theme_button.setIcon(
                icons.icon("sun" if self.theme == "dark" else "moon",
                           icon_colour(self.theme, "text_dim"), 16))
            self.sidebar.rebuild_categories()
            self._render_current()

    def toggle_theme(self) -> None:
        self.theme = "light" if self.theme == "dark" else "dark"
        self.settings.set("theme", self.theme)
        self.apply_theme()

    # -- navigation --------------------------------------------------------
    def _show(self, descriptor: tuple[str, Any], push: bool = True) -> None:
        if push and descriptor != self.current:
            self.history.append(self.current)
        self.current = descriptor
        page = self._build_page(descriptor)
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        if hasattr(page, "on_show"):
            page.on_show()
        self._highlight_nav(descriptor)

    def _render_current(self) -> None:
        page = self._build_page(self.current)
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        if hasattr(page, "on_show"):
            page.on_show()
        self._highlight_nav(self.current)

    def _build_page(self, descriptor: tuple[str, Any]):
        kind, payload = descriptor
        if kind == "home":
            return HomePage(self)
        if kind == "tool":
            return ToolPage(self, payload)
        if kind == "category":
            tools = registry.in_category(payload)
            return ToolListPage(self, payload,
                                f"{len(tools)} tools · {registry.blurb(payload)}", tools)
        if kind == "search":
            query, results = payload
            return ToolListPage(self, f"Results for “{query}”",
                                f"{len(results)} matching tool(s)", results)
        if kind == "settings":
            return SettingsPage(self)
        if kind == "deps":
            return DependenciesPage(self)
        if kind == "favourites":
            tools = [tool for tool in (registry.get(i) for i in
                                       self.settings.get("favourites", [])) if tool]
            return ToolListPage(self, "Favourites",
                                "Tools you starred, always one click away.", tools)
        if kind == "recent":
            tools = [tool for tool in (registry.get(i) for i in
                                       self.settings.get("recent", [])) if tool]
            return ToolListPage(self, "Recently used",
                                "The last tools you ran, newest first.", tools)
        return HomePage(self)

    def _highlight_nav(self, descriptor: tuple[str, Any]) -> None:
        kind = descriptor[0]
        if kind in ("home", "favourites", "recent"):
            self.sidebar.set_active(kind)
        else:
            self.sidebar.set_active("")

    def _escape(self) -> None:
        if self.current[0] != "home":
            self.back()
        else:
            self.sidebar.focus_search()

    def go_home(self) -> None:
        self.history.clear()
        self._show(("home", None), push=False)

    def back(self) -> None:
        if not self.history:
            self.go_home()
            return
        descriptor = self.history.pop()
        self.current = descriptor
        page = self._build_page(descriptor)
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        if hasattr(page, "on_show"):
            page.on_show()
        self._highlight_nav(descriptor)

    def open_tool(self, tool) -> None:
        self._show(("tool", tool))

    def open_category(self, category: str) -> None:
        self._show(("category", category))

    def open_nav(self, key: str) -> None:
        if key == "home":
            self.go_home()
        else:
            self._show((key, None))

    def open_settings(self) -> None:
        self._show(("settings", None))

    def open_dependencies(self) -> None:
        self._show(("deps", None))

    def refresh_sidebar(self) -> None:
        self.sidebar.rebuild_categories()

    # -- search ------------------------------------------------------------
    def on_search_typing(self, text: str) -> None:
        self._pending_query = text.strip()
        if len(self._pending_query) < 2:
            if self.current[0] == "search":
                self.go_home()
            return
        self._search_timer.start()

    def _run_search(self) -> None:
        query = getattr(self, "_pending_query", "")
        if len(query) < 2:
            return
        self.open_search(query, focus=False)

    def on_search_enter(self) -> None:
        query = self.sidebar.search.text().strip()
        if not query:
            return
        results = registry.search(query, limit=6)
        if len(results) == 1:
            self.open_tool(results[0])
        else:
            self.open_search(query)

    def open_search(self, query: str, focus: bool = True) -> None:
        results = registry.search(query, limit=60)
        if focus:
            self.sidebar.search.setText(query)
        self._show(("search", (query, results)))

    # -- window state ------------------------------------------------------
    def closeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self.settings.set("window", {"w": self.width(), "h": self.height()})
        super().closeEvent(event)
