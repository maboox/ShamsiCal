"""Small reusable Qt controls; remote rich-text resources are blocked."""

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QTextCursor, QTextDocument
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QTextEdit, QVBoxLayout

from . import icons as qta


def label(text="", name="", wrap=False):
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setObjectName(name)
    widget.setWordWrap(wrap)
    return widget


def button(text, icon="", callback=None, primary=False):
    widget = QPushButton(text)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.setAccessibleName(text)
    widget.setToolTip(text)
    if icon:
        widget.setProperty("iconName", icon)
        widget.setIcon(qta.icon(icon, color="#77b9ff" if not primary else "white"))
    if primary:
        widget.setObjectName("primary")
    if callback:
        widget.clicked.connect(callback)
    return widget


def card():
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(14)
    return frame, layout


class PrivateDocument(QTextDocument):
    def loadResource(self, resource_type, name):
        # No remote tracking images or local-file disclosure via pasted/imported HTML.
        return None


class DayButton(QPushButton):
    """Two calendar dates with a clear primary/secondary type hierarchy."""

    def __init__(self):
        super().__init__()
        self.primary = self.secondary = ""
        self.setObjectName("day")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(47)
        self.colors = {}

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.primary:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        main = (
            "white"
            if self.isChecked()
            else self.colors.get("danger" if self.property("friday") else "text", "white")
        )
        sub = "#edf4ff" if self.isChecked() else self.colors.get("muted", "#a3b6d1")
        painter.setPen(QColor(main))
        font = QFont(self.font())
        font.setPointSize(max(12, self.font().pointSize() + 1))
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, 2, self.width(), self.height() * 0.56), Qt.AlignmentFlag.AlignCenter, self.primary
        )
        font.setPointSize(max(8, self.font().pointSize() - 3))
        font.setWeight(QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QColor(sub))
        painter.drawText(
            QRectF(0, self.height() * 0.53, self.width(), self.height() * 0.42),
            Qt.AlignmentFlag.AlignCenter,
            self.secondary,
        )


class NoteEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocument(PrivateDocument(self))
        self.setAcceptDrops(False)

    def insertFromMimeData(self, source):
        if source.hasText():
            # Keep external paste predictable; formatting remains available in the toolbar.
            self.textCursor().insertText(source.text())

    def checklist(self):
        cursor = self.textCursor()
        block = cursor.block()
        text = block.text()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        if text.startswith(("☐ ", "☑ ")):
            cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText("☑" if text.startswith("☐") else "☐")
        else:
            cursor.insertText("☐ ")
        cursor.endEditBlock()
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()
            text = cursor.block().text()
            if text.startswith(("☐ ", "☑ ")):
                if text.strip() in ("☐", "☑"):
                    cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                    cursor.removeSelectedText()
                else:
                    cursor.insertBlock()
                    cursor.insertText("☐ ")
                self.setTextCursor(cursor)
                return
        super().keyPressEvent(event)
