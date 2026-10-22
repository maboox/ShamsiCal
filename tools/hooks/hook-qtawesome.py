"""Bundle the one icon family the app loads, with its own MIT notice."""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files(
    "qtawesome", includes=["fonts/phosphor-1.3.0.ttf", "fonts/phosphor-charmap-1.3.0.json"]
)
