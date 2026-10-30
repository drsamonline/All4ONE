"""Design tokens and the stylesheet.

One palette, two modes. Everything visual is expressed here as a token and
consumed by ``stylesheet()``, so the app has a single place to change its look.
"""

from __future__ import annotations

DARK = {
    "bg": "#0d1117",
    "bg_alt": "#0a0e14",
    "surface": "#141a22",
    "surface_2": "#1a222c",
    "surface_3": "#212b37",
    "border": "#232d3b",
    "border_soft": "#1b2430",
    "text": "#e6edf3",
    "text_dim": "#a9b6c6",
    "muted": "#78889b",
    "accent": "#6d8cff",
    "accent_hover": "#7f9bff",
    "accent_press": "#5a79e6",
    "accent_soft": "#1b2745",
    "ok": "#3fb950",
    "ok_soft": "#12281a",
    "warn": "#d29922",
    "warn_soft": "#2a2113",
    "danger": "#f85149",
    "danger_soft": "#2d1416",
    "console_bg": "#0a0e14",
    "console_text": "#c9d6e4",
    "shadow": "#000000",
}

LIGHT = {
    "bg": "#f6f7f9",
    "bg_alt": "#eceef2",
    "surface": "#ffffff",
    "surface_2": "#f4f6f9",
    "surface_3": "#e9edf3",
    "border": "#dde3ec",
    "border_soft": "#e8edf4",
    "text": "#101720",
    "text_dim": "#3d4a5c",
    "muted": "#68788c",
    "accent": "#4f6ef7",
    "accent_hover": "#4160ea",
    "accent_press": "#3752cc",
    "accent_soft": "#e8edff",
    "ok": "#1a7f37",
    "ok_soft": "#e6f5ea",
    "warn": "#9a6700",
    "warn_soft": "#fdf3dd",
    "danger": "#c62828",
    "danger_soft": "#fdeaea",
    "console_bg": "#0f141b",
    "console_text": "#d6e0ea",
    "shadow": "#c9d2de",
}


def palette(theme: str) -> dict[str, str]:
    return LIGHT if theme == "light" else DARK


def font_stack() -> str:
    return '"Segoe UI Variable Display", "Segoe UI", "Inter", "SF Pro Text", "Noto Sans", sans-serif'


def mono_stack() -> str:
    return '"Cascadia Mono", "JetBrains Mono", "Consolas", "DejaVu Sans Mono", monospace'


def stylesheet(theme: str) -> str:
    c = palette(theme)
    return f"""
* {{
    font-family: {font_stack()};
    font-size: 13px;
    color: {c['text']};
    outline: none;
}}
QWidget#Root {{ background: {c['bg']}; }}
QWidget#Sidebar {{ background: {c['bg_alt']}; border-right: 1px solid {c['border_soft']}; }}
QWidget#ContentArea {{ background: {c['bg']}; }}
QWidget#TopBar {{ background: {c['bg']}; }}

QLabel#Brand {{ font-size: 17px; font-weight: 700; letter-spacing: 0.2px; }}
QLabel#BrandSub {{ color: {c['muted']}; font-size: 11px; }}
QLabel#PageTitle {{ font-size: 24px; font-weight: 700; }}
QLabel#PageSubtitle {{ color: {c['muted']}; font-size: 13px; }}
QLabel#SectionTitle {{ font-size: 14px; font-weight: 600; }}
QLabel#FieldLabel {{ font-size: 12px; font-weight: 600; color: {c['text_dim']}; }}
QLabel#FieldHelp {{ font-size: 11px; color: {c['muted']}; }}
QLabel#Required {{ color: {c['danger']}; font-size: 12px; }}
QLabel#CardTitle {{ font-size: 14px; font-weight: 600; }}
QLabel#CardBody {{ color: {c['muted']}; font-size: 12px; }}
QLabel#Muted {{ color: {c['muted']}; }}
QLabel#ToolSummary {{ color: {c['text_dim']}; font-size: 13px; }}
QLabel#Status {{ color: {c['muted']}; font-size: 12px; }}

QFrame#Card {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 12px;
}}
QFrame#Card:hover {{ border-color: {c['accent']}; }}
QFrame#Panel {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 12px;
}}
QFrame#StatCard {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 12px;
}}
QFrame#Divider {{ background: {c['border_soft']}; max-height: 1px; border: none; }}
QFrame#SidebarDivider {{ background: {c['border_soft']}; max-height: 1px; border: none; }}

QLabel#Chip {{
    background: {c['surface_2']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 3px 9px;
    font-size: 11px;
    color: {c['text_dim']};
}}
QLabel#ChipAccent {{
    background: {c['accent_soft']};
    border: 1px solid {c['accent']};
    border-radius: 9px;
    padding: 3px 9px;
    font-size: 11px;
    color: {c['accent']};
}}
QLabel#ChipOk {{
    background: {c['ok_soft']};
    border: 1px solid {c['ok']};
    border-radius: 9px;
    padding: 3px 9px;
    font-size: 11px;
    color: {c['ok']};
}}
QLabel#ChipWarn {{
    background: {c['warn_soft']};
    border: 1px solid {c['warn']};
    border-radius: 9px;
    padding: 3px 9px;
    font-size: 11px;
    color: {c['warn']};
}}
QLabel#ChipDanger {{
    background: {c['danger_soft']};
    border: 1px solid {c['danger']};
    border-radius: 9px;
    padding: 3px 9px;
    font-size: 11px;
    color: {c['danger']};
}}

QPushButton {{
    background: {c['surface_2']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 7px 14px;
    font-size: 13px;
}}
QPushButton:hover {{ background: {c['surface_3']}; border-color: {c['accent']}; }}
QPushButton:pressed {{ background: {c['border']}; }}
QPushButton:disabled {{ color: {c['muted']}; border-color: {c['border_soft']}; }}

QPushButton#Primary {{
    background: {c['accent']};
    border: 1px solid {c['accent']};
    color: #ffffff;
    font-weight: 600;
    padding: 9px 20px;
}}
QPushButton#Primary:hover {{ background: {c['accent_hover']}; }}
QPushButton#Primary:pressed {{ background: {c['accent_press']}; }}
QPushButton#Primary:disabled {{ background: {c['surface_3']}; border-color: {c['border']};
                               color: {c['muted']}; }}

QPushButton#Ghost {{
    background: transparent;
    border: 1px solid transparent;
    color: {c['text_dim']};
    padding: 6px 10px;
}}
QPushButton#Ghost:hover {{ background: {c['surface_2']}; color: {c['text']}; }}

QPushButton#Danger {{
    background: {c['danger_soft']};
    border: 1px solid {c['danger']};
    color: {c['danger']};
    font-weight: 600;
}}
QPushButton#Danger:hover {{ background: {c['danger']}; color: #ffffff; }}

QPushButton#NavItem {{
    background: transparent;
    border: none;
    border-radius: 9px;
    padding: 9px 12px;
    text-align: left;
    color: {c['text_dim']};
    font-size: 13px;
}}
QPushButton#NavItem:hover {{ background: {c['surface_2']}; color: {c['text']}; }}
QPushButton#NavItem:checked {{
    background: {c['accent_soft']};
    color: {c['accent']};
    font-weight: 600;
}}
QPushButton#NavCount {{
    background: transparent; border: none; color: {c['muted']};
    font-size: 11px; padding: 0px;
}}

QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {c['surface_2']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 8px 10px;
    selection-background-color: {c['accent']};
    selection-color: #ffffff;
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:focus {{ border-color: {c['accent']}; }}
QLineEdit:disabled, QComboBox:disabled {{ color: {c['muted']}; }}
QLineEdit#Search {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    padding: 9px 12px;
}}
QLineEdit#Search:focus {{ border-color: {c['accent']}; }}

QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    selection-background-color: {c['accent_soft']};
    selection-color: {c['accent']};
    padding: 4px;
    outline: none;
}}
QCheckBox {{ spacing: 8px; color: {c['text']}; }}
QCheckBox::indicator {{
    width: 17px; height: 17px;
    border: 1px solid {c['border']};
    border-radius: 5px;
    background: {c['surface_2']};
}}
QCheckBox::indicator:checked {{
    background: {c['accent']};
    border-color: {c['accent']};
    image: none;
}}
QCheckBox::indicator:hover {{ border-color: {c['accent']}; }}

QSlider::groove:horizontal {{
    height: 4px; background: {c['surface_3']}; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {c['accent']}; width: 14px; height: 14px;
    margin: -5px 0; border-radius: 7px;
}}
QSlider::sub-page:horizontal {{ background: {c['accent']}; border-radius: 2px; }}

QProgressBar {{
    background: {c['surface_3']};
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{ background: {c['accent']}; border-radius: 3px; }}

QPlainTextEdit#Console {{
    background: {c['console_bg']};
    color: {c['console_text']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    font-family: {mono_stack()};
    font-size: 12px;
    padding: 12px;
}}

QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 10px; margin: 4px 2px 4px 0;
}}
QScrollBar::handle:vertical {{
    background: {c['surface_3']}; border-radius: 5px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; }}
QScrollBar::handle:horizontal {{ background: {c['surface_3']}; border-radius: 5px; min-width: 30px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QToolTip {{
    background: {c['surface_3']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 6px 8px;
}}
QSplitter::handle {{ background: transparent; width: 8px; }}
QTableWidget {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    gridline-color: {c['border_soft']};
    selection-background-color: {c['accent_soft']};
    selection-color: {c['text']};
}}
QHeaderView::section {{
    background: {c['surface_2']};
    border: none;
    border-bottom: 1px solid {c['border']};
    padding: 8px;
    font-weight: 600;
    color: {c['text_dim']};
}}
QMenu {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 6px;
}}
QMenu::item {{ padding: 7px 22px 7px 14px; border-radius: 6px; }}
QMenu::item:selected {{ background: {c['accent_soft']}; color: {c['accent']}; }}
"""


def icon_colour(theme: str, kind: str = "muted") -> str:
    c = palette(theme)
    return {"muted": c["muted"], "text": c["text"], "accent": c["accent"],
            "ok": c["ok"], "warn": c["warn"], "danger": c["danger"]}.get(kind, c["muted"])
