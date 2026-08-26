"""Tests for the MCP server tools (mcp_server.py).

The @mcp.tool()-decorated functions stay directly callable, so we exercise them
as plain functions: classification, every report type, and the save/get/list
round-trip. A guard test asserts the tool's report-type Literal never drifts
from the engine's reports.REPORT_TYPES (the single source of truth).
"""

import sys
import typing
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mcp_server as m  # noqa: E402
from app import reports, storage  # noqa: E402

HIRING = {"eu_market": True, "provider_role": "provider",
          "hr_usecases": ["employment"], "hr_does_profiling": True,
          "sys_name": "MCP test system"}


@pytest.fixture(autouse=True)
def _tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)


def test_get_questionnaire_returns_schema():
    q = m.get_questionnaire()
    assert "sections" in q and q["sections"]


def test_classify_ai_system_is_deterministic_high():
    r = m.classify_ai_system(HIRING)
    assert r["tier"] == "high"
    assert r["high_risk_obligations"]


def test_security_and_data_security_tools_run():
    assert "risks" in m.classify_ai_security(HIRING)
    assert "risks" in m.assess_data_security(HIRING)


def test_generate_report_covers_every_type():
    for rtype in reports.REPORT_TYPES:
        md = m.generate_report(HIRING, rtype)
        assert isinstance(md, str) and len(md) > 200


def test_save_requires_confirmation():
    # Without confirmed=True nothing is persisted (HITL enforced as a contract).
    out = m.save_assessment(HIRING)
    assert out["saved"] is False
    assert m.list_assessments() == []


def test_save_get_list_roundtrip():
    saved = m.save_assessment(HIRING, confirmed=True)
    aid = saved["id"]
    assert saved["saved"] is True and saved["classification"]["tier"] == "high"
    loaded = m.get_assessment(aid)
    assert loaded["id"] == aid and loaded["answers"]["sys_name"] == "MCP test system"
    assert any(row["id"] == aid for row in m.list_assessments())


def test_generate_report_by_saved_id():
    aid = m.save_assessment(HIRING, confirmed=True)["id"]
    md = m.generate_report(report_type="compliance", assessment_id=aid)
    assert "Conformity Tracker" in md


def test_get_assessment_missing_raises():
    with pytest.raises(ValueError):
        m.get_assessment("no-such-id")


def test_scan_repository_tool():
    result = m.scan_repository(str(ROOT / "app"))
    assert "ai_detected" in result


def test_report_type_literal_matches_engine():
    """The generate_report Literal must list exactly reports.REPORT_TYPES, so
    the MCP surface can't silently drift when a report type is added."""
    hints = typing.get_type_hints(m.generate_report)
    literal_values = set(typing.get_args(hints["report_type"]))
    assert literal_values == set(reports.REPORT_TYPES), (
        "MCP generate_report Literal is out of sync with reports.REPORT_TYPES"
    )
