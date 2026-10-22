# Third-party notices

ShamsiCal source is GPL-3.0-or-later. Dependencies retain their own copyright and license terms. The portable Windows ZIP includes available dependency license files under `licenses/` plus the font's OFL text. Source archives for ShamsiCal are available from its matching GitHub tag. Upstream project links below provide dependency source and full notices.

| Component | Purpose | License / upstream |
| --- | --- | --- |
| PyQt6 and PyQt6-sip | Qt Python bindings | GPL v3 / [Riverbank](https://www.riverbankcomputing.com/software/pyqt/) |
| Qt 6 (PyQt6-Qt6 wheel) | Desktop UI runtime | LGPL/GPL and component-specific notices / [Qt](https://www.qt.io/licensing/open-source-lgpl-obligations) |
| jdatetime | Jalali date API | PSF-2.0 / [python-jalali](https://github.com/slashmili/python-jalali) |
| jalali-core | Jalali conversion core | LGPL / [jalali-core](https://github.com/slashmili/jalali-core) |
| hijridate | Umm al-Qura conversion | MIT / [hijridate](https://github.com/dralshehri/hijridate) |
| feedparser | RSS/Atom parsing | BSD-2-Clause / [feedparser](https://github.com/kurtmckee/feedparser) |
| feedparser-sgmllib | SGML parser | PSF-2.0 / [feedparser-sgmllib](https://github.com/python-syndication/feedparser-sgmllib) |
| urllib3 | HTTPS transport | MIT / [urllib3](https://github.com/urllib3/urllib3) |
| certifi | CA trust bundle | MPL 2.0 / [certifi](https://github.com/certifi/python-certifi) |
| QtAwesome, QtPy | Icon font rendering and Qt compatibility | MIT / [QtAwesome](https://github.com/spyder-ide/qtawesome), [QtPy](https://github.com/spyder-ide/qtpy) |
| Phosphor 1.3 icon font | Interface icons | MIT / [Phosphor](https://github.com/phosphor-icons/phosphor-icons) |
| packaging | Runtime compatibility metadata | Apache 2.0 / BSD / [packaging](https://github.com/pypa/packaging) |
| Vazirmatn 33.003 | Bundled Persian/Latin typography | SIL OFL 1.1 / [Vazirmatn](https://github.com/rastikerdar/vazirmatn); [bundled OFL](shamsical/assets/fonts/OFL.txt) |
| Python | Interpreter in standalone distribution | PSF license / [Python](https://docs.python.org/3/license.html) |
| PyInstaller bootloader | Standalone launcher | GPL with bootloader exception / [PyInstaller](https://pyinstaller.org/en/stable/license.html) |

Vazirmatn font files are unmodified, downloaded from the upstream `v33.003` tag. The app loads them for its own process and does not install fonts into the operating system. The blue calendar mark and banner are original project assets drawn by `tools/brand_assets.py`.

The optional event and AI services are not bundled dependencies; users are subject to their respective service terms. No affiliation with those providers is implied.
