"""Load only Phosphor in-process; do not install fonts into Windows."""

from pathlib import Path

import qtawesome
from qtawesome.iconic_font import IconicFont

_font = None


def icon(name, **options):
    global _font
    if _font is None:
        directory = str(Path(qtawesome.__file__).parent / "fonts")
        _font = IconicFont(("ph", "phosphor-1.3.0.ttf", "phosphor-charmap-1.3.0.json", directory))
    return _font.icon(name, **options)
