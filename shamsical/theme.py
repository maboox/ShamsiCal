"""Shared design tokens and consistent focus/disabled states."""

PALETTES = {
    "ocean": {
        "bg": "#0b1220",
        "panel": "#111e32",
        "raised": "#192a43",
        "border": "#2b4060",
        "text": "#edf4ff",
        "muted": "#a3b6d1",
        "accent": "#77b9ff",
        "selected": "#245dba",
        "hover": "#223957",
        "danger": "#ffb1bb",
    },
    "light": {
        "bg": "#edf3fb",
        "panel": "#ffffff",
        "raised": "#e9f1fc",
        "border": "#c6d6ec",
        "text": "#122b4a",
        "muted": "#4e6481",
        "accent": "#1c58b1",
        "selected": "#245dba",
        "hover": "#dce9fa",
        "danger": "#a01c38",
    },
}


def stylesheet(theme, size):
    p = PALETTES[theme]
    return f"""
    QWidget {{ color: {p["text"]}; font-size: {size}pt; }}
    QMainWindow, QDialog, QWidget#root {{ background: {p["bg"]}; }}
    QFrame#card {{ background: {p["panel"]}; border: 1px solid {p["border"]}; border-radius: 18px; }}
    QLabel {{ background: transparent; border: none; }}
    QLabel#muted {{ color: {p["muted"]}; font-size: {max(9, size - 1)}pt; }}
    QLabel#hero {{ font-size: {size + 30}pt; font-weight: 700; color: {p["accent"]}; }}
    QLabel#heading {{ font-size: {size + 7}pt; font-weight: 650; }}
    QLabel#brand {{ font-size: {size + 10}pt; font-weight: 700; }}
    QPushButton, QToolButton {{ background: {p["raised"]}; border: 1px solid transparent; border-radius: 9px; padding: 8px 12px; min-height: 22px; }}
    QPushButton:hover, QToolButton:hover {{ background: {p["hover"]}; }}
    QPushButton:focus, QToolButton:focus, QComboBox:focus, QTextEdit:focus, QLineEdit:focus, QSpinBox:focus, QListWidget:focus {{ border: 2px solid {p["accent"]}; }}
    QPushButton:disabled, QToolButton:disabled {{ color: {p["muted"]}; background: {p["panel"]}; }}
    QPushButton#primary {{ background: {p["selected"]}; color: white; }}
    QPushButton#primary:hover {{ background: #3475d4; }}
    QPushButton#day {{ background: transparent; min-width: 34px; min-height: 37px; padding: 4px; border-radius: 10px; }}
    QPushButton#day:hover {{ background: {p["hover"]}; }}
    QPushButton#day[friday="true"] {{ color: {p["danger"]}; }}
    QPushButton#day[today="true"] {{ border: 1px solid {p["accent"]}; }}
    QPushButton#day:checked {{ background: {p["selected"]}; color: white; border: 1px solid {p["accent"]}; }}
    QTabWidget::pane {{ border: none; background: transparent; }}
    QTabBar::tab {{ color: {p["muted"]}; background: transparent; padding: 12px 22px; border-bottom: 2px solid transparent; }}
    QTabBar::tab:selected {{ color: {p["accent"]}; border-bottom: 2px solid {p["accent"]}; }}
    QTabBar::tab:hover {{ background: {p["raised"]}; }}
    QTextEdit, QLineEdit, QListWidget, QComboBox, QSpinBox {{ background: {p["panel"]}; border: 1px solid {p["border"]}; border-radius: 10px; padding: 9px; selection-background-color: {p["selected"]}; selection-color: white; }}
    QListWidget::item {{ padding: 12px; border-bottom: 1px solid {p["border"]}; }}
    QListWidget::item:selected {{ background: {p["selected"]}; color: white; border-radius: 6px; }}
    QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
    QScrollBar:vertical {{ background: {p["bg"]}; width: 10px; }}
    QScrollBar::handle:vertical {{ background: {p["border"]}; min-height: 32px; border-radius: 5px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    QCheckBox {{ padding: 8px 0; spacing: 10px; }}
    QCheckBox::indicator {{ width: 20px; height: 20px; }}
    QStatusBar {{ background: {p["bg"]}; color: {p["muted"]}; border-top: 1px solid {p["border"]}; }}
    QToolTip {{ background: {p["raised"]}; color: {p["text"]}; border: 1px solid {p["border"]}; padding: 6px; }}
    """
