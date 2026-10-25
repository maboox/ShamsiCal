import os

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from . import network
from .widgets import button, label


class ReaderPage(QWidget):
    def __init__(self, window, compact=False):
        super().__init__()
        self.window = window
        self.items = []
        self.feeds = window.store.data["feeds"]
        self.busy = False
        self.generation = 0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        toolbar = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.setMinimumWidth(130 if compact else 180)
        self.combo.setAccessibleName(window.t("feeds"))
        self.combo.addItems([feed["name"] for feed in self.feeds])
        self.combo.currentIndexChanged.connect(self.clear)
        toolbar.addWidget(self.combo, 1)
        add = button(window.t("add_feed"), "ph.plus", self.add)
        remove = button(window.t("remove_feed"), "ph.trash", self.remove)
        toolbar.addWidget(add)
        toolbar.addWidget(remove)
        self.refresh_button = button(window.t("refresh"), "ph.arrow-clockwise", self.refresh, True)
        toolbar.addWidget(self.refresh_button)
        if compact:
            for control in (add, remove, self.refresh_button):
                control.setText("")
                control.setFixedWidth(34)
        layout.addLayout(toolbar)
        self.status = label(window.t("feed_hint"), "muted", True)
        layout.addWidget(self.status)
        body = QVBoxLayout() if compact else QHBoxLayout()
        self.list = QListWidget()
        self.list.setWordWrap(True)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setMinimumWidth(0 if compact else 240)
        if compact:
            self.list.setMaximumHeight(105)
        self.list.setAccessibleName(window.t("feeds"))
        self.list.currentRowChanged.connect(self.select)
        body.addWidget(self.list, 2)
        detail = QVBoxLayout()
        self.title = label(window.t("empty_feed"), "widgetTitle" if compact else "heading", True)
        if compact:
            self.title.setMaximumHeight(90)
        detail.addWidget(self.title)
        self.summary = label("", wrap=True)
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self.summary)
        detail.addWidget(scroll, 1)
        self.open_button = button(window.t("open_link"), "ph.arrow-square-out", self.open_link)
        self.ai_button = button(window.t("ai"), "ph.sparkle", self.ai)
        if compact:
            actions = QHBoxLayout()
            self.ai_button.setText("AI")
            actions.addWidget(self.open_button, 1)
            actions.addWidget(self.ai_button)
            detail.addLayout(actions)
        else:
            detail.addWidget(self.open_button)
            detail.addWidget(self.ai_button)
        body.addLayout(detail, 3)
        layout.addLayout(body, 1)
        self.clear()

    def clear(self, *_):
        self.generation += 1
        self.items = []
        self.list.clear()
        self.title.setText(self.window.t("empty_feed"))
        self.summary.setText("")
        self.status.setText(self.window.t("feed_hint"))
        self.open_button.setEnabled(False)
        self.ai_button.setEnabled(False)

    def add(self):
        name, ok = QInputDialog.getText(self, self.window.t("add_feed"), self.window.t("feed_name"))
        if not ok or not name.strip():
            return
        url, ok = QInputDialog.getText(self, self.window.t("add_feed"), self.window.t("feed_url"))
        if not ok:
            return
        try:
            url = network.safe_url(url)
        except network.NetworkError:
            QMessageBox.warning(self, self.window.t("error"), self.window.t("feed_url"))
            return
        self.feeds.append({"name": name.strip()[:120], "url": url})
        self.combo.addItem(name.strip()[:120])
        self.combo.setCurrentIndex(len(self.feeds) - 1)
        self.window.schedule_save()

    def remove(self):
        index = self.combo.currentIndex()
        if index >= 0:
            self.feeds.pop(index)
            self.combo.removeItem(index)
            self.clear()
            self.window.schedule_save()

    def refresh(self):
        index = self.combo.currentIndex()
        if self.busy or index < 0:
            return
        self.clear()
        generation = self.generation
        url = self.feeds[index]["url"]
        self.set_busy(True)
        self.status.setText(self.window.t("loading"))

        def complete(items, error):
            self.set_busy(False)
            if generation != self.generation:
                return
            if error:
                self.status.setText(self.window.t("feed_error"))
                return
            self.items = items
            self.list.addItems([item["title"] for item in items])
            self.status.setText(
                self.feeds[self.combo.currentIndex()]["name"] if items else self.window.t("no_items")
            )
            if items:
                self.list.setCurrentRow(0)

        self.window.jobs.submit(lambda: network.read_feed(url), complete)

    def set_busy(self, busy):
        self.busy = busy
        self.refresh_button.setEnabled(not busy)
        self.ai_button.setEnabled(not busy and self.list.currentRow() >= 0)

    def select(self, index):
        valid = 0 <= index < len(self.items)
        self.open_button.setEnabled(valid and bool(self.items[index]["link"]))
        self.ai_button.setEnabled(valid and not self.busy)
        if valid:
            self.title.setText(self.items[index]["title"])
            self.summary.setText(self.items[index]["summary"])

    def open_link(self):
        index = self.list.currentRow()
        if not self.busy and 0 <= index < len(self.items) and self.items[index]["link"]:
            try:
                url = network.safe_url(self.items[index]["link"])
            except network.NetworkError:
                return
            self.set_busy(True)
            self.open_button.setEnabled(False)

            def check_destination():
                from urllib.parse import urlsplit

                network.public_addresses(urlsplit(url).hostname)
                return url

            def complete(result, error):
                self.set_busy(False)
                self.select(self.list.currentRow())
                if error:
                    self.status.setText(self.window.t("feed_error"))
                else:
                    QDesktopServices.openUrl(QUrl(result))

            self.window.jobs.submit(check_destination, complete)

    def ai(self):
        index = self.list.currentRow()
        if self.busy or not 0 <= index < len(self.items):
            return
        if not os.environ.get("TOGETHER_API_KEY") or not os.environ.get("SHAMSICAL_AI_MODEL"):
            QMessageBox.information(self, self.window.t("ai"), self.window.t("ai_config"))
            return
        if (
            QMessageBox.question(
                self,
                self.window.t("ai"),
                self.window.t("ai_consent"),
                defaultButton=QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        text = self.items[index]["title"] + "\n" + self.items[index]["summary"]
        generation = self.generation
        self.set_busy(True)
        self.status.setText(self.window.t("loading"))

        def complete(result, error):
            self.set_busy(False)
            if generation != self.generation:
                return
            self.status.setText(self.window.t("ai_error") if error else self.window.t("ai_label"))
            if not error:
                # Display against the original article only, even if selection changed.
                if self.list.currentRow() == index:
                    self.summary.setText(result)

        self.window.jobs.submit(lambda: network.summarize(text), complete)
