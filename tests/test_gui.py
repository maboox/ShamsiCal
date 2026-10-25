import threading

import jdatetime
import pytest
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt, QUrl
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QMessageBox, QTabWidget

from shamsical import calendar, network
from shamsical.app import Window
from shamsical.storage import StorageError, Store
from shamsical.widgets import PrivateDocument


@pytest.fixture
def window(qtbot, tmp_path, monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("Unexpected network call")

    monkeypatch.setattr(network, "fetch", unexpected)
    widget = Window(Store(tmp_path))
    qtbot.addWidget(widget)
    widget.start()
    yield widget
    qtbot.waitUntil(lambda: not widget.jobs.pending)


def test_offline_start_and_month_day_navigation(window, qtbot):
    window.show_panel("month")
    window.select_day(jdatetime.date(1403, 12, 30))
    qtbot.mouseClick(window.next_month, Qt.MouseButton.LeftButton)
    assert window.day == jdatetime.date(1404, 1, 30)
    window.select_day(jdatetime.date(1404, 1, 1))
    index = next(i for i, value in enumerate(window.cells) if value and value.day == 10)
    qtbot.mouseClick(window.day_buttons[index], Qt.MouseButton.LeftButton)
    assert window.day.day == 10
    window.go_today()
    assert window.day == calendar.today()
    assert not window.jobs.pending


def test_notes_survive_switch_and_restart(window, qtbot):
    notes = window.notes_page
    notes.editor.setPlainText("متن یادداشت اول")
    notes.add_note()
    notes.editor.setPlainText("Second note")
    notes.list.setCurrentRow(0)
    assert notes.editor.toPlainText() == "متن یادداشت اول"
    assert window.persist()
    restored = Store(window.store.directory)
    assert "Second note" in restored.data["notes"][1]["html"]


def test_delete_preserves_neighbour_and_last_note(window, monkeypatch):
    notes = window.notes_page
    notes.editor.setPlainText("first")
    notes.add_note()
    notes.editor.setPlainText("second")
    notes.list.setCurrentRow(0)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    notes.delete()
    assert notes.editor.toPlainText() == "second"
    assert len(notes.notes) == 1
    notes.delete()
    assert len(notes.notes) == 1
    assert notes.editor.toPlainText() == ""


def test_save_failure_visible_and_data_retained(window, monkeypatch):
    window.notes_page.editor.setPlainText("Keep this safe")

    def fail():
        raise StorageError("disk full")

    monkeypatch.setattr(window.store, "save", fail)
    assert not window.persist()
    assert window.save_failed
    assert "Keep this safe" in window.store.data["notes"][0]["html"]
    assert window.statusBar().currentMessage() == window.t("save_error")
    monkeypatch.undo()


def test_resources_never_loaded():
    document = PrivateDocument()
    for url in ("file:///private.png", "https://example.org/tracker.png"):
        assert document.loadResource(2, QUrl(url)) is None


def test_settings_language_theme_rebuild_preserves_notes(window, qtbot):
    window.notes_page.editor.setPlainText("Preserve on settings change")
    page = window.settings_page
    page.language.setCurrentIndex(page.language.findData("en"))
    page.theme.setCurrentIndex(page.theme.findData("light"))
    page.apply()
    assert window.language == "en"
    assert window.layoutDirection() == Qt.LayoutDirection.LeftToRight
    assert window.store.data["theme"] == "light"
    assert window.notes_page.editor.toPlainText() == "Preserve on settings change"


def test_async_old_feed_result_cannot_replace_new_selection(window, qtbot, monkeypatch):
    page = window.reader_page
    page.feeds.extend(
        [{"name": "One", "url": "https://example.org/a"}, {"name": "Two", "url": "https://example.org/b"}]
    )
    page.combo.addItems(["One", "Two"])
    ready = threading.Event()

    def slow(_url):
        ready.wait(3)
        return [{"title": "Old", "summary": "Old item", "link": ""}]

    monkeypatch.setattr(network, "read_feed", slow)
    page.refresh()
    page.combo.setCurrentIndex(1)
    window.notes_page.editor.setPlainText("UI remains responsive")
    ready.set()
    qtbot.waitUntil(lambda: not page.busy)
    assert page.items == []
    assert page.list.count() == 0
    assert window.notes_page.editor.toPlainText() == "UI remains responsive"


def test_failed_events_are_not_cached(window, qtbot, monkeypatch):
    window.store.data["online_events"] = True

    def fail(_day):
        raise network.NetworkError("offline")

    monkeypatch.setattr(network, "read_events", fail)
    window.load_events()
    qtbot.waitUntil(lambda: not window.event_busy)
    assert window.day.isoformat() not in window.store.data["events"]
    assert window.events_label.text() == window.t("event_error")
    assert not window.event_timer.isActive()


def test_midnight_follows_today_but_keeps_browsed_date(window, monkeypatch):
    old = window.day
    following = calendar.shift_day(old, 1)
    monkeypatch.setattr(calendar, "today", lambda: following)
    window.tick()
    assert window.day == following
    window.day = old
    monkeypatch.setattr(calendar, "today", lambda: calendar.shift_day(following, 1))
    window.tick()
    assert window.day == old


def test_default_ui_is_independent_desktop_widgets(window):
    assert window.width() <= 460
    assert window.height() <= 430
    assert not window.findChildren(QTabWidget)
    assert window.quote_widget.isVisible()
    assert not window.note_widget.isVisible()
    for panel in window.panels.values():
        assert panel.isWindow()
        assert panel.parentWidget() is None
        assert panel.windowFlags() & Qt.WindowType.FramelessWindowHint
        assert panel.windowType() == Qt.WindowType.Tool


def test_calendar_can_hide_while_notes_and_reader_stay_visible(window):
    window.show_panel("notes")
    window.show_panel("reader")
    window.hide_panel("calendar")
    assert not window.isVisible()
    assert window.note_widget.isVisible()
    assert window.reader_widget.isVisible()
    window.reader_widget.close()
    assert not window.reader_widget.isVisible()
    assert window.note_widget.isVisible()
    assert window.store.data["widgets"]["reader"]["visible"] is False


def test_positions_sizes_and_visibility_survive_restart(window, qtbot):
    window.show_panel("notes")
    window.note_widget.move(40, 100)
    window.note_widget.resize(540, 350)
    window.move(90, 40)
    window.hide_panel("quote")
    assert window.persist()
    window.close()
    restored = Window(Store(window.store.directory))
    qtbot.addWidget(restored)
    restored.start()
    assert restored.pos() == QPoint(90, 40)
    assert restored.note_widget.pos() == QPoint(40, 100)
    assert restored.note_widget.width() == 540
    assert restored.note_widget.isVisible()
    assert not restored.quote_widget.isVisible()


def test_drag_handle_moves_only_the_target_widget(window):
    panel = window.quote_widget
    before = panel.pos()
    calendar_before = window.pos()
    local = QPointF(12, 12)
    origin = QPointF(panel.handle.mapToGlobal(QPoint(12, 12)))
    for kind, position, button, buttons in (
        (QEvent.Type.MouseButtonPress, origin, Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton),
        (QEvent.Type.MouseMove, origin + QPointF(30, 40), Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton),
        (
            QEvent.Type.MouseButtonRelease,
            origin + QPointF(30, 40),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
        ),
    ):
        event = QMouseEvent(kind, local, position, button, buttons, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(panel.handle, event)
    assert panel.pos() == before + QPoint(30, 40)
    assert window.pos() == calendar_before
    assert window.store.data["widgets"]["quote"]["x"] == panel.x()


def test_widget_settings_keep_notes_layout_and_content(window):
    window.show_panel("notes")
    window.note_widget.move(70, 110)
    window.notes_page.editor.setPlainText("Desktop note survives the appearance change")
    window.show_settings()
    page = window.settings_page
    page.background.setChecked(False)
    page.pin.setChecked(True)
    page.apply()
    assert window.note_widget.isVisible()
    assert window.note_widget.pos() == QPoint(70, 110)
    assert "survives" in window.notes_page.editor.toPlainText()
    assert window.store.data["widget_background"] is False
    assert window.note_widget.windowFlags() & Qt.WindowType.WindowStaysOnTopHint


def test_no_tray_keeps_a_recoverable_widget(window):
    window.tray.hide()
    window.hide_panel("calendar")
    window.hide_panel("quote")
    assert window.isVisible()
    assert window.store.data["widgets"]["calendar"]["visible"] is True


def test_compact_calendar_hides_details_but_not_other_widgets(window):
    quote_before = window.quote_widget.isVisible()
    window.toggle_compact()
    assert window.date_details.isHidden()
    assert window.shortcut_bar.isHidden()
    assert window.height() < 260
    assert window.quote_widget.isVisible() == quote_before
