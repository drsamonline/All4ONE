"""Reusable widgets: cards, chips, option editors, the output console."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.tool import (
    BOOL,
    CHOICE,
    COLOR,
    DIR,
    FILE,
    FILES,
    FLOAT,
    INT,
    MULTI,
    PASSWORD,
    SAVE,
    SLIDER,
    Field,
)

from . import icons
from .theme import icon_colour


# --------------------------------------------------------------------------
# Small building blocks
# --------------------------------------------------------------------------
class Card(QFrame):
    """A clickable surface used for tools and categories."""

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None, hoverable: bool = True) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setCursor(QCursor(Qt.PointingHandCursor) if hoverable else Qt.ArrowCursor)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt naming
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class Chip(QLabel):
    def __init__(self, text: str, kind: str = "Chip", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName(kind)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)


class Divider(QFrame):
    def __init__(self, parent: QWidget | None = None, name: str = "Divider") -> None:
        super().__init__(parent)
        self.setObjectName(name)
        self.setFrameShape(QFrame.NoFrame)


def icon_label(name: str, colour: str, size: int = 20) -> QLabel:
    label = QLabel()
    label.setPixmap(icons.pixmap(name, colour, size))
    label.setFixedSize(size, size)
    return label


def icon_button(name: str, tooltip: str, theme: str, size: int = 16) -> QPushButton:
    button = QPushButton()
    button.setObjectName("Ghost")
    button.setIcon(icons.icon(name, icon_colour(theme, "text_dim"), size))
    button.setIconSize(QSize(size, size))
    button.setToolTip(tooltip)
    button.setFixedSize(30, 30)
    button.setCursor(QCursor(Qt.PointingHandCursor))
    return button


def heading(text: str, name: str = "PageTitle") -> QLabel:
    label = QLabel(text)
    label.setObjectName(name)
    return label


# --------------------------------------------------------------------------
# Path input with a browse button and drag-and-drop
# --------------------------------------------------------------------------
class PathPicker(QWidget):
    def __init__(self, field: Field, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.field = field
        self._drag_active = False
        self.setAcceptDrops(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.edit = QLineEdit()
        self.edit.setPlaceholderText(
            field.placeholder or ("Drop a file here, or click Browse" if field.kind != DIR
                                  else "Drop a folder here, or click Browse"))
        self.edit.setText(str(field.default or ""))
        layout.addWidget(self.edit, 1)

        self.button = QPushButton("Browse…")
        self.button.setCursor(QCursor(Qt.PointingHandCursor))
        self.button.clicked.connect(self.browse)
        layout.addWidget(self.button)

    # -- behaviour ---------------------------------------------------------
    def browse(self) -> None:
        start = self.edit.text().strip() or str(Path.home())
        if self.field.kind == DIR:
            chosen = QFileDialog.getExistingDirectory(self, "Choose a folder", start)
        elif self.field.kind == FILES:
            chosen, _ = QFileDialog.getOpenFileNames(self, "Choose files", start,
                                                     self.field.filters)
            chosen = "|".join(chosen)
        elif self.field.kind == SAVE:
            chosen, _ = QFileDialog.getSaveFileName(self, "Save as",
                                                    self.edit.text() or start,
                                                    self.field.filters)
        else:
            chosen, _ = QFileDialog.getOpenFileName(self, "Choose a file", start,
                                                    self.field.filters)
        if chosen:
            self.edit.setText(chosen)

    def value(self) -> str:
        return self.edit.text().strip()

    def set_value(self, value: Any) -> None:
        self.edit.setText(str(value or ""))

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._drag_active = True
            self.edit.setPlaceholderText("Release to use this path")

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._drag_active = False
        self.edit.setPlaceholderText(self.field.placeholder or "Drop a file here")

    def dropEvent(self, event) -> None:  # noqa: N802
        urls = event.mimeData().urls()
        if not urls:
            return
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if paths:
            self.edit.setText("|".join(paths) if self.field.kind == FILES else paths[0])
        self._drag_active = False
        event.acceptProposedAction()


# --------------------------------------------------------------------------
# One option on a tool page
# --------------------------------------------------------------------------
class FieldEditor(QWidget):
    """Renders a single :class:`Field` and can read its value back."""

    changed = Signal()

    def __init__(self, field: Field, theme: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.field = field
        self.theme = theme
        self._widgets: list[QWidget] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(5)

        if field.kind != BOOL:
            header = QHBoxLayout()
            header.setContentsMargins(0, 0, 0, 0)
            header.setSpacing(4)
            label = QLabel(field.label)
            label.setObjectName("FieldLabel")
            header.addWidget(label)
            if field.required:
                star = QLabel("*")
                star.setObjectName("Required")
                header.addWidget(star)
            header.addStretch(1)
            outer.addLayout(header)

        outer.addWidget(self._build())

        if field.help:
            hint = QLabel(field.help)
            hint.setObjectName("FieldHelp")
            hint.setWordWrap(True)
            outer.addWidget(hint)

    # -- construction ------------------------------------------------------
    def _build(self) -> QWidget:
        field = self.field
        kind = field.kind

        if kind in (FILE, FILES, DIR, SAVE):
            picker = PathPicker(field)
            picker.edit.textChanged.connect(self.changed)
            self._widgets.append(picker)
            return picker

        if kind == BOOL:
            box = QCheckBox(field.label)
            box.setChecked(bool(field.default))
            box.toggled.connect(self.changed)
            self._widgets.append(box)
            return box

        if kind == MULTI:
            editor = QPlainTextEdit()
            editor.setPlainText(str(field.default or ""))
            editor.setPlaceholderText(field.placeholder)
            editor.setFixedHeight(max(70, field.rows * 18))
            editor.textChanged.connect(self.changed)
            self._widgets.append(editor)
            return editor

        if kind == PASSWORD:
            editor = QLineEdit(str(field.default or ""))
            editor.setEchoMode(QLineEdit.Password)
            editor.setPlaceholderText(field.placeholder)
            editor.textChanged.connect(self.changed)
            self._widgets.append(editor)
            return editor

        if kind == CHOICE:
            combo = QComboBox()
            combo.addItems(list(field.choices))
            if field.default in field.choices:
                combo.setCurrentIndex(list(field.choices).index(field.default))
            combo.currentIndexChanged.connect(self.changed)
            self._widgets.append(combo)
            return combo

        if kind == INT:
            spin = QSpinBox()
            spin.setRange(int(field.minimum if field.minimum is not None else -2_000_000_000),
                          int(field.maximum if field.maximum is not None else 2_000_000_000))
            spin.setValue(int(field.default or 0))
            if field.suffix:
                spin.setSuffix(" " + field.suffix)
            spin.valueChanged.connect(self.changed)
            self._widgets.append(spin)
            return spin

        if kind == FLOAT:
            spin = QDoubleSpinBox()
            spin.setDecimals(3)
            spin.setRange(float(field.minimum if field.minimum is not None else -1e12),
                          float(field.maximum if field.maximum is not None else 1e12))
            if field.step:
                spin.setSingleStep(field.step)
            spin.setValue(float(field.default or 0))
            if field.suffix:
                spin.setSuffix(" " + field.suffix)
            spin.valueChanged.connect(self.changed)
            self._widgets.append(spin)
            return spin

        if kind == SLIDER:
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(int(field.minimum or 0), int(field.maximum or 100))
            slider.setValue(int(field.default or 0))
            readout = QLabel(str(int(field.default or 0)))
            readout.setObjectName("Muted")
            readout.setFixedWidth(46)
            slider.valueChanged.connect(lambda value: readout.setText(f"{value}{field.suffix}"))
            slider.valueChanged.connect(self.changed)
            layout.addWidget(slider, 1)
            layout.addWidget(readout)
            self._widgets.extend([row, slider])
            return row

        if kind == COLOR:
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)
            swatch = QPushButton()
            swatch.setFixedSize(46, 32)
            value = str(field.default or "#ffffff")
            swatch.setStyleSheet(f"background:{value}; border:1px solid #8884; border-radius:8px;")
            readout = QLineEdit(value)
            readout.setMaxLength(9)

            def choose() -> None:
                colour = QColorDialog.getColor(parent=self, title="Choose a colour")
                if colour.isValid():
                    hex_code = colour.name()
                    readout.setText(hex_code)
                    swatch.setStyleSheet(
                        f"background:{hex_code}; border:1px solid #8884; border-radius:8px;")

            def sync(text: str) -> None:
                swatch.setStyleSheet(f"background:{text}; border:1px solid #8884; border-radius:8px;")
                self.changed.emit()

            swatch.clicked.connect(choose)
            readout.textChanged.connect(sync)
            layout.addWidget(swatch)
            layout.addWidget(readout, 1)
            self._widgets.extend([row, readout])
            return row

        editor = QLineEdit(str(field.default or ""))
        editor.setPlaceholderText(field.placeholder)
        editor.textChanged.connect(self.changed)
        self._widgets.append(editor)
        return editor

    # -- value access ------------------------------------------------------
    def value(self) -> Any:
        field = self.field
        widget = self._widgets[0]
        if isinstance(widget, PathPicker):
            return widget.value()
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QPlainTextEdit):
            return widget.toPlainText()
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            return widget.value()
        if field.kind == SLIDER:
            return widget.findChild(QSlider).value() if widget.findChild(QSlider) else field.default
        if field.kind == COLOR:
            return self._widgets[1].text()
        if isinstance(widget, QLineEdit):
            return widget.text()
        return field.default

    def set_value(self, value: Any) -> None:
        widget = self._widgets[0]
        if isinstance(widget, PathPicker):
            widget.set_value(value)
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QPlainTextEdit):
            widget.setPlainText(str(value or ""))
        elif isinstance(widget, QComboBox):
            index = widget.findText(str(value))
            if index >= 0:
                widget.setCurrentIndex(index)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.setValue(type(widget.value())(value or 0))
        elif self.field.kind == SLIDER:
            slider = widget.findChild(QSlider)
            if slider:
                slider.setValue(int(value or 0))
        elif self.field.kind == COLOR:
            self._widgets[1].setText(str(value or "#ffffff"))
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value or ""))

    def focus_first(self) -> None:
        for widget in self._widgets:
            inner = widget
            if isinstance(widget, PathPicker):
                inner = widget.edit
            if isinstance(inner, (QLineEdit, QPlainTextEdit)):
                inner.setFocus()
                return


# --------------------------------------------------------------------------
# Output console
# --------------------------------------------------------------------------
class Console(QPlainTextEdit):
    """Streaming output. Control lines (\\x00progress:, \\x00output:) are consumed."""

    progress_changed = Signal(int, str)
    output_found = Signal(str)

    def __init__(self, theme: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Console")
        self.setReadOnly(True)
        self.setMaximumBlockCount(20000)
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.theme = theme

    def append_line(self, line: str) -> None:
        if line.startswith("\x00progress:"):
            _, _, rest = line.partition(":")
            value, _, note = rest.partition(":")
            try:
                self.progress_changed.emit(int(float(value)), note)
            except ValueError:
                pass
            return
        if line.startswith("\x00output:"):
            self.output_found.emit(line[len("\x00output:"):])
            return
        self.appendPlainText(line)
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())

    def write_header(self, text: str) -> None:
        self.appendPlainText(text)
        self.appendPlainText("─" * 60)
