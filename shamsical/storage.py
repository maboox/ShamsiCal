"""Versioned local data, atomic writes, and explicit recovery on corruption."""

import copy
import json
import os
import shutil
import tempfile
from pathlib import Path

MAX_DATA_BYTES = 16 * 1024 * 1024
DEFAULTS = {
    "schema": 1,
    "language": "fa",
    "theme": "ocean",
    "font_size": 11,
    "online_events": False,
    "notes": [],
    "feeds": [],
    "events": {},
    "quotes": ["هر روز، فرصتی برای یک شروع تازه است.", "قدم‌های کوچک، مسیرهای بزرگ می‌سازند."],
    "quote_frequency": "daily",
    "compact": False,
}


class StorageError(Exception):
    """The original data remains untouched; the user must recover it."""


def validate(data):
    if not isinstance(data, dict) or type(data.get("schema")) is not int or data.get("schema") != 1:
        raise StorageError("Unsupported or invalid data schema")
    if set(data) - set(DEFAULTS) - {"geometry", "full_size"}:
        raise StorageError("Unknown workspace fields")
    for key, kind in {"notes": list, "feeds": list, "quotes": list, "events": dict}.items():
        if not isinstance(data.get(key, DEFAULTS[key]), kind):
            raise StorageError(f"Invalid {key} data")
    for note in data.get("notes", []):
        if not isinstance(note, dict) or not all(isinstance(note.get(k), str) for k in ("title", "html")):
            raise StorageError("Invalid note data")
    for feed in data.get("feeds", []):
        if not isinstance(feed, dict) or not all(isinstance(feed.get(k), str) for k in ("name", "url")):
            raise StorageError("Invalid feed data")
    if not all(isinstance(q, str) for q in data.get("quotes", [])):
        raise StorageError("Invalid quote data")
    for key, events in data.get("events", {}).items():
        if (
            not isinstance(key, str)
            or not isinstance(events, list)
            or not all(isinstance(e, str) for e in events)
        ):
            raise StorageError("Invalid cached events")
    if data.get("language", "fa") not in ("fa", "en") or data.get("theme", "ocean") not in ("ocean", "light"):
        raise StorageError("Invalid language or theme")
    if type(data.get("font_size", 11)) is not int or not 9 <= data.get("font_size", 11) <= 16:
        raise StorageError("Invalid font size")
    for key in ("online_events", "compact"):
        if type(data.get(key, False)) is not bool:
            raise StorageError(f"Invalid {key} preference")
    if data.get("quote_frequency", "daily") not in ("daily", "hourly", "weekly"):
        raise StorageError("Invalid quote frequency")
    return {**copy.deepcopy(DEFAULTS), **data}


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / "workspace.json"
        self.data = copy.deepcopy(DEFAULTS)
        if self.path.exists():
            self.data = self.read(self.path)

    @staticmethod
    def read(path):
        try:
            if Path(path).stat().st_size > MAX_DATA_BYTES:
                raise StorageError("Data file exceeds the 16 MiB limit")
            return validate(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError, UnicodeError, ValueError) as error:
            raise StorageError("Cannot read workspace data; recover from a backup") from error

    def save(self):
        validate(self.data)
        payload = json.dumps(self.data, ensure_ascii=False, indent=2).encode("utf-8")
        if len(payload) > MAX_DATA_BYTES:
            raise StorageError("Workspace exceeds 16 MiB; export and shorten large notes")
        self.directory.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=self.directory, prefix=".workspace-", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            if self.path.exists():
                self.read(self.path)
                backup = self.path.with_suffix(".json.bak")
                backup_tmp = self.path.with_suffix(".json.bak.tmp")
                shutil.copyfile(self.path, backup_tmp)
                os.replace(backup_tmp, backup)
            os.replace(temporary, self.path)
        except OSError as error:
            raise StorageError("Cannot save workspace; check available space and permissions") from error
        finally:
            Path(temporary).unlink(missing_ok=True)

    def export(self, target):
        target = Path(target).resolve()
        if target in (self.path.resolve(), self.path.with_suffix(".json.bak").resolve()):
            raise StorageError("Choose an export destination outside the active data files")
        with target.open("x", encoding="utf-8") as stream:
            json.dump(self.data, stream, ensure_ascii=False, indent=2)
