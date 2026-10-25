"""Startup for the independent ShamsiCal desktop widget suite."""

import argparse
import sys
from pathlib import Path

from PyQt6.QtCore import QLockFile, QStandardPaths, QTimer
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication, QMessageBox

from . import __version__
from .desktop import Window
from .storage import StorageError, Store


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
    app.setQuitOnLastWindowClosed(False)
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
        window = Window(store, quit_application=True)
        window.start()
        if args.smoke_test:
            QTimer.singleShot(400, window.close)
        return app.exec()
    finally:
        lock.unlock()
        if temporary:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
