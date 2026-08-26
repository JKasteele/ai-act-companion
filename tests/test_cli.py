"""Tests for the `ai-act` CLI (app/cli.py).

The CLI is a shipped entry point and the surface the MCP/skill flows lean on, so
exercise every subcommand end-to-end against the synthetic examples. Output is
captured; storage is redirected to a temp dir so nothing touches the real data/.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import cli, storage  # noqa: E402

EXAMPLES = ROOT / "examples"
HIRING = str(EXAMPLES / "hiring_cv_screening.json")


@pytest.fixture(autouse=True)
def _tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)


def test_questionnaire_emits_valid_json(capsys):
    assert cli.main(["questionnaire"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert "sections" in out and out["title"]


def test_classify_prints_tier(capsys):
    assert cli.main(["classify", "--answers", HIRING]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["classification"]["tier"] == "high"


def test_classify_from_stdin(capsys, monkeypatch):
    import io
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"eu_market": True})))
    assert cli.main(["classify", "--answers", "-"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["classification"]["tier"] == "minimal"


def test_classify_save_persists_and_lists(capsys):
    assert cli.main(["classify", "--answers", HIRING, "--save"]) == 0
    saved = json.loads(capsys.readouterr().out)
    assert saved["id"]
    # list now shows exactly that saved assessment.
    assert cli.main(["list"]) == 0
    listing = json.loads(capsys.readouterr().out)
    assert any(row["id"] == saved["id"] for row in listing)


def test_report_from_answers_stdout(capsys):
    assert cli.main(["report", "--answers", HIRING, "--type", "risk"]) == 0
    md = capsys.readouterr().out
    assert md.startswith("# AI Risk Assessment")
    assert "TalentMatch CV screening" in md


def test_report_to_file(tmp_path, capsys):
    out_path = tmp_path / "dpia.md"
    assert cli.main(["report", "--answers", HIRING, "--type", "dpia",
                     "--out", str(out_path)]) == 0
    assert out_path.read_text(encoding="utf-8").startswith("# ")
    assert "Wrote" in capsys.readouterr().out


def test_report_missing_assessment_returns_1(capsys):
    assert cli.main(["report", "--assessment", "does-not-exist", "--type", "risk"]) == 1
    assert "not found" in capsys.readouterr().err.lower()


def test_report_by_saved_id_roundtrip(capsys):
    cli.main(["classify", "--answers", HIRING, "--save"])
    aid = json.loads(capsys.readouterr().out)["id"]
    assert cli.main(["report", "--assessment", aid, "--type", "compliance"]) == 0
    assert "Conformity Tracker" in capsys.readouterr().out


def test_scan_repo_json(capsys):
    # Scan the app package (fast, and it plainly uses ML/AI vocabulary).
    assert cli.main(["scan", str(ROOT / "app"), "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert "ai_detected" in out
