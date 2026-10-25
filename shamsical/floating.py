"""Independent desktop tool windows with drag handles and retained geometry."""

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QHBoxLayout, QSizeGrip, QVBoxLayout, QWidget

from .theme import PALETTES
from .widgets import button, label


class StatusLabel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.text = label("", "muted", True)
        layout.addWidget(self.text)

    def showMessage(self, message, *_):
        self.text.setText(message)

    def currentMessage(self):
        return self.text.text()


class DragHandle(QWidget):
    def __init__(self, panel):
        super().__init__(panel)
        self.panel = panel
        self.anchor = None
        self.origin = None
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.anchor = event.globalPosition().toPoint()
            self.origin = self.panel.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.anchor is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.panel.move(self.origin + event.globalPosition().toPoint() - self.anchor)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.anchor = self.origin = None
            self.panel.owner.remember_panel(self.panel)
            event.accept()


class FloatingPanel(QWidget):
    def __init__(self, owner, key, title):
        # No QWidget parent: hiding the calendar must not hide the other widgets.
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.owner, self.key = owner, key
        self.setWindowTitle(f"ShamsiCal · {title}")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("desktopWidget")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 10, 16, 10)
        outer.setSpacing(7)
        self.handle = DragHandle(self)
        self.handle.setToolTip(owner.t("drag_widget"))
        header = QHBoxLayout(self.handle)
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(3)
        self.title_label = label(title, "muted")
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        header.addWidget(self.title_label, 1)
        self.menu_button = self.icon_button(owner.t("widget_menu"), "ph.dots-three", self.open_menu)
        self.hide_button = self.icon_button(owner.t("hide_widget"), "ph.x", lambda: owner.hide_panel(key))
        header.addWidget(self.menu_button)
        header.addWidget(self.hide_button)
        outer.addWidget(self.handle)
        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(8)
        outer.addLayout(self.body, 1)
        footer = QHBoxLayout()
        self.status = StatusLabel()
        footer.addWidget(self.status, 1)
        self.grip = QSizeGrip(self)
        self.grip.setFixedSize(13, 13)
        footer.addWidget(self.grip)
        outer.addLayout(footer)

    @staticmethod
    def icon_button(title, icon, callback):
        control = button(title, icon, callback)
        control.setText("")
        control.setObjectName("widgetIcon")
        control.setFixedSize(30, 28)
        return control

    def set_content(self, widget):
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        self.body.addWidget(widget)

    def paintEvent(self, event):
        if self.owner.store.data["widget_background"]:
            colors = PALETTES[self.owner.store.data["theme"]]
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor(colors["panel"]))
            painter.setPen(QPen(QColor(colors["border"]), 1))
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 15, 15)

    def open_menu(self):
        menu = self.owner.create_menu(self)
        menu.exec(self.menu_button.mapToGlobal(QPoint(0, self.menu_button.height())))
        menu.deleteLater()

    def contextMenuEvent(self, event):
        menu = self.owner.create_menu(self)
        menu.exec(event.globalPos())
        menu.deleteLater()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.owner.remember_panel(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.owner.remember_panel(self)

    def closeEvent(self, event):
        if not self.owner.quitting:
            self.owner.hide_panel(self.key)
        event.accept()
