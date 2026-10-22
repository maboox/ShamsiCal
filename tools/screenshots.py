"""Capture actual Qt widgets using an isolated, synthetic workspace."""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import jdatetime
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication

from shamsical.app import Window
from shamsical.storage import Store

app = QApplication([])
app.setStyle("Fusion")
project = Path(__file__).resolve().parents[1]
for font in (project / "shamsical/assets/fonts").glob("*.ttf"):
    QFontDatabase.addApplicationFont(str(font))
app.setFont(QFont("Vazirmatn", 11))
output = project / "docs/images"
output.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as directory:
    store = Store(directory)
    store.data["notes"] = [
        {
            "title": "یک شروع تازه",
            "html": "<h2>ایده‌های این هفته</h2><p>برای چیزهای مهم، جا باز کن.</p><p>☑ مرتب‌کردن فضای کار</p><p>☐ بیست دقیقه مطالعه</p><p>☐ برنامه‌ریزی برای فردا</p>",
        }
    ]
    window = Window(store)
    window.resize(1140, 940)
    window.day = jdatetime.date(1405, 7, 29)
    window.render_date()
    window.show()
    app.processEvents()
    window.grab().save(str(output / "calendar-fa.png"))
    window.tabs.setCurrentWidget(window.notes_page)
    app.processEvents()
    window.grab().save(str(output / "notes-fa.png"))
    window.store.data.update({"language": "en", "theme": "light"})
    window.rebuild()
    app.processEvents()
    window.grab().save(str(output / "calendar-en.png"))
    window.close()
