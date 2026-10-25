"""The application is a suite of independent desktop widgets, as in v1."""

import time
from pathlib import Path

import jdatetime
from PyQt6.QtCore import QPoint, QSettings, Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from . import calendar, network
from . import icons as qta
from .floating import FloatingPanel
from .i18n import tr
from .jobs import Jobs
from .notes import NotesPage
from .reader import ReaderPage
from .settings import SettingsPage
from .storage import StorageError
from .theme import PALETTES, stylesheet
from .widgets import DayButton, button, label

PANEL_KEYS = {
    "calendar": "calendar",
    "quote": "quote_widget",
    "notes": "notes",
    "reader": "feeds",
    "month": "month_widget",
}
DEFAULT_VISIBLE = {"calendar": True, "quote": True, "notes": False, "reader": False, "month": False}
DEFAULT_SIZES = {
    "calendar": (380, 320),
    "quote": (320, 155),
    "notes": (570, 380),
    "reader": (390, 450),
    "month": (450, 470),
}


class Window(FloatingPanel):
    """Calendar widget and coordinator; no tabbed application window is created."""

    def __init__(self, store, *, quit_application=False):
        self.store = store
        self.building = True
        self.started = False
        self.quitting = False
        self.quit_application = quit_application
        self.panels = {}
        self.settings_dialog = None
        self.day = calendar.today()
        self.last_today = self.day
        self.event_busy = self.save_failed = False
        super().__init__(self, "calendar", "ShamsiCal")
        self.panels["calendar"] = self
        self.setWindowIcon(QIcon(str(Path(__file__).parent / "assets/app.png")))
        self.jobs = Jobs(self)
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
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.tray.setToolTip("ShamsiCal")
        self.tray.activated.connect(self.tray_activated)
        self.rebuild()
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

    def statusBar(self):
        # Shared save/network feedback for the reusable notes and settings controls.
        return self.status

    def rebuild(self):
        self.building = True
        self.save_timer.stop()
        if self.settings_dialog:
            self.settings_dialog.hide()
            self.settings_dialog.deleteLater()
            self.settings_dialog = None
        for key, panel in list(self.panels.items()):
            if key != "calendar":
                panel.hide()
                panel.deleteLater()
        self.panels = {"calendar": self}
        QApplication.instance().setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if self.language == "fa" else Qt.LayoutDirection.LeftToRight
        )
        states = self.store.data["widgets"]
        for key in PANEL_KEYS:
            states.setdefault(key, {}).setdefault("visible", DEFAULT_VISIBLE[key])
        self.set_content(self.build_calendar())
        self.quote_widget = self.make_panel("quote")
        self.quote_label = label("", wrap=True)
        self.quote_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.quote_widget.body.addWidget(self.quote_label, 1)
        self.note_widget = self.make_panel("notes")
        self.notes_page = NotesPage(self)
        self.note_widget.set_content(self.notes_page)
        self.reader_widget = self.make_panel("reader")
        self.reader_page = ReaderPage(self, compact=True)
        self.reader_widget.set_content(self.reader_page)
        self.month_widget = self.make_panel("month")
        self.month_widget.set_content(self.build_month())
        for key, panel in self.panels.items():
            self.apply_appearance(panel)
            self.restore_panel(key)
        self.settings_dialog = QDialog(self)
        self.settings_dialog.setWindowTitle(self.t("settings"))
        self.settings_dialog.setWindowIcon(self.windowIcon())
        self.settings_dialog.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint, self.store.data["always_on_top"]
        )
        self.settings_dialog.setStyleSheet(stylesheet(self.store.data["theme"], self.store.data["font_size"]))
        layout = QVBoxLayout(self.settings_dialog)
        self.settings_page = SettingsPage(self)
        layout.addWidget(self.settings_page)
        self.settings_dialog.resize(560, 660)
        old_menu = self.tray.contextMenu()
        self.tray.setContextMenu(self.create_menu())
        if old_menu:
            old_menu.deleteLater()
        self.building = False
        self.render_date()
        self.status.showMessage(self.t("saved"))
        if self.started:
            self.show_saved_panels()

    def make_panel(self, key):
        panel = FloatingPanel(self, key, self.t(PANEL_KEYS[key]))
        panel.setWindowIcon(self.windowIcon())
        minimum = {"quote": (230, 110), "notes": (430, 290), "reader": (330, 350), "month": (400, 420)}[key]
        panel.setMinimumSize(*minimum)
        self.panels[key] = panel
        for sequence, callback in (
            ("Ctrl+S", self.persist),
            ("Ctrl+N", self.new_note),
            ("Ctrl+T", self.go_today),
        ):
            shortcut = QShortcut(QKeySequence(sequence), panel)
            shortcut.activated.connect(callback)
        return panel

    def apply_appearance(self, panel):
        panel.setStyleSheet(
            stylesheet(self.store.data["theme"], self.store.data["font_size"])
            + "QPushButton#widgetIcon { min-height: 0; padding: 2px; border-radius: 6px; } QLabel#widgetDay { font-size: 34pt; font-weight: 700; color: "
            + PALETTES[self.store.data["theme"]]["accent"]
            + "; } QLabel#widgetTitle { font-size: 14pt; font-weight: 600; }"
        )
        panel.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.store.data["always_on_top"])
        panel.setWindowOpacity(self.store.data["widget_opacity"] / 100)
        panel.handle.setToolTip(self.t("drag_widget"))
        for control, key in ((panel.menu_button, "widget_menu"), (panel.hide_button, "hide_widget")):
            control.setToolTip(self.t(key))
            control.setAccessibleName(self.t(key))
        for child in panel.findChildren(QWidget):
            if isinstance(child, QPushButton) and child.property("iconName"):
                child.setIcon(
                    qta.icon(
                        child.property("iconName"),
                        color="white"
                        if child.objectName() == "primary"
                        else PALETTES[self.store.data["theme"]]["accent"],
                    )
                )
            if isinstance(child, type(self.quote_label)):
                if not self.store.data["widget_background"]:
                    shadow = QGraphicsDropShadowEffect(child)
                    shadow.setBlurRadius(5)
                    shadow.setOffset(0, 1)
                    shadow.setColor(QColor(0, 0, 0, 200))
                    child.setGraphicsEffect(shadow)
                else:
                    child.setGraphicsEffect(None)
        panel.update()

    def build_calendar(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        self.compact_label = label("", "widgetTitle", True)
        layout.addWidget(self.compact_label)
        self.hero_frame = QWidget()
        top = QHBoxLayout(self.hero_frame)
        top.setContentsMargins(0, 0, 0, 0)
        self.day_number = label("", "widgetDay")
        top.addWidget(self.day_number)
        date_text = QVBoxLayout()
        date_text.setSpacing(0)
        self.weekday = label("", "widgetTitle")
        self.full_date = label("", "muted")
        date_text.addWidget(self.weekday)
        date_text.addWidget(self.full_date)
        top.addLayout(date_text, 1)
        layout.addWidget(self.hero_frame)
        actions = QHBoxLayout()
        self.previous_day = self.icon_button(
            self.t("previous_day"),
            "ph.caret-right" if self.language == "fa" else "ph.caret-left",
            lambda: self.select_day(calendar.shift_day(self.day, -1)),
        )
        self.next_day = self.icon_button(
            self.t("next_day"),
            "ph.caret-left" if self.language == "fa" else "ph.caret-right",
            lambda: self.select_day(calendar.shift_day(self.day, 1)),
        )
        actions.addWidget(self.previous_day)
        actions.addWidget(button(self.t("today"), "ph.sun", self.go_today, True), 1)
        actions.addWidget(self.next_day)
        actions.addWidget(
            self.icon_button(self.t("month_widget"), "ph.calendar-blank", lambda: self.toggle_panel("month"))
        )
        layout.addLayout(actions)
        self.date_details = QWidget()
        details = QVBoxLayout(self.date_details)
        details.setContentsMargins(0, 0, 0, 0)
        details.setSpacing(4)
        self.gregorian = label("", "muted")
        self.hijri = label("", "muted")
        details.addWidget(self.gregorian)
        details.addWidget(self.hijri)
        self.events_label = label("", wrap=True)
        self.events_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self.events_label)
        scroll.setMinimumHeight(32)
        scroll.setMaximumHeight(82)
        details.addWidget(scroll)
        self.event_source = label("", "muted", True)
        details.addWidget(self.event_source)
        layout.addWidget(self.date_details, 1)
        self.shortcut_bar = QWidget()
        shortcuts = QHBoxLayout(self.shortcut_bar)
        shortcuts.setContentsMargins(0, 0, 0, 0)
        for key, icon in (("notes", "ph.notebook"), ("reader", "ph.rss"), ("quote", "ph.quotes")):
            shortcuts.addWidget(
                self.icon_button(
                    self.t(PANEL_KEYS[key]), icon, lambda checked=False, key=key: self.toggle_panel(key)
                )
            )
        shortcuts.addStretch()
        self.events_refresh = self.icon_button(
            self.t("refresh"), "ph.arrow-clockwise", lambda: self.load_events(force=True)
        )
        shortcuts.addWidget(self.events_refresh)
        shortcuts.addWidget(self.icon_button(self.t("settings"), "ph.sliders-horizontal", self.show_settings))
        layout.addWidget(self.shortcut_bar)
        self.setMinimumSize(320, 150)
        self.date_details.setVisible(not self.store.data["compact"])
        self.hero_frame.setVisible(not self.store.data["compact"])
        self.compact_label.setVisible(self.store.data["compact"])
        self.shortcut_bar.setVisible(not self.store.data["compact"])
        return content

    def build_month(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        heading_row = QHBoxLayout()
        self.month_heading = label("", "widgetTitle")
        heading_row.addWidget(self.month_heading, 1)
        self.previous_month = self.icon_button(
            self.t("previous_month"), "ph.minus", lambda: self.select_day(calendar.shift_month(self.day, -1))
        )
        self.next_month = self.icon_button(
            self.t("next_month"), "ph.plus", lambda: self.select_day(calendar.shift_month(self.day, 1))
        )
        heading_row.addWidget(self.previous_month)
        heading_row.addWidget(self.next_month)
        layout.addLayout(heading_row)
        grid = QGridLayout()
        grid.setSpacing(4)
        names = calendar.WEEKDAYS_FA if self.language == "fa" else calendar.WEEKDAYS_EN
        for column, name in enumerate(names):
            heading = label(name, "muted")
            heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(heading, 0, column)
        self.day_buttons = []
        for index in range(42):
            cell = DayButton()
            cell.colors = PALETTES[self.store.data["theme"]]
            cell.clicked.connect(lambda checked=False, index=index: self.cell_clicked(index))
            grid.addWidget(cell, index // 7 + 1, index % 7)
            self.day_buttons.append(cell)
        layout.addLayout(grid)
        layout.addWidget(button(self.t("jump"), "ph.magnifying-glass", self.jump))
        return content

    def default_geometry(self, key):
        screen = QApplication.primaryScreen().availableGeometry()
        width, height = DEFAULT_SIZES[key]
        positions = {
            "calendar": (screen.right() - width - 28, screen.top() + 35),
            "quote": (screen.right() - width - 28, screen.top() + 380),
            "notes": (screen.left() + 35, screen.top() + 35),
            "reader": (screen.left() + 35, screen.top() + 445),
            "month": (screen.right() - width - 430, screen.top() + 35),
        }
        return (*positions[key], width, height)

    def restore_panel(self, key):
        panel = self.panels[key]
        state = self.store.data["widgets"][key]
        x, y, width, height = self.default_geometry(key)
        x, y, width, height = (
            state.get("x", x),
            state.get("y", y),
            state.get("width", width),
            state.get("height", height),
        )
        screen = (
            QApplication.screenAt(QPoint(x + width // 2, y + height // 2)) or QApplication.primaryScreen()
        )
        rect = screen.availableGeometry()
        width, height = (
            min(max(width, panel.minimumWidth()), rect.width()),
            min(max(height, panel.minimumHeight()), rect.height()),
        )
        panel.resize(width, height)
        panel.move(
            min(max(x, rect.left()), max(rect.left(), rect.right() - panel.width() + 1)),
            min(max(y, rect.top()), max(rect.top(), rect.bottom() - panel.height() + 1)),
        )

    def start(self):
        self.started = True
        self.clock.start()
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        self.show_saved_panels()

    def show_saved_panels(self):
        states = self.store.data["widgets"]
        if not self.tray.isVisible() and not any(states[key]["visible"] for key in PANEL_KEYS):
            states["calendar"]["visible"] = True
        for key, panel in self.panels.items():
            panel.setVisible(states[key]["visible"])

    def remember_panel(self, panel):
        if self.building or not self.started or self.quitting:
            return
        state = self.store.data["widgets"].setdefault(panel.key, {})
        state.update({"x": panel.x(), "y": panel.y(), "width": panel.width(), "height": panel.height()})
        self.schedule_save()

    def show_panel(self, key):
        self.store.data["widgets"][key]["visible"] = True
        self.panels[key].show()
        self.panels[key].raise_()
        self.schedule_save()

    def hide_panel(self, key):
        if not self.tray.isVisible() and not any(
            panel.isVisible() for name, panel in self.panels.items() if name != key
        ):
            # Without a tray, retain a recoverable calendar rather than orphaning the process.
            if key == "calendar":
                self.close()
                return
            self.show_panel("calendar")
        self.store.data["widgets"][key]["visible"] = False
        self.panels[key].hide()
        self.schedule_save()

    def toggle_panel(self, key):
        self.hide_panel(key) if self.panels[key].isVisible() else self.show_panel(key)

    def reset_layout(self):
        self.building = True
        for key in PANEL_KEYS:
            self.store.data["widgets"][key] = {"visible": self.store.data["widgets"][key]["visible"]}
            self.restore_panel(key)
        self.building = False
        for panel in self.panels.values():
            self.remember_panel(panel)
        self.schedule_save()

    def import_v1_layout(self):
        old = QSettings("MyCompany", "ShamsiCalendar")
        self.building = True
        try:
            saved = old.value("main_widget/pos", "")
            if isinstance(saved, str) and saved:
                x, y = map(int, saved.split(","))
                self.store.data["widgets"]["calendar"].update({"x": x, "y": y})
            for key, prefix in (("quote", "quote_widget"), ("reader", "rss_widget")):
                point = old.value(prefix + "/pos")
                if isinstance(point, QPoint):
                    self.store.data["widgets"][key].update({"x": point.x(), "y": point.y()})
                self.store.data["widgets"][key]["visible"] = old.value(
                    prefix + "/is_visible", DEFAULT_VISIBLE[key], type=bool
                )
            geometry = old.value("note_manager/geometry")
            if geometry:
                self.note_widget.restoreGeometry(geometry)
                self.store.data["widgets"]["notes"].update(
                    {
                        "x": self.note_widget.x(),
                        "y": self.note_widget.y(),
                        "width": self.note_widget.width(),
                        "height": self.note_widget.height(),
                    }
                )
            self.store.data["widgets"]["notes"]["visible"] = old.value(
                "note_manager/is_visible", False, type=bool
            )
        except (ValueError, TypeError):
            pass
        finally:
            self.building = False
        for key in PANEL_KEYS:
            self.restore_panel(key)
        self.show_saved_panels()
        self.schedule_save()

    def create_menu(self, panel=None):
        menu = QMenu(panel or self)
        menu.setStyleSheet(stylesheet(self.store.data["theme"], self.store.data["font_size"]))
        for key, text in PANEL_KEYS.items():
            action = QAction(self.t(text), menu)
            action.setCheckable(True)
            action.setChecked(self.store.data["widgets"][key]["visible"])
            action.setData(key)
            action.triggered.connect(lambda checked=False, key=key: self.toggle_panel(key))
            menu.addAction(action)

        def sync_checks():
            for action in menu.actions():
                if action.data() in PANEL_KEYS:
                    action.setChecked(self.store.data["widgets"][action.data()]["visible"])

        menu.aboutToShow.connect(sync_checks)
        menu.addSeparator()
        for text, callback in (
            ("today", self.go_today),
            ("jump", self.jump),
            ("copy_date", self.copy_date),
            ("compact", self.toggle_compact),
            ("settings", self.show_settings),
            ("reset_layout", self.reset_layout),
            ("quit", self.close),
        ):
            action = QAction(self.t(text), menu)
            action.triggered.connect(lambda checked=False, callback=callback: callback())
            menu.addAction(action)
        return menu

    def tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_panel("calendar")

    def show_settings(self):
        if not self.settings_dialog.isVisible():
            for key, control in self.settings_page.visibility.items():
                control.setChecked(self.store.data["widgets"][key]["visible"])
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def render_date(self):
        self.day_number.setText(calendar.digits(self.day.day, self.language))
        index = (self.day.togregorian().weekday() + 2) % 7
        self.weekday.setText((calendar.WEEKDAYS_FA if self.language == "fa" else calendar.WEEKDAYS_EN)[index])
        self.full_date.setText(calendar.heading(self.day, self.language))
        self.compact_label.setText(
            f"{self.weekday.text()} {calendar.digits(self.day.day, self.language)} {calendar.heading(self.day, self.language)}"
        )
        self.gregorian.setText(f"{self.day.togregorian():%d %B %Y}")
        self.hijri.setText(calendar.hijri_text(self.day, self.language))
        self.month_heading.setText(calendar.heading(self.day, self.language))
        self.cells = calendar.month_cells(self.day)
        for index, cell in enumerate(self.day_buttons):
            day = self.cells[index] if index < len(self.cells) else None
            cell.setVisible(index < ((len(self.cells) + 6) // 7) * 7)
            cell.setEnabled(day is not None)
            cell.primary = calendar.digits(day.day, self.language) if day else ""
            cell.secondary = str(day.togregorian().day) if day else ""
            cell.setChecked(day == self.day)
            cell.setProperty("today", day == calendar.today())
            cell.setProperty("friday", index % 7 == 6)
            cell.setAccessibleName(str(day) if day else "")
            cell.style().unpolish(cell)
            cell.style().polish(cell)
            cell.update()
        self.events_refresh.setEnabled(self.store.data["online_events"] and not self.event_busy)
        self.show_events()
        if self.store.data["online_events"]:
            self.event_timer.start()
        self.render_quote()

    def show_events(self):
        events = self.store.data["events"].get(self.day.isoformat())
        if isinstance(events, list) and all(isinstance(item, str) for item in events):
            self.events_label.setText("\n".join(events[:5]) if events else self.t("no_events"))
            self.event_source.setText(self.t("cached"))
        else:
            self.events_label.setText(
                self.t("loading") if self.store.data["online_events"] else self.t("offline")
            )
            self.event_source.setText(self.t("provider") if self.store.data["online_events"] else "")
        self.event_source.setVisible(bool(self.event_source.text()))

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
            self.show_events()
            if self.day == day and error:
                self.event_source.setText(self.t("event_error"))
                self.event_source.show()
                if key not in self.store.data["events"]:
                    self.events_label.setText(self.t("event_error"))
            elif self.day != day:
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
        if ok:
            try:
                values = [int(value) for value in text.strip().replace("-", "/").split("/")]
                if len(values) != 3 or not calendar.MIN_YEAR <= values[0] <= calendar.MAX_YEAR:
                    raise ValueError
                self.select_day(jdatetime.date(*values))
            except (ValueError, OverflowError):
                QMessageBox.warning(self, self.t("error"), self.t("invalid_date"))

    def copy_date(self):
        QApplication.clipboard().setText(f"{self.day.year}/{self.day.month:02}/{self.day.day:02}")

    def new_note(self):
        self.show_panel("notes")
        self.notes_page.add_note()

    def toggle_compact(self):
        self.store.data["compact"] = not self.store.data["compact"]
        self.date_details.setVisible(not self.store.data["compact"])
        self.hero_frame.setVisible(not self.store.data["compact"])
        self.compact_label.setVisible(self.store.data["compact"])
        self.shortcut_bar.setVisible(not self.store.data["compact"])
        self.layout().activate()
        self.resize(self.width(), 170 if self.store.data["compact"] else DEFAULT_SIZES["calendar"][1])
        self.schedule_save()

    def tick(self):
        now = calendar.today()
        if now != self.last_today:
            if self.day == self.last_today:
                self.day = now
            self.last_today = now
            self.render_date()
        self.render_quote()

    def schedule_save(self):
        if not self.building and not self.quitting:
            self.save_timer.start()

    def persist(self, collect=True):
        if collect:
            self.notes_page.collect()
        try:
            self.store.save()
            self.save_failed = False
            for panel in self.panels.values():
                panel.status.showMessage(self.t("saved"))
            return True
        except (StorageError, OSError):
            self.save_failed = True
            for panel in self.panels.values():
                panel.status.showMessage(self.t("save_error"))
            return False

    def closeEvent(self, event):
        if self.quitting:
            event.accept()
            return
        if self.jobs.pending:
            self.status.showMessage(self.t("busy"))
            event.ignore()
            return
        for panel in self.panels.values():
            self.remember_panel(panel)
        self.save_timer.stop()
        if not self.persist():
            QMessageBox.warning(self, self.t("error"), self.t("close_unsaved"))
            self.show_settings()
            event.ignore()
            return
        self.quitting = True
        self.event_timer.stop()
        self.clock.stop()
        self.tray.hide()
        self.settings_dialog.close()
        for key, panel in self.panels.items():
            if key != "calendar":
                panel.close()
        event.accept()
        if self.quit_application:
            QApplication.instance().quit()
