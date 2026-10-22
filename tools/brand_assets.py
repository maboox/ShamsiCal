"""Original code-drawn identity assets. No generated or stock UI mockups."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QImage, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QApplication

app = QApplication([])
root = Path(__file__).resolve().parents[1]
for font in (root / "shamsical/assets/fonts").glob("*.ttf"):
    QFontDatabase.addApplicationFont(str(font))


def calendar_mark(painter, x, y, size):
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#245dba"))
    painter.drawRoundedRect(QRectF(x, y, size, size), size * 0.22, size * 0.22)
    painter.setBrush(QColor("#ddecff"))
    painter.drawRoundedRect(
        QRectF(x + size * 0.20, y + size * 0.23, size * 0.6, size * 0.58), size * 0.07, size * 0.07
    )
    painter.setPen(QPen(QColor("#245dba"), size * 0.045))
    painter.drawLine(int(x + size * 0.23), int(y + size * 0.40), int(x + size * 0.77), int(y + size * 0.40))
    for position in (0.33, 0.67):
        painter.drawLine(
            int(x + size * position), int(y + size * 0.16), int(x + size * position), int(y + size * 0.31)
        )
    painter.setPen(QColor("#245dba"))
    painter.setFont(QFont("Vazirmatn", int(size * 0.20), QFont.Weight.Bold))
    painter.drawText(QRectF(x, y + size * 0.44, size, size * 0.34), Qt.AlignmentFlag.AlignCenter, "ش")


image = QImage(1440, 440, QImage.Format.Format_ARGB32)
p = QPainter(image)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
gradient = QLinearGradient(0, 0, 1440, 440)
gradient.setColorAt(0, QColor("#0b1220"))
gradient.setColorAt(1, QColor("#153d71"))
p.fillRect(image.rect(), gradient)
p.setPen(QPen(QColor("#2b5687"), 1))
p.setBrush(Qt.BrushStyle.NoBrush)
for radius in (200, 290, 380):
    p.drawEllipse(QRectF(1300 - radius, 220 - radius, radius * 2, radius * 2))
calendar_mark(p, 1120, 118, 210)
p.setPen(QColor("#a6cbff"))
p.setFont(QFont("Vazirmatn", 13, QFont.Weight.Bold))
p.drawText(80, 75, "PERSIAN CALENDAR  /  YOUR PRIVATE DESKTOP SPACE")
p.setPen(QColor("#f2f7ff"))
p.setFont(QFont("Vazirmatn", 62, QFont.Weight.Bold))
p.drawText(76, 184, "ShamsiCal")
p.setPen(QColor("#a6cbff"))
p.setFont(QFont("Vazirmatn", 24))
p.drawText(80, 246, "A little clarity for every day.")
p.setPen(QColor("#f2f7ff"))
p.setFont(QFont("Vazirmatn", 23))
p.drawText(QRectF(80, 270, 820, 58), Qt.AlignmentFlag.AlignLeft, "روزت را روشن‌تر شروع کن")
p.setPen(QColor("#b8cbe5"))
p.setFont(QFont("Vazirmatn", 13))
p.drawText(80, 384, "JALALI · GREGORIAN · HIJRI     /     NOTES · RSS     /     فارسی + ENGLISH")
p.end()
images = root / "docs/images"
images.mkdir(parents=True, exist_ok=True)
image.save(str(images / "banner.png"))
icon = QImage(256, 256, QImage.Format.Format_ARGB32)
icon.fill(Qt.GlobalColor.transparent)
p = QPainter(icon)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
calendar_mark(p, 8, 8, 240)
p.end()
icon.save(str(root / "shamsical/assets/app.png"))
icon.save(str(root / "shamsical/assets/app.ico"))
print("Brand assets created")
