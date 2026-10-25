from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCharFormat
from PyQt6.QtWidgets import QHBoxLayout, QInputDialog, QListWidget, QMessageBox, QVBoxLayout, QWidget

from .widgets import NoteEdit, button, label


class NotesPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.current = -1
        self.loading = False
        self.notes = window.store.data["notes"]
        if not self.notes:
            self.notes.append({"title": window.t("new_note"), "html": ""})
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        side = QVBoxLayout()
        side.addWidget(button(window.t("new_note"), "ph.plus", self.add_note, True))
        self.list = QListWidget()
        self.list.setMinimumWidth(110)
        self.list.setMaximumWidth(180)
        self.list.setAccessibleName(window.t("notes"))
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side.addWidget(self.list)
        side.addWidget(button(window.t("rename"), "ph.pencil-simple", self.rename))
        side.addWidget(button(window.t("delete"), "ph.trash", self.delete))
        layout.addLayout(side, 1)
        content = QVBoxLayout()
        toolbar = QHBoxLayout()
        for key, icon, callback in (
            ("bold", "ph.text-bolder", lambda: self.format("bold")),
            ("italic", "ph.text-italic", lambda: self.format("italic")),
            ("checklist", "ph.check-square", lambda: self.editor.checklist()),
        ):
            control = button(window.t(key), icon, callback)
            control.setText("")
            control.setFixedWidth(38)
            toolbar.addWidget(control)
        toolbar.addStretch()
        content.addLayout(toolbar)
        self.editor = NoteEdit()
        self.editor.setPlaceholderText(window.t("placeholder"))
        self.editor.setAccessibleName(window.t("notes"))
        content.addWidget(self.editor, 1)
        content.addWidget(label(window.t("saved"), "muted"))
        layout.addLayout(content, 3)
        self.list.addItems([note["title"] for note in self.notes])
        self.list.currentRowChanged.connect(self.select)
        self.list.itemDoubleClicked.connect(self.rename)
        self.editor.textChanged.connect(self.changed)
        self.list.setCurrentRow(0)

    def collect(self):
        if 0 <= self.current < len(self.notes) and not self.loading:
            self.notes[self.current]["html"] = self.editor.toHtml()

    def changed(self):
        if not self.loading:
            self.collect()
            self.window.schedule_save()

    def select(self, index):
        self.collect()
        self.current = index
        self.loading = True
        self.editor.setHtml(self.notes[index]["html"] if 0 <= index < len(self.notes) else "")
        self.loading = False

    def add_note(self):
        self.collect()
        title = self.window.t("new_note")
        self.notes.append({"title": title, "html": ""})
        self.list.addItem(title)
        self.list.setCurrentRow(len(self.notes) - 1)
        self.editor.setFocus()
        self.window.schedule_save()

    def rename(self, *_):
        if self.current < 0:
            return
        title, ok = QInputDialog.getText(
            self, self.window.t("rename"), self.window.t("note_title"), text=self.notes[self.current]["title"]
        )
        if ok and title.strip():
            self.notes[self.current]["title"] = title.strip()[:120]
            self.list.item(self.current).setText(title.strip()[:120])
            self.window.schedule_save()

    def delete(self):
        if (
            self.current < 0
            or QMessageBox.question(
                self,
                self.window.t("delete"),
                self.window.t("delete_note"),
                defaultButton=QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        index = self.current
        self.current = -1
        self.list.blockSignals(True)
        self.list.takeItem(index)
        self.notes.pop(index)
        self.list.blockSignals(False)
        if not self.notes:
            self.add_note()
        else:
            target = min(index, len(self.notes) - 1)
            self.list.setCurrentRow(target)
            self.select(target)
        self.window.schedule_save()

    def format(self, kind):
        fmt = QTextCharFormat()
        if kind == "bold":
            fmt.setFontWeight(
                QFont.Weight.Normal if self.editor.fontWeight() >= QFont.Weight.Bold else QFont.Weight.Bold
            )
        else:
            fmt.setFontItalic(not self.editor.fontItalic())
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()
