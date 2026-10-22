import copy

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QMessageBox,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .storage import StorageError, Store
from .widgets import button, card, label


class SettingsPage(QScrollArea):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 12, 0, 12)
        appearance, area = card()
        area.addWidget(label(window.t("appearance"), "heading"))
        form = QFormLayout()
        self.language = QComboBox()
        self.language.addItem("فارسی", "fa")
        self.language.addItem("English", "en")
        self.language.setCurrentIndex(self.language.findData(window.language))
        self.theme = QComboBox()
        self.theme.addItem(window.t("ocean"), "ocean")
        self.theme.addItem(window.t("light"), "light")
        self.theme.setCurrentIndex(self.theme.findData(window.store.data["theme"]))
        self.size = QSpinBox()
        self.size.setRange(9, 16)
        self.size.setValue(window.store.data["font_size"])
        for key, control in (("language", self.language), ("theme", self.theme), ("font_size", self.size)):
            form.addRow(window.t(key), control)
        area.addLayout(form)
        layout.addWidget(appearance)
        privacy, area = card()
        area.addWidget(label(window.t("privacy"), "heading"))
        area.addWidget(label(window.t("privacy_copy"), "muted", True))
        self.online = QCheckBox(window.t("enable_events"))
        self.online.setChecked(window.store.data["online_events"])
        area.addWidget(self.online)
        area.addWidget(label(window.t("events_consent"), "muted", True))
        actions = QHBoxLayout()
        actions.addWidget(button(window.t("export"), "ph.export", self.export))
        actions.addWidget(button(window.t("import"), "ph.arrow-square-in", self.restore))
        area.addLayout(actions)
        area.addWidget(button(window.t("legacy"), "ph.notebook", self.import_legacy))
        area.addWidget(label(window.t("legacy_hint"), "muted", True))
        area.addWidget(button(window.t("purge_key"), "ph.key", self.purge_key))
        layout.addWidget(privacy)
        quotes, area = card()
        area.addWidget(label(window.t("quotes"), "heading"))
        self.quotes = QTextEdit()
        self.quotes.setAcceptRichText(False)
        self.quotes.setPlainText("\n".join(window.store.data["quotes"]))
        self.quotes.setMinimumHeight(110)
        area.addWidget(self.quotes)
        self.frequency = QComboBox()
        for key in ("daily", "hourly", "weekly"):
            self.frequency.addItem(window.t(key), key)
        self.frequency.setCurrentIndex(self.frequency.findData(window.store.data["quote_frequency"]))
        frequency_form = QFormLayout()
        frequency_form.addRow(window.t("frequency"), self.frequency)
        area.addLayout(frequency_form)
        layout.addWidget(quotes)
        layout.addWidget(button(window.t("apply"), "ph.check", self.apply, True))
        self.setWidget(content)

    def export(self):
        self.window.notes_page.collect()
        path, _ = QFileDialog.getSaveFileName(
            self, self.window.t("export"), "ShamsiCal-backup.json", "JSON (*.json)"
        )
        if not path:
            return
        try:
            # QFileDialog already confirms overwrites; write the export without touching live data.
            import json
            from pathlib import Path

            target = Path(path).resolve()
            if target in (
                self.window.store.path.resolve(),
                self.window.store.path.with_suffix(".json.bak").resolve(),
            ):
                raise StorageError("Active data file")
            target.write_text(
                json.dumps(self.window.store.data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            QMessageBox.information(self, self.window.t("done"), self.window.t("export"))
        except (OSError, StorageError):
            self.file_error()

    def restore(self):
        if self.window.jobs.pending:
            self.window.statusBar().showMessage(self.window.t("busy"))
            return
        path, _ = QFileDialog.getOpenFileName(self, self.window.t("import"), "", "JSON (*.json)")
        if not path:
            return
        try:
            replacement = Store.read(path)
        except StorageError:
            self.file_error()
            return
        if (
            QMessageBox.question(
                self,
                self.window.t("import"),
                self.window.t("restore_confirm"),
                defaultButton=QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        # Consent to online events is per installation, never inherited from an imported file.
        replacement["online_events"] = False
        previous = self.window.store.data
        self.window.store.data = replacement
        if self.window.persist(collect=False):
            self.window.rebuild()
        else:
            self.window.store.data = previous

    def import_legacy(self):
        if self.window.jobs.pending:
            self.window.statusBar().showMessage(self.window.t("busy"))
            return
        old = QSettings("MyCompany", "ShamsiCalendar")
        count = min(old.beginReadArray("note_tabs"), 500)
        imported = []
        for index in range(count):
            old.setArrayIndex(index)
            title, content = old.value("title", ""), old.value("content", "")
            if isinstance(title, str) and isinstance(content, str) and len(content) <= 1_000_000:
                note = {"title": title[:120] or self.window.t("new_note"), "html": content}
                if note not in self.window.store.data["notes"]:
                    imported.append(note)
        old.endArray()
        self.window.notes_page.collect()
        self.window.store.data["notes"].extend(imported)
        if imported:
            if not self.window.persist():
                del self.window.store.data["notes"][-len(imported) :]
                QMessageBox.warning(self, self.window.t("error"), self.window.t("save_error"))
                return
            self.window.rebuild()
        QMessageBox.information(
            self.window, self.window.t("done"), self.window.t("legacy_done" if imported else "legacy_empty")
        )

    def purge_key(self):
        old = QSettings("MyCompany", "ShamsiCalendar")
        old.remove("togetherai/api_token")
        old.sync()
        if old.status() != QSettings.Status.NoError:
            self.file_error()
        else:
            QMessageBox.information(self, self.window.t("done"), self.window.t("purge_done"))

    def apply(self):
        if self.window.jobs.pending:
            self.window.statusBar().showMessage(self.window.t("busy"))
            return
        self.window.notes_page.collect()
        previous = copy.deepcopy(self.window.store.data)
        self.window.store.data.update(
            {
                "language": self.language.currentData(),
                "theme": self.theme.currentData(),
                "font_size": self.size.value(),
                "online_events": self.online.isChecked(),
                "quotes": [
                    line.strip()[:1000] for line in self.quotes.toPlainText().splitlines() if line.strip()
                ][:500],
                "quote_frequency": self.frequency.currentData(),
            }
        )
        if self.window.persist():
            self.window.rebuild()
        else:
            self.window.store.data = previous

    def file_error(self):
        QMessageBox.warning(self, self.window.t("error"), self.window.t("file_error"))
