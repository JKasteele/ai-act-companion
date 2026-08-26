"""Round-trip and robustness tests for the JSON file storage (app/storage.py).

Path-traversal defence is covered in test_security.py; here we assert the
save/load/list/delete lifecycle, the single-read load_all(), atomic writes (no
temp files left behind, no corruption), and that a malformed file is skipped
rather than crashing the listing.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import storage  # noqa: E402


@pytest.fixture(autouse=True)
def _tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    return tmp_path


def _record(name="Demo"):
    return {
        "id": storage.new_id(name),
        "created_at": storage.now_iso(),
        "answers": {"sys_name": name},
        "classification": {"tier": "high", "tier_label": "High risk"},
        "security": {"risks": [{"id": "LLM01:2025"}]},
    }


def test_new_id_is_valid_slug():
    assert storage.is_valid_id(storage.new_id("Some System!!"))


def test_save_load_roundtrip():
    rec = _record()
    storage.save(rec)
    assert storage.load(rec["id"]) == rec


def test_delete_removes_record():
    rec = _record()
    storage.save(rec)
    assert storage.delete(rec["id"]) is True
    assert storage.load(rec["id"]) is None
    assert storage.delete(rec["id"]) is False  # already gone


def test_list_all_summarises_newest_first():
    a = _record("Alpha")
    a["created_at"] = "2026-01-01T00:00:00+00:00"
    b = _record("Beta")
    b["created_at"] = "2026-06-01T00:00:00+00:00"
    storage.save(a)
    storage.save(b)
    rows = storage.list_all()
    assert [r["sys_name"] for r in rows] == ["Beta", "Alpha"]
    assert rows[0]["security_risks"] == 1 and rows[0]["tier"] == "high"


def test_load_all_returns_full_dicts_once(_tmp_data_dir):
    storage.save(_record("One"))
    full = storage.load_all()
    assert len(full) == 1 and full[0]["classification"]["tier"] == "high"


def test_save_is_atomic_leaves_no_temp_files(_tmp_data_dir):
    rec = _record()
    storage.save(rec)
    leftovers = list(_tmp_data_dir.glob("*.tmp"))
    assert not leftovers, f"atomic save left temp files: {leftovers}"
    assert list(_tmp_data_dir.glob("*.json")) == [_tmp_data_dir / f"{rec['id']}.json"]


def test_malformed_file_is_skipped_not_fatal(_tmp_data_dir):
    storage.save(_record("Good"))
    (_tmp_data_dir / "broken.json").write_text("{not valid json", encoding="utf-8")
    rows = storage.list_all()  # must not raise
    assert len(rows) == 1 and rows[0]["sys_name"] == "Good"


def test_load_rejects_invalid_id():
    assert storage.load("../etc/passwd") is None
    assert storage.load("bad id with spaces") is None
