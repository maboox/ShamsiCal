"""Application composition, calendar view, and lifecycle."""

import argparse
import sys
import time
from pathlib import Path

import jdatetime
from PyQt6.QtCore import QByteArray, QLockFile, QStandardPaths, Qt, QTimer
from PyQt6.QtGui import QFont, QFontDatabase, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from . import __version__, calendar, network
from . import icons as qta
from .i18n import tr
from .jobs import Jobs
from .notes import NotesPage
from .reader import ReaderPage
from .settings import SettingsPage
from .storage import StorageError, Store
from .theme import PALETTES, stylesheet
from .widgets import DayButton, button, card, label


class Window(QMainWindow):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.day = calendar.today()
        self.last_today = self.day
        self.jobs = Jobs(self)
        self.event_busy = False
        self.save_failed = False
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(500)
        self.save_timer.timeout.connect(self.persist)
        self.event_timer = QTimer(self)
        self.event_timer.setSingleShot(True)
        self.event_timer.setInterval(250)
        self.event_timer.timeout.connect(self.load_events)
        self.clock = QTimer(self)
        self.clock.setInterval(30_000)
        self.clock.timeout.connect(self.tick)
        self.clock.start()
        self.setWindowTitle(f"ShamsiCal {__version__}")
        self.setWindowIcon(QIcon(str(Path(__file__).parent / "assets/app.png")))
        self.resize(1140, 800)
        self.rebuild()
        geometry = store.data.get("geometry")
        if isinstance(geometry, str):
            self.restoreGeometry(QByteArray.fromHex(geometry.encode("ascii", errors="ignore")))
            # Recover after a display is disconnected.
            if not any(
                screen.availableGeometry().intersects(self.frameGeometry())
                for screen in QApplication.screens()
            ):
                self.move(QApplication.primaryScreen().availableGeometry().center() - self.rect().center())
        available = (self.screen() or QApplication.primaryScreen()).availableGeometry()
        self.resize(min(self.width(), available.width() - 20), min(self.height(), available.height() - 50))
        for sequence, callback in (
            ("Ctrl+T", self.go_today),
            ("Alt+Left", lambda: self.select_day(calendar.shift_day(self.day, -1))),
            ("Alt+Right", lambda: self.select_day(calendar.shift_day(self.day, 1))),
            ("Ctrl+J", self.jump),
            ("Ctrl+N", self.new_note),
            ("Ctrl+S", self.persist),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(callback)

    @property
    def language(self):
        return self.store.data["language"]

    def t(self, key):
        return tr(key, self.language)

    def rebuild(self):
        self.save_timer.stop()
        previous = self.takeCentralWidget()
        if previous:
            previous.deleteLater()
        QApplication.instance().setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if self.language == "fa" else Qt.LayoutDirection.LeftToRight
        )
        self.setStyleSheet(stylesheet(self.store.data["theme"], self.store.data["font_size"]))
        root = QWidget()
        root.setObjectName("root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 20, 28, 12)
        layout.setSpacing(20)
        header = QHBoxLayout()
        mark = label()
        mark.setPixmap(qta.icon("ph.calendar-blank-fill", color="#77b9ff").pixmap(44, 44))
        header.addWidget(mark)
        brand = QVBoxLayout()
        brand.setSpacing(2)
        brand.addWidget(label("ShamsiCal", "brand"))
        brand.addWidget(label(self.t("tagline"), "muted"))
        header.addLayout(brand)
        header.addStretch()
        self.compact_button = button(
            self.t("expand" if self.store.data["compact"] else "compact"),
            "ph.corners-in",
            self.toggle_compact,
        )
        header.addWidget(self.compact_button)
        layout.addLayout(header)
        self.tabs = QTabWidget()
        self.tabs.setAccessibleName("ShamsiCal")
        self.calendar_page = self.build_calendar()
        self.notes_page = NotesPage(self)
        self.reader_page = ReaderPage(self)
        self.settings_page = SettingsPage(self)
        for page, key, icon in (
            (self.calendar_page, "calendar", "ph.calendar-blank"),
            (self.notes_page, "notes", "ph.notebook"),
            (self.reader_page, "feeds", "ph.rss"),
            (self.settings_page, "settings", "ph.sliders-horizontal"),
        ):
            self.tabs.addTab(page, qta.icon(icon, color="#77b9ff"), self.t(key))
        layout.addWidget(self.tabs, 1)
        self.setCentralWidget(root)
        self.statusBar().setSizeGripEnabled(True)
        self.statusBar().showMessage(self.t("saved"))
        self.apply_compact()
        self.render_date()

    def build_calendar(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 14, 0, 0)
        layout.setSpacing(16)
        row = QHBoxLayout()
        row.setSpacing(18)
        self.month_card, area = card()
        top = QHBoxLayout()
        self.month_heading = label("", "heading")
        top.addWidget(self.month_heading, 1)
        self.previous_month = button(
            "",
            "ph.caret-right" if self.language == "fa" else "ph.caret-left",
            lambda: self.select_day(calendar.shift_month(self.day, -1)),
        )
        self.previous_month.setAccessibleName(self.t("previous_month"))
        self.previous_month.setToolTip(self.t("previous_month"))
        self.next_month = button(
            "",
            "ph.caret-left" if self.language == "fa" else "ph.caret-right",
            lambda: self.select_day(calendar.shift_month(self.day, 1)),
        )
        self.next_month.setAccessibleName(self.t("next_month"))
        self.next_month.setToolTip(self.t("next_month"))
        top.addWidget(self.previous_month)
        top.addWidget(self.next_month)
        area.addLayout(top)
        self.month_bridge = label("", "muted")
        self.month_bridge.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        area.addWidget(self.month_bridge)
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(5)
        names = calendar.WEEKDAYS_FA if self.language == "fa" else calendar.WEEKDAYS_EN
        for column, name in enumerate(names):
            day_label = label(name, "muted")
            day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(day_label, 0, column)
            self.grid.setColumnStretch(column, 1)
        self.day_buttons = []
        for index in range(42):
            cell = DayButton()
            cell.colors = PALETTES[self.store.data["theme"]]
            cell.clicked.connect(lambda checked=False, index=index: self.cell_clicked(index))
            self.grid.addWidget(cell, index // 7 + 1, index % 7)
            self.day_buttons.append(cell)
        area.addLayout(self.grid)
        area.addStretch()
        actions = QHBoxLayout()
        actions.addWidget(button(self.t("today"), "ph.sun", self.go_today, True))
        actions.addWidget(button(self.t("jump"), "ph.magnifying-glass", self.jump))
        area.addLayout(actions)
        row.addWidget(self.month_card, 3)
        self.detail_card, area = card()
        area.addWidget(label(self.t("selected"), "muted"))
        hero = QHBoxLayout()
        self.day_number = label("", "hero")
        hero.addWidget(self.day_number)
        hero_text = QVBoxLayout()
        self.weekday = label("", "heading")
        self.full_date = label("", "muted")
        hero_text.addWidget(self.weekday)
        hero_text.addWidget(self.full_date)
        hero.addLayout(hero_text, 1)
        area.addLayout(hero)
        day_actions = QHBoxLayout()
        day_actions.addWidget(
            button(
                self.t("previous_day"), "ph.minus", lambda: self.select_day(calendar.shift_day(self.day, -1))
            )
        )
        day_actions.addWidget(
            button(self.t("next_day"), "ph.plus", lambda: self.select_day(calendar.shift_day(self.day, 1)))
        )
        area.addLayout(day_actions)
        self.gregorian = label("", wrap=True)
        self.hijri = label("", wrap=True)
        area.addWidget(label(self.t("gregorian"), "muted"))
        area.addWidget(self.gregorian)
        area.addWidget(label(self.t("hijri"), "muted"))
        area.addWidget(self.hijri)
        self.event_header = label(self.t("events"), "heading")
        area.addWidget(self.event_header)
        self.events_label = label("", wrap=True)
        self.events_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        event_scroll = QScrollArea()
        event_scroll.setWidgetResizable(True)
        event_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        event_scroll.setMinimumHeight(60)
        event_scroll.setMaximumHeight(150)
        event_scroll.setWidget(self.events_label)
        area.addWidget(event_scroll)
        self.event_source = label(self.t("provider"), "muted", True)
        area.addWidget(self.event_source)
        area.addStretch()
        actions = QHBoxLayout()
        actions.addWidget(button(self.t("copy_date"), "ph.copy", self.copy_date))
        self.events_refresh = button(
            self.t("refresh"), "ph.arrow-clockwise", lambda: self.load_events(force=True)
        )
        actions.addWidget(self.events_refresh)
        area.addLayout(actions)
        row.addWidget(self.detail_card, 2)
        layout.addLayout(row, 1)
        self.quote_card, area = card()
        area.addWidget(label(self.t("quote"), "muted"))
        self.quote_label = label("", wrap=True)
        area.addWidget(self.quote_label)
        layout.addWidget(self.quote_card)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        return scroll

    def render_date(self):
        self.month_heading.setText(calendar.heading(self.day, self.language))
        first, last = (
            self.day.replace(day=1),
            self.day.replace(day=calendar.month_length(self.day.year, self.day.month)),
        )
        self.month_bridge.setText(f"{first.togregorian():%d %b %Y} — {last.togregorian():%d %b %Y}")
        cells = calendar.month_cells(self.day)
        self.cells = cells
        for index, cell in enumerate(self.day_buttons):
            day = cells[index] if index < len(cells) else None
            cell.setVisible(index < ((len(cells) + 6) // 7) * 7)
            cell.setEnabled(day is not None)
            cell.primary = calendar.digits(day.day, self.language) if day else ""
            cell.secondary = str(day.togregorian().day) if day else ""
            cell.setChecked(day == self.day)
            cell.setProperty("today", day == calendar.today())
            cell.setProperty("friday", index % 7 == 6)
            cell.setAccessibleName(f"{day.year}/{day.month:02}/{day.day:02}" if day else "")
            cell.setToolTip(f"{day.togregorian():%Y-%m-%d}" if day else "")
            cell.style().unpolish(cell)
            cell.style().polish(cell)
            cell.update()
        self.previous_month.setEnabled((self.day.year, self.day.month) != (calendar.MIN_YEAR, 1))
        self.next_month.setEnabled((self.day.year, self.day.month) != (calendar.MAX_YEAR, 12))
        self.day_number.setText(calendar.digits(self.day.day, self.language))
        weekday_index = (self.day.togregorian().weekday() + 2) % 7
        self.weekday.setText(
            (calendar.WEEKDAYS_FA if self.language == "fa" else calendar.WEEKDAYS_EN)[weekday_index]
        )
        self.full_date.setText(calendar.heading(self.day, self.language))
        self.gregorian.setText(f"{self.day.togregorian():%d %B %Y}")
        self.hijri.setText(calendar.hijri_text(self.day, self.language))
        self.events_refresh.setEnabled(self.store.data["online_events"] and not self.event_busy)
        self.show_events()
        self.event_timer.start()
        self.render_quote()

    def show_events(self):
        key = self.day.isoformat()
        events = self.store.data["events"].get(key)
        valid = isinstance(events, list) and all(isinstance(item, str) for item in events)
        if valid:
            self.events_label.setText("\n".join(events[:5]) if events else self.t("no_events"))
            self.event_source.setText(self.t("cached"))
        else:
            self.events_label.setText(
                self.t("loading") if self.store.data["online_events"] else self.t("offline")
            )
            self.event_source.setText(self.t("provider") if self.store.data["online_events"] else "")

    def load_events(self, force=False):
        self.event_timer.stop()
        if self.event_busy or not self.store.data["online_events"]:
            return
        day = self.day
        key = day.isoformat()
        if not force and key in self.store.data["events"]:
            return
        self.event_busy = True
        self.events_refresh.setEnabled(False)
        self.events_label.setText(self.t("loading"))

        def complete(events, error):
            self.event_busy = False
            self.events_refresh.setEnabled(self.store.data["online_events"])
            if not error and self.store.data["online_events"]:
                self.store.data["events"][key] = events
                while len(self.store.data["events"]) > 400:
                    self.store.data["events"].pop(next(iter(self.store.data["events"])))
                self.schedule_save()
            if self.day == day:
                if error:
                    self.show_events()
                    self.event_source.setText(self.t("event_error"))
                    if key not in self.store.data["events"]:
                        self.events_label.setText(self.t("event_error"))
                else:
                    self.show_events()
            else:
                self.show_events()
                self.event_timer.start()

        self.jobs.submit(lambda: network.read_events(day), complete)

    def render_quote(self):
        quotes = self.store.data["quotes"]
        interval = {"hourly": 3600, "daily": 86400, "weekly": 604800}[self.store.data["quote_frequency"]]
        self.quote_label.setText(quotes[int(time.time() // interval) % len(quotes)] if quotes else "")

    def cell_clicked(self, index):
        if index < len(self.cells) and self.cells[index]:
            self.select_day(self.cells[index])

    def select_day(self, day):
        self.day = day
        self.render_date()

    def go_today(self):
        self.select_day(calendar.today())

    def jump(self):
        text, ok = QInputDialog.getText(self, self.t("jump"), self.t("jump_prompt"))
        if not ok:
            return
        try:
            # int accepts both Persian and Arabic decimal digits.
            values = [int(value) for value in text.strip().replace("-", "/").split("/")]
            if len(values) != 3 or not calendar.MIN_YEAR <= values[0] <= calendar.MAX_YEAR:
                raise ValueError
            self.select_day(jdatetime.date(*values))
        except (ValueError, OverflowError):
            QMessageBox.warning(self, self.t("error"), self.t("invalid_date"))

    def copy_date(self):
        QApplication.clipboard().setText(f"{self.day.year}/{self.day.month:02}/{self.day.day:02}")

    def new_note(self):
        self.tabs.setCurrentWidget(self.notes_page)
        self.notes_page.add_note()

    def toggle_compact(self):
        if not self.store.data["compact"]:
            self.store.data["full_size"] = [self.width(), self.height()]
        self.store.data["compact"] = not self.store.data["compact"]
        self.apply_compact()
        self.schedule_save()

    def apply_compact(self):
        compact = self.store.data["compact"]
        self.month_card.setVisible(not compact)
        self.quote_card.setVisible(not compact)
        self.compact_button.setText(self.t("expand" if compact else "compact"))
        self.setMinimumSize(490 if compact else 950, 620 if compact else 680)
        if compact:
            self.resize(520, 700)
        else:
            size = self.store.data.get("full_size", [1140, 800])
            if (
                isinstance(size, list)
                and len(size) == 2
                and all(type(n) is int and 500 <= n <= 4000 for n in size)
            ):
                self.resize(*size)

    def tick(self):
        now = calendar.today()
        if now != self.last_today:
            if self.day == self.last_today:
                self.day = now
            self.last_today = now
            self.render_date()
        self.render_quote()

    def schedule_save(self):
        self.save_timer.start()

    def persist(self, collect=True):
        if collect and hasattr(self, "notes_page"):
            self.notes_page.collect()
        try:
            self.store.save()
            self.save_failed = False
            self.statusBar().showMessage(self.t("saved"))
            return True
        except (StorageError, OSError):
            self.save_failed = True
            self.statusBar().showMessage(self.t("save_error"))
            return False

    def closeEvent(self, event):
        if self.jobs.pending:
            self.statusBar().showMessage(self.t("busy"))
            event.ignore()
            return
        self.save_timer.stop()
        self.store.data["geometry"] = bytes(self.saveGeometry().toHex()).decode("ascii")
        if not self.persist():
            QMessageBox.warning(self, self.t("error"), self.t("close_unsaved"))
            self.tabs.setCurrentWidget(self.settings_page)
            event.ignore()
            return
        self.event_timer.stop()
        self.clock.stop()
        event.accept()


def main(argv=None):
    parser = argparse.ArgumentParser(description="ShamsiCal desktop calendar")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--data-dir", type=Path, help="Use a separate local workspace directory")
    parser.add_argument(
        "--smoke-test", action="store_true", help="Render offscreen and quit without changing user data"
    )
    args = parser.parse_args(argv)
    app = QApplication(sys.argv[:1])
    app.setOrganizationName("ShamsiCal")
    app.setApplicationName("ShamsiCal")
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")
    font_dir = Path(__file__).parent / "assets" / "fonts"
    for font in font_dir.glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(font))
    families = QFontDatabase.families()
    app.setFont(
        QFont(
            next(
                (name for name in ("Vazirmatn", "Segoe UI", "Tahoma", "DejaVu Sans") if name in families),
                app.font().family(),
            ),
            11,
        )
    )
    directory = args.data_dir or Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    )
    temporary = None
    if args.smoke_test:
        import tempfile

        temporary = tempfile.TemporaryDirectory(prefix="shamsical-smoke-")
        directory = Path(temporary.name)
    try:
        directory.mkdir(parents=True, exist_ok=True)
        lock = QLockFile(str(directory / "workspace.lock"))
        lock.setStaleLockTime(0)
        if not lock.tryLock(100):
            QMessageBox.warning(None, "ShamsiCal", "این فضای کاری باز است. / This workspace is already open.")
            return 1
        store = Store(directory)
    except (StorageError, OSError) as error:
        QMessageBox.critical(
            None,
            "ShamsiCal · Recovery",
            "داده‌ها دست‌نخورده ماندند. فایل پشتیبان را بازیابی کنید.\nYour data was left untouched. Restore workspace.json from workspace.json.bak, or start with --data-dir pointing to a new folder.\n\n"
            + str(directory)
            + "\n"
            + str(error),
        )
        return 1
    try:
        window = Window(store)
        window.show()
        if args.smoke_test:
            QTimer.singleShot(400, window.close)
        return app.exec()
    finally:
        lock.unlock()
        if temporary:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
