import copy
import json

import pytest

from shamsical.storage import DEFAULTS, StorageError, Store, validate


def test_roundtrip_unicode_and_previous_backup(tmp_path):
    store = Store(tmp_path)
    store.data["notes"] = [{"title": "روز نو", "html": "<p>سلام</p>"}]
    store.save()
    store.data["notes"][0]["html"] = "<p>دوباره سلام</p>"
    store.save()
    assert Store(tmp_path).data == store.data
    assert "دوباره" not in Store.read(tmp_path / "workspace.json.bak")["notes"][0]["html"]
    assert not list(tmp_path.glob(".workspace-*"))


@pytest.mark.parametrize("content", ["{bad", "[]", '{"schema":2}', '{"schema":1,"notes":[{}]}'])
def test_corrupt_file_is_never_overwritten(tmp_path, content):
    path = tmp_path / "workspace.json"
    path.write_text(content)
    with pytest.raises(StorageError):
        Store(tmp_path)
    assert path.read_text() == content


def test_failed_atomic_replace_keeps_original(tmp_path, monkeypatch):
    store = Store(tmp_path)
    store.save()
    original = store.path.read_bytes()
    store.data["quotes"] = ["new"]

    def fail(*_):
        raise PermissionError("disk failure")

    monkeypatch.setattr("shamsical.storage.os.replace", fail)
    with pytest.raises(StorageError):
        store.save()
    assert store.path.read_bytes() == original


@pytest.mark.parametrize(
    "key,value",
    [
        ("api_key", "private"),
        ("font_size", "large"),
        ("online_events", "false"),
        ("events", {"day": [42]}),
        ("language", "unknown"),
    ],
)
def test_invalid_or_unexpected_fields_rejected(key, value):
    data = copy.deepcopy(DEFAULTS)
    data[key] = value
    with pytest.raises(StorageError):
        validate(data)


def test_export_refuses_live_data_file(tmp_path):
    store = Store(tmp_path)
    store.save()
    with pytest.raises(StorageError):
        store.export(store.path)
    store.export(tmp_path / "export.json")
    assert json.loads((tmp_path / "export.json").read_text(encoding="utf-8"))["schema"] == 1
