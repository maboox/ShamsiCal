"""Capture actual independent widgets, with only isolated synthetic demo data."""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import jdatetime
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QImage, QLinearGradient, QPainter
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


def capture(suite, language):
    for key in ("calendar", "quote", "notes", "reader"):
        suite.show_panel(key)
    suite.resize(380, 330)
    suite.quote_widget.resize(320, 165)
    suite.note_widget.resize(520, 400)
    suite.reader_widget.resize(360, 460)
    page = suite.reader_page
    page.feeds.append({"name": "Demo RSS", "url": "https://example.org/feed"})
    page.combo.addItem("Demo RSS")
    page.items = [
        {
            "title": "خبرخوانی به انتخاب تو" if language == "fa" else "Your reading, your choice",
            "summary": "این متن نمونه است. خبرها فقط با درخواست شما دریافت می‌شوند؛ خبری خودکار باز یا دریافت نمی‌شود."
            if language == "fa"
            else "This is sample content. Feeds load only when you choose Refresh. Nothing is fetched automatically.",
            "link": "https://example.org/article",
        },
        {
            "title": "یک جای کوچک برای خبرهای مهم"
            if language == "fa"
            else "A little space for the stories that matter",
            "summary": "Demo",
            "link": "",
        },
    ]
    page.list.addItems([item["title"] for item in page.items])
    page.list.setCurrentRow(0)
    page.status.setText("Demo RSS")
    app.processEvents()
    suite.grab().save(str(output / f"calendar-{language}.png"))
    suite.note_widget.grab().save(str(output / f"notes-{language}.png"))
    image = QImage(1420, 680, QImage.Format.Format_ARGB32)
    painter = QPainter(image)
    gradient = QLinearGradient(0, 0, 1420, 680)
    gradient.setColorAt(0, QColor("#14283f" if language == "fa" else "#e2ecf8"))
    gradient.setColorAt(1, QColor("#244d70" if language == "fa" else "#c8dbee"))
    painter.fillRect(image.rect(), gradient)
    painter.setPen(QColor("#ddecff" if language == "fa" else "#1a3a5e"))
    painter.setFont(QFont("Vazirmatn", 17, QFont.Weight.Bold))
    painter.drawText(
        35,
        42,
        "ShamsiCal · ویجت‌های مستقل دسکتاپ" if language == "fa" else "ShamsiCal · Independent desktop widgets",
    )
    for key, x, y in (("notes", 35, 80), ("reader", 585, 80), ("calendar", 980, 80), ("quote", 1040, 440)):
        painter.drawPixmap(x, y, suite.panels[key].grab())
    painter.setFont(QFont("Vazirmatn", 10))
    painter.drawText(
        35, 650, "Actual Qt widgets · Synthetic demo content · Positions chosen for this preview"
    )
    painter.end()
    image.save(str(output / f"widgets-{language}.png"))


with tempfile.TemporaryDirectory() as directory:
    store = Store(directory)
    store.data["notes"] = [
        {
            "title": "یک شروع تازه",
            "html": "<h3>ایده‌های این هفته</h3><p>برای چیزهای مهم، جا باز کن.</p><p>☑ مرتب‌کردن فضای کار</p><p>☐ بیست دقیقه مطالعه</p><p>☐ برنامه‌ریزی برای فردا</p>",
        }
    ]
    suite = Window(store)
    suite.day = jdatetime.date(1405, 8, 3)
    suite.start()
    suite.render_date()
    capture(suite, "fa")
    suite.toggle_compact()
    app.processEvents()
    suite.grab().save(str(output / "compact-fa.png"))
    suite.store.data.update({"language": "en", "theme": "light", "compact": False, "feeds": []})
    suite.rebuild()
    capture(suite, "en")
    suite.close()
