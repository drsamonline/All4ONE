"""Pages: home, category, search, the per-tool page, settings and dependencies."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core import APP_TAGLINE, deps, registry
from core.runner import RunResult, execute
from core.tool import BOOL, Tool

from . import icons
from .theme import icon_colour, palette
from .widgets import Card, Chip, Console, Divider, FieldEditor, heading, icon_button, icon_label


# --------------------------------------------------------------------------
# Base page
# --------------------------------------------------------------------------
class BasePage(QWidget):
    def __init__(self, app, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.app = app
        self.theme = app.theme

    def on_show(self) -> None:
        """Called every time the page becomes visible."""

    def rebuild_theme(self) -> None:
        self.theme = self.app.theme


def scrollable(inner: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    area.setWidget(inner)
    return area


# --------------------------------------------------------------------------
# Cards
# --------------------------------------------------------------------------
def tool_card(app, tool: Tool, width: int = 0) -> Card:
    theme = app.theme
    card = Card()
    card.setMinimumHeight(96)
    if width:
        card.setFixedWidth(width)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)

    top = QHBoxLayout()
    top.setSpacing(9)
    top.addWidget(icon_label(icons.category_icon(tool.category),
                             icon_colour(theme, "accent"), 17))
    name = QLabel(tool.name)
    name.setObjectName("CardTitle")
    top.addWidget(name, 1)
    ok, reason = registry.is_available(tool)
    if tool.destructive:
        top.addWidget(Chip("careful", "ChipWarn"))
    elif not ok:
        top.addWidget(Chip("needs setup", "ChipWarn"))
    layout.addLayout(top)

    summary = QLabel(tool.summary)
    summary.setObjectName("CardBody")
    summary.setWordWrap(True)
    summary.setMaximumHeight(46)
    layout.addWidget(summary)

    meta = QHBoxLayout()
    meta.setSpacing(6)
    meta.addWidget(Chip(tool.category))
    if tool.needs:
        meta.addWidget(Chip(" · ".join(tool.needs)))
    if tool.is_windows_only:
        meta.addWidget(Chip("Windows"))
    meta.addStretch(1)
    layout.addLayout(meta)

    card.clicked.connect(lambda: app.open_tool(tool))
    card.setToolTip(reason or tool.summary)
    return card


def category_card(app, category: str, count: int) -> Card:
    theme = app.theme
    card = Card()
    card.setMinimumHeight(104)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(7)

    top = QHBoxLayout()
    top.setSpacing(10)
    tile = QFrame()
    tile.setFixedSize(34, 34)
    tile.setStyleSheet(
        f"background:{palette(theme)['accent_soft']}; border-radius:9px;")
    tile_layout = QHBoxLayout(tile)
    tile_layout.setContentsMargins(0, 0, 0, 0)
    tile_layout.addWidget(icon_label(icons.category_icon(category),
                                     icon_colour(theme, "accent"), 18), 0, Qt.AlignCenter)
    top.addWidget(tile)
    title = QLabel(category)
    title.setObjectName("CardTitle")
    top.addWidget(title, 1)
    top.addWidget(Chip(f"{count}"))
    layout.addLayout(top)

    blurb = QLabel(registry.blurb(category))
    blurb.setObjectName("CardBody")
    blurb.setWordWrap(True)
    layout.addWidget(blurb)

    card.clicked.connect(lambda: app.open_category(category))
    return card


def stat_card(app, value: str, label: str, icon_name: str) -> QFrame:
    theme = app.theme
    frame = QFrame()
    frame.setObjectName("StatCard")
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(12)
    layout.addWidget(icon_label(icon_name, icon_colour(theme, "accent"), 20))
    column = QVBoxLayout()
    column.setSpacing(0)
    number = QLabel(value)
    number.setStyleSheet("font-size:19px; font-weight:700;")
    caption = QLabel(label)
    caption.setObjectName("Muted")
    column.addWidget(number)
    column.addWidget(caption)
    layout.addLayout(column)
    layout.addStretch(1)
    return frame


# --------------------------------------------------------------------------
# Home
# --------------------------------------------------------------------------
class HomePage(BasePage):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._built = False

    def on_show(self) -> None:
        self.theme = self.app.theme
        if self._built:
            self._refresh()
            return
        self._build()
        self._built = True

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(34, 26, 34, 34)
        layout.setSpacing(22)

        hero = QVBoxLayout()
        hero.setSpacing(6)
        title = heading("What do you need to do?")
        hero.addWidget(title)
        subtitle = QLabel(f"{APP_TAGLINE}  ·  every tool on its own page, no plugins to install.")
        subtitle.setObjectName("PageSubtitle")
        hero.addWidget(subtitle)

        self.search = QLineEdit()
        self.search.setObjectName("Search")
        self.search.setPlaceholderText("Search tools — try 'pdf', 'hash', 'rename', 'resize'…")
        self.search.setMinimumHeight(42)
        self.search.returnPressed.connect(self._on_search)
        self.search.textChanged.connect(self._on_typing)
        hero.addWidget(self.search)
        layout.addLayout(hero)

        stats = registry.stats()
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(stat_card(self.app, str(stats["tools"]), "tools", "grid"))
        row.addWidget(stat_card(self.app, str(stats["categories"]), "categories", "package"))
        row.addWidget(stat_card(self.app, str(stats["ready"]), "ready to run", "check"))
        row.addWidget(stat_card(self.app, "0", "plugins", "plug"))
        layout.addLayout(row)

        self.favourites_section = self._section(layout, "Favourites", "star")
        self.recent_section = self._section(layout, "Recently used", "clock")

        layout.addWidget(heading("Browse by category", "SectionTitle"))
        self.grid = QGridLayout()
        self.grid.setSpacing(12)
        counts = registry.counts()
        for index, category in enumerate(registry.CATEGORY_NAMES):
            self.grid.addWidget(category_card(self.app, category, counts[category]),
                                index // 4, index % 4)
        layout.addLayout(self.grid)
        layout.addStretch(1)

        outer.addWidget(scrollable(inner))
        self._inner_layout = layout
        self._refresh()

    def _section(self, layout: QVBoxLayout, title: str, icon_name: str) -> QVBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(icon_label(icon_name, icon_colour(self.theme, "muted"), 16))
        header.addWidget(heading(title, "SectionTitle"))
        header.addStretch(1)
        wrapper = QWidget()
        wrapper.setLayout(header)
        layout.addWidget(wrapper)
        holder = QVBoxLayout()
        holder.setSpacing(10)
        layout.addLayout(holder)
        return holder

    def _fill_strip(self, holder: QVBoxLayout, tools: list[Tool], empty: str) -> None:
        while holder.count():
            item = holder.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not tools:
            label = QLabel(empty)
            label.setObjectName("Muted")
            holder.addWidget(label)
            return
        strip = QHBoxLayout()
        strip.setSpacing(12)
        for tool in tools[:3]:
            strip.addWidget(tool_card(self.app, tool), 1)
        holder.addLayout(strip)

    def _refresh(self) -> None:
        favourites = [registry.get(tool_id) for tool_id in self.app.settings.get("favourites", [])]
        favourites = [tool for tool in favourites if tool]
        recents = [registry.get(tool_id) for tool_id in self.app.settings.get("recent", [])]
        recents = [tool for tool in recents if tool]
        self._fill_strip(self.favourites_section, favourites,
                         "Star a tool from its page and it will appear here.")
        self._fill_strip(self.recent_section, recents,
                         "Tools you run will show up here.")

    def _on_typing(self, text: str) -> None:
        if len(text.strip()) >= 2:
            self.app.open_search(text, focus=False)

    def _on_search(self) -> None:
        text = self.search.text().strip()
        if not text:
            return
        results = registry.search(text, limit=5)
        if len(results) == 1:
            self.app.open_tool(results[0])
        else:
            self.app.open_search(text)


# --------------------------------------------------------------------------
# Category and search results
# --------------------------------------------------------------------------
class ToolListPage(BasePage):
    """Shared layout for a category listing and search results."""

    def __init__(self, app, title: str, subtitle: str, tools: list[Tool]) -> None:
        super().__init__(app)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        inner = QWidget()
        body = QVBoxLayout(inner)
        body.setContentsMargins(34, 20, 34, 34)
        body.setSpacing(16)

        header = QHBoxLayout()
        column = QVBoxLayout()
        column.setSpacing(4)
        column.addWidget(heading(title))
        caption = QLabel(subtitle)
        caption.setObjectName("PageSubtitle")
        caption.setWordWrap(True)
        column.addWidget(caption)
        header.addLayout(column, 1)
        body.addLayout(header)

        grid = QGridLayout()
        grid.setSpacing(12)
        for index, tool in enumerate(tools):
            grid.addWidget(tool_card(self.app, tool), index // 2, index % 2)
        if not tools:
            empty = QLabel("Nothing here yet.")
            empty.setObjectName("Muted")
            grid.addWidget(empty, 0, 0)
        body.addLayout(grid)
        body.addStretch(1)
        layout.addWidget(scrollable(inner))


# --------------------------------------------------------------------------
# The per-tool page
# --------------------------------------------------------------------------
class ToolWorker(QObject):
    line = Signal(str)
    finished = Signal(object)

    def __init__(self, tool: Tool, values: dict[str, Any]) -> None:
        super().__init__()
        self.tool = tool
        self.values = values
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def run(self) -> None:
        result = execute(self.tool, self.values, sink=self.line.emit,
                         cancelled=self._cancel.is_set)
        self.finished.emit(result)


class ToolPage(BasePage):
    def __init__(self, app, tool: Tool) -> None:
        super().__init__(app)
        self.tool = tool
        self.editors: dict[str, FieldEditor] = {}
        self.thread: QThread | None = None
        self.worker: ToolWorker | None = None
        self.outputs: list[str] = []
        self._build()

    # -- construction ------------------------------------------------------
    def _build(self) -> None:
        theme = self.theme
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(28, 18, 28, 22)
        layout.setSpacing(16)

        # header
        header = QHBoxLayout()
        header.setSpacing(14)
        back = icon_button("arrow-left", "Back", theme)
        back.clicked.connect(self.app.back)
        header.addWidget(back, 0, Qt.AlignTop)

        tile = QFrame()
        tile.setFixedSize(46, 46)
        tile.setStyleSheet(f"background:{palette(theme)['accent_soft']}; border-radius:12px;")
        tile_layout = QHBoxLayout(tile)
        tile_layout.setContentsMargins(0, 0, 0, 0)
        tile_layout.addWidget(icon_label(icons.category_icon(self.tool.category),
                                         icon_colour(theme, "accent"), 24), 0, Qt.AlignCenter)
        header.addWidget(tile, 0, Qt.AlignTop)

        column = QVBoxLayout()
        column.setSpacing(4)
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.addWidget(heading(self.tool.name))
        title_row.addWidget(Chip(self.tool.category, "ChipAccent"))
        ok, reason = registry.is_available(self.tool)
        if ok:
            title_row.addWidget(Chip("ready", "ChipOk"))
        else:
            title_row.addWidget(Chip("needs setup", "ChipWarn"))
        if self.tool.destructive:
            title_row.addWidget(Chip("changes data", "ChipDanger"))
        title_row.addStretch(1)
        column.addLayout(title_row)

        summary = QLabel(self.tool.summary)
        summary.setObjectName("ToolSummary")
        summary.setWordWrap(True)
        column.addWidget(summary)

        if not ok and reason:
            hint = QLabel(f"  {reason}")
            hint.setObjectName("FieldHelp")
            hint.setWordWrap(True)
            column.addWidget(hint)
        header.addLayout(column, 1)

        star = icon_button("star" if not self.app.settings.is_favourite(self.tool.id) else "star",
                           "Favourite", theme, 18)
        if self.app.settings.is_favourite(self.tool.id):
            star.setStyleSheet(f"color:{palette(theme)['warn']};")
            star.setIcon(icons.icon("star", palette(theme)["warn"], 18))
        self.star_button = star

        def toggle_favourite() -> None:
            on = self.app.settings.toggle_favourite(self.tool.id)
            star.setIcon(icons.icon("star", palette(theme)["warn"] if on
                                    else icon_colour(theme, "text_dim"), 18))
            self.app.refresh_sidebar()

        star.clicked.connect(toggle_favourite)
        header.addWidget(star, 0, Qt.AlignTop)
        layout.addLayout(header)

        layout.addWidget(Divider())

        # body: options | console
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(10)

        splitter.addWidget(self._options_panel())
        splitter.addWidget(self._console_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([430, 620])
        layout.addWidget(splitter, 1)

        root.addWidget(inner)

        run_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        run_shortcut.activated.connect(self.run_tool)
        run_shortcut2 = QShortcut(QKeySequence("Ctrl+Enter"), self)
        run_shortcut2.activated.connect(self.run_tool)

    def _options_panel(self) -> QWidget:
        theme = self.theme
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setMinimumWidth(360)
        panel.setMaximumWidth(560)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        header = QHBoxLayout()
        header.addWidget(heading("Options", "SectionTitle"))
        header.addStretch(1)
        if self.tool.fields:
            reset = QPushButton("Reset")
            reset.setObjectName("Ghost")
            reset.setCursor(QCursor(Qt.PointingHandCursor))
            reset.clicked.connect(self.reset_values)
            header.addWidget(reset)
        layout.addLayout(header)

        form_host = QWidget()
        self.form = QVBoxLayout(form_host)
        self.form.setContentsMargins(0, 0, 6, 0)
        self.form.setSpacing(14)

        if not self.tool.fields:
            note = QLabel("This tool takes no options — just run it.")
            note.setObjectName("Muted")
            self.form.addWidget(note)

        for field in self.tool.fields:
            editor = FieldEditor(field, theme)
            editor.changed.connect(self._update_command_preview)
            self.editors[field.key] = editor
            self.form.addWidget(editor)

        for field in self.tool.fields:
            if field.show_if:
                trigger = self.editors.get(field.show_if)
                if trigger is not None:
                    self._bind_visibility(field, trigger)

        self.form.addStretch(1)
        layout.addWidget(scrollable(form_host), 1)

        layout.addWidget(Divider())

        self.command_preview = QLabel()
        self.command_preview.setObjectName("FieldHelp")
        self.command_preview.setWordWrap(True)
        self.command_preview.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.command_preview)
        self._update_command_preview()

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.run_button = QPushButton("  Run")
        self.run_button.setObjectName("Primary")
        self.run_button.setIcon(icons.icon("play", "#ffffff", 14))
        self.run_button.setMinimumHeight(38)
        self.run_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.run_button.clicked.connect(self.run_tool)
        actions.addWidget(self.run_button, 1)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("Danger")
        self.stop_button.setMinimumHeight(38)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_tool)
        actions.addWidget(self.stop_button)
        layout.addLayout(actions)
        return panel

    def _console_panel(self) -> QWidget:
        theme = self.theme
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(heading("Output", "SectionTitle"))
        self.status = QLabel("Not run yet")
        self.status.setObjectName("Status")
        header.addWidget(self.status)
        header.addStretch(1)

        self.copy_button = icon_button("copy", "Copy output", theme)
        self.copy_button.clicked.connect(self.copy_output)
        self.save_button = icon_button("save", "Save output to a file", theme)
        self.save_button.clicked.connect(self.save_output)
        self.open_button = icon_button("external", "Open the produced file", theme)
        self.open_button.clicked.connect(self.open_output)
        self.open_button.setEnabled(False)
        clear = icon_button("trash", "Clear", theme)
        clear.clicked.connect(self.clear_output)
        for button in (self.copy_button, self.save_button, self.open_button, clear):
            header.addWidget(button)
        layout.addLayout(header)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(5)
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.console = Console(theme)
        self.console.setPlaceholderText("Output appears here as the tool runs.")
        self.console.progress_changed.connect(self._on_progress)
        self.console.output_found.connect(self._on_output)
        layout.addWidget(self.console, 1)

        self.console.write_header(
            f"{self.tool.name}  ·  {self.tool.id}\n"
            f"{self.tool.summary}\n"
            f"Equivalent command:  all4one run {self.tool.id} …")
        return panel

    # -- helpers -----------------------------------------------------------
    def _bind_visibility(self, field, trigger: FieldEditor) -> None:
        def update() -> None:
            self.editors[field.key].setVisible(bool(trigger.value()))
        trigger.changed.connect(update)
        update()

    def _update_command_preview(self) -> None:
        parts = [f"all4one run {self.tool.id}"]
        for field in self.tool.fields:
            editor = self.editors.get(field.key)
            if editor is None:
                continue
            value = editor.value()
            if field.kind == BOOL:
                if value:
                    parts.append(f"--{field.key}")
                continue
            text = "|".join(value) if isinstance(value, list) else str(value)
            if not text or text == str(field.default):
                continue
            if len(text) > 42:
                text = text[:39] + "…"
            parts.append(f'--{field.key} "{text}"')
        line = " ".join(parts)
        self.command_preview.setText(line if len(line) < 160 else line[:157] + "…")

    def reset_values(self) -> None:
        for field in self.tool.fields:
            self.editors[field.key].set_value(field.default_value())

    def collect(self) -> dict[str, Any]:
        return {key: editor.value() for key, editor in self.editors.items()}

    # -- running -----------------------------------------------------------
    def run_tool(self) -> None:
        if self.thread is not None:
            return
        values = self.collect()
        tool = self.tool.normalise(values)
        problems = self.tool.validate(tool)
        if problems:
            QMessageBox.warning(self, "Missing information", "\n".join(problems))
            return
        if self.tool.destructive and self.app.settings.get("confirm_destructive", True):
            answer = QMessageBox.question(
                self, "Confirm",
                f"{self.tool.name} can change or delete data.\n\nRun it now?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                return

        self.outputs = []
        self.open_button.setEnabled(False)
        self.console.clear()
        self.console.write_header(
            f"{self.tool.name}  ·  {self.tool.id}\n{self.tool.summary}\n")
        self.progress.show()
        self.progress.setValue(0)
        self.status.setText("Running…")
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.thread = QThread()
        self.worker = ToolWorker(self.tool, values)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.line.connect(self.console.append_line)
        self.worker.finished.connect(self._on_finished)
        self.thread.start()
        self.app.settings.push_recent(self.tool.id)

    def stop_tool(self) -> None:
        if self.worker is not None:
            self.worker.cancel()
            self.status.setText("Stopping…")

    def _on_progress(self, value: int, note: str) -> None:
        self.progress.setValue(value)
        if note:
            self.status.setText(note)

    def _on_output(self, path: str) -> None:
        if path not in self.outputs:
            self.outputs.append(path)
        self.open_button.setEnabled(True)

    def _on_finished(self, result: RunResult) -> None:
        if self.thread is not None:
            self.thread.quit()
            self.thread.wait(3000)
            self.thread.deleteLater()
            self.thread = None
            self.worker = None
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress.hide()
        if result.cancelled:
            self.status.setText(f"Stopped after {result.seconds:.1f}s")
        elif result.ok:
            self.status.setText(f"Done in {result.seconds:.2f}s")
        else:
            self.status.setText(f"Failed — {result.error[:60]}")
        if result.outputs:
            self.outputs = list(result.outputs)
            self.open_button.setEnabled(True)

    # -- output actions ----------------------------------------------------
    def copy_output(self) -> None:
        QGuiApplication.clipboard().setText(self.console.toPlainText())
        self.status.setText("Output copied")

    def save_output(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        text = self.console.toPlainText()
        if not text.strip():
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save output",
                                             str(Path.home() / f"{self.tool.id}-output.txt"),
                                             "Text (*.txt);;All files (*)")
        if not path:
            return
        Path(path).write_text(text, encoding="utf-8")
        self.status.setText(f"Saved to {Path(path).name}")

    def open_output(self) -> None:
        if not self.outputs:
            return
        target = self.outputs[-1]
        if self.app.settings.get("confirm_destructive", True) and not Path(target).exists():
            self.status.setText("The output file no longer exists")
            return
        import os
        import subprocess
        import sys
        try:
            if sys.platform == "win32":
                os.startfile(target)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.run(["open", target], check=False)
            else:
                subprocess.run(["xdg-open", target], check=False)
        except OSError as exc:
            self.status.setText(f"Could not open: {exc}")

    def clear_output(self) -> None:
        self.console.clear()
        self.status.setText("Cleared")


# --------------------------------------------------------------------------
# Settings and dependencies
# --------------------------------------------------------------------------
class SettingsPage(BasePage):
    def __init__(self, app) -> None:
        super().__init__(app)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        inner = QWidget()
        body = QVBoxLayout(inner)
        body.setContentsMargins(34, 24, 34, 34)
        body.setSpacing(16)

        body.addWidget(heading("Settings"))
        caption = QLabel("All4one stores nothing on your machine except this small preferences file.")
        caption.setObjectName("PageSubtitle")
        body.addWidget(caption)

        card = QFrame()
        card.setObjectName("Panel")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(14)

        theme_row = QHBoxLayout()
        theme_column = QVBoxLayout()
        theme_column.addWidget(QLabel("Appearance"))
        hint = QLabel("Dark suits long sessions; light suits printing and screenshots.")
        hint.setObjectName("FieldHelp")
        theme_column.addWidget(hint)
        theme_row.addLayout(theme_column, 1)
        self.theme_button = QPushButton()
        self.theme_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.theme_button.clicked.connect(self.app.toggle_theme)
        theme_row.addWidget(self.theme_button)
        card_layout.addLayout(theme_row)

        card_layout.addWidget(Divider())

        self.confirm_box = QCheckBox("Ask before a tool that changes or deletes data")
        self.confirm_box.setChecked(bool(self.app.settings.get("confirm_destructive", True)))
        self.confirm_box.toggled.connect(
            lambda state: self.app.settings.set("confirm_destructive", bool(state)))
        card_layout.addWidget(self.confirm_box)

        self.wrap_box = QCheckBox("Wrap long lines in the output console")
        self.wrap_box.setChecked(bool(self.app.settings.get("wrap_output", True)))
        self.wrap_box.toggled.connect(self._set_wrap)
        card_layout.addWidget(self.wrap_box)

        card_layout.addWidget(Divider())

        location = QLabel(f"Preferences file:  {self.app.settings.path}")
        location.setObjectName("FieldHelp")
        location.setWordWrap(True)
        location.setTextInteractionFlags(Qt.TextSelectableByMouse)
        card_layout.addWidget(location)

        buttons = QHBoxLayout()
        open_folder = QPushButton("Open settings folder")
        open_folder.clicked.connect(self._open_folder)
        buttons.addWidget(open_folder)
        clear_recents = QPushButton("Clear recent history")
        clear_recents.clicked.connect(self._clear_recents)
        buttons.addWidget(clear_recents)
        buttons.addStretch(1)
        card_layout.addLayout(buttons)

        body.addWidget(card)
        body.addStretch(1)
        layout.addWidget(scrollable(inner))

    def on_show(self) -> None:
        self.theme = self.app.theme
        self.theme_button.setText(
            "Switch to light" if self.app.theme == "dark" else "Switch to dark")

    def _set_wrap(self, state: bool) -> None:
        self.app.settings.set("wrap_output", bool(state))

    def _open_folder(self) -> None:
        import os
        import subprocess
        import sys
        folder = str(self.app.settings.path.parent)
        Path(folder).mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(folder)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.run(["open", folder], check=False)
            else:
                subprocess.run(["xdg-open", folder], check=False)
        except OSError:
            pass

    def _clear_recents(self) -> None:
        self.app.settings.set("recent", [])
        self.app.refresh_sidebar()


class DependenciesPage(BasePage):
    def __init__(self, app) -> None:
        super().__init__(app)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        inner = QWidget()
        body = QVBoxLayout(inner)
        body.setContentsMargins(34, 24, 34, 34)
        body.setSpacing(14)

        body.addWidget(heading("Optional dependencies"))
        caption = QLabel("All4one runs on the Python standard library alone. These extras unlock "
                         "the tools that use them — nothing else is affected.")
        caption.setObjectName("PageSubtitle")
        caption.setWordWrap(True)
        body.addWidget(caption)

        header = QHBoxLayout()
        header.addStretch(1)
        refresh = QPushButton("  Re-check")
        refresh.setIcon(icons.icon("refresh", icon_colour(app.theme, "text_dim"), 14))
        refresh.clicked.connect(self._refresh)
        header.addWidget(refresh)
        body.addLayout(header)

        self.holder = QVBoxLayout()
        self.holder.setSpacing(8)
        body.addLayout(self.holder)
        body.addStretch(1)
        layout.addWidget(scrollable(inner))
        self._populate()

    def on_show(self) -> None:
        self.theme = self.app.theme
        self._populate()

    def _refresh(self) -> None:
        deps.refresh()
        self._populate()

    def _populate(self) -> None:
        while self.holder.count():
            item = self.holder.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        theme = self.app.theme
        for row in deps.status():
            card = QFrame()
            card.setObjectName("Card")
            line = QHBoxLayout(card)
            line.setContentsMargins(16, 12, 16, 12)
            line.setSpacing(12)
            line.addWidget(icon_label("check" if row["available"] else "alert",
                                      icon_colour(theme, "ok" if row["available"] else "warn"), 16))
            column = QVBoxLayout()
            column.setSpacing(2)
            name = QLabel(row["label"])
            name.setStyleSheet("font-weight:600;")
            column.addWidget(name)
            detail = QLabel(row["hint"] if not row["available"] else "Installed and ready")
            detail.setObjectName("FieldHelp")
            detail.setWordWrap(True)
            column.addWidget(detail)
            line.addLayout(column, 1)
            line.addWidget(Chip("ready", "ChipOk") if row["available"]
                           else Chip("missing", "ChipWarn"))
            self.holder.addWidget(card)
