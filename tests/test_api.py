"""API smoke tests (FastAPI TestClient). Runs with pytest.

Guards the endpoints that the frontend depends on, including the /api/examples
robustness against non-object JSON files in examples/ (e.g. golden_set.json).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app import main as main_module  # noqa: E402
from app.llm import budget  # noqa: E402
from app.llm.config import settings  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def test_examples_endpoint_ok_and_well_formed():
    r = client.get("/api/examples")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    # Only real example objects (with answers) are returned; array files skipped.
    for ex in data:
        assert ex["answers"].get("sys_name")
        assert ex["tier_label"]


def test_ai_status_endpoint_reports_anthropic_fallback_without_key(tmp_path, monkeypatch):
    monkeypatch.setenv("AIACT_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(settings, "provider", "anthropic")
    budget.reset_for_tests()
    try:
        r = client.get("/api/ai/status")
        assert r.status_code == 200
        body = r.json()
        assert body["provider"] == "replay"
        assert body["fallback_from"] == "anthropic"
        assert body["fallback_reason"] == "unavailable"
        assert "budget" in body
    finally:
        budget.reset_for_tests()


def test_questionnaire_endpoint():
    r = client.get("/api/questionnaire")
    assert r.status_code == 200
    assert len(r.json()["sections"]) == 13


def test_assess_rejects_blank_name_and_oversized_free_text():
    blank = client.post("/api/assess", json={"answers": {"sys_name": "   "}})
    assert blank.status_code == 422
    assert "non-empty system name" in str(blank.json())

    oversized = client.post("/api/assess", json={"answers": {
        "sys_name": "Bounded", "sys_description": "x" * 10_001}})
    assert oversized.status_code == 422
    assert "at most 10000 characters" in str(oversized.json())

    prefill = client.post("/api/ai/prefill", json={"description": "x" * 10_001})
    assert prefill.status_code == 422

    nested = "value"
    for _ in range(10):
        nested = {"child": nested}
    too_deep = client.post("/api/assess", json={"answers": {
        "sys_name": "Nested", "dg_datasets": nested}})
    assert too_deep.status_code == 422
    assert "nested at most" in str(too_deep.json())


def test_demo_submissions_are_stateless_and_inventory_is_curated(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "DEMO_MODE", True)
    monkeypatch.setattr(main_module.storage, "DATA_DIR", tmp_path)

    # Even a pre-existing private/local record is not exposed by demo endpoints.
    main_module.storage.save({
        "id": "private-local-record", "created_at": main_module.storage.now_iso(),
        "answers": {"sys_name": "Must stay private"},
        "classification": {}, "security": {},
    })
    before = set(tmp_path.glob("*.json"))

    result = client.post("/api/assess", json={"answers": {
        "sys_name": "Visitor Secret", "eu_market": True}})
    assert result.status_code == 200
    body = result.json()
    assert body["persisted"] is False
    assert set(tmp_path.glob("*.json")) == before
    assert client.get(f"/api/assessments/{body['id']}").status_code == 404

    portfolio = client.get("/api/portfolio").json()
    names = {row["sys_name"] for row in portfolio["systems"]}
    assert "Visitor Secret" not in names
    assert "Must stay private" not in names
    assert names  # shipped synthetic examples remain usable
    assert "Visitor Secret" not in client.get("/api/export.csv").text
    assert "Must stay private" not in client.get("/api/register.csv").text

    example_id = portfolio["systems"][0]["id"]
    assert client.get(f"/api/assessments/{example_id}").status_code == 200

    report = client.post("/api/report?type=risk", json={"answers": {
        "sys_name": "Visitor Secret", "eu_market": True}})
    assert report.status_code == 200
    assert len(report.json()["markdown"]) > 200


def test_timeline_endpoint_for_countdown():
    r = client.get("/api/timeline")
    assert r.status_code == 200
    milestones = r.json()["milestones"]
    assert len(milestones) >= 3
    for m in milestones:
        assert m["date"] and m["label"] and m["basis"]
        # ISO date the frontend can parse: YYYY-MM-DD
        assert len(m["date"]) == 10 and m["date"][4] == "-"
    # Digital Omnibus (Reg. (EU) 2026/1744): Annex III high-risk is 2 Dec 2027,
    # and no milestone may still advertise Annex III for 2 Aug 2026.
    by_date = {m["date"]: m["label"] for m in milestones}
    assert "Annex III" in by_date["2027-12-02"]
    assert "Annex III" not in by_date.get("2026-08-02", "")
    assert r.json()["last_reviewed"] and r.json()["amendments"]


def test_assess_report_delete_roundtrip():
    r = client.post("/api/assess", json={
        "answers": {"eu_market": True, "sys_name": "Roundtrip", "p_social_scoring": True}})
    assert r.status_code == 200
    body = r.json()
    assert body["classification"]["tier"] == "prohibited"

    rep = client.get(f"/api/assessments/{body['id']}/report", params={"type": "risk"})
    assert rep.status_code == 200
    assert "Risk Assessment" in rep.json()["markdown"]

    # clean up the assessment this test created
    assert client.delete(f"/api/assessments/{body['id']}").status_code == 200


def test_unknown_report_type_rejected():
    r = client.post("/api/assess", json={"answers": {"eu_market": True, "sys_name": "X"}})
    aid = r.json()["id"]
    assert client.get(f"/api/assessments/{aid}/report", params={"type": "bogus"}).status_code == 400
    client.delete(f"/api/assessments/{aid}")


def test_new_tier3_report_types_render():
    r = client.post("/api/assess", json={"answers": {
        "eu_market": True, "sys_name": "Tier3 Demo", "sec_is_llm": True,
        "sec_public": True, "arch_data_scope": "all-users",
        "arch_access_control_layer": "llm-prompt"}})
    aid = r.json()["id"]
    for rtype in ("stride", "incident", "modelcard"):
        rep = client.get(f"/api/assessments/{aid}/report", params={"type": rtype})
        assert rep.status_code == 200, rtype
        assert len(rep.json()["markdown"]) > 200
    client.delete(f"/api/assessments/{aid}")


def test_report_lang_nl_and_validation():
    r = client.post("/api/assess", json={"answers": {
        "eu_market": True, "sys_name": "Lang Demo", "t_interacts_humans": True}})
    aid = r.json()["id"]
    nl = client.get(f"/api/assessments/{aid}/report?type=risk&lang=nl")
    assert nl.status_code == 200 and "Samenvatting (NL)" in nl.json()["markdown"]
    en = client.get(f"/api/assessments/{aid}/report?type=risk")
    assert "Samenvatting (NL)" not in en.json()["markdown"]
    assert client.get(f"/api/assessments/{aid}/report?type=risk&lang=de").status_code == 400
    client.delete(f"/api/assessments/{aid}")


def test_portfolio_rollup_and_csv_columns():
    r = client.post("/api/assess", json={"answers": {
        "eu_market": True, "sys_name": "Rollup Demo", "t_interacts_humans": True}})
    aid = r.json()["id"]

    pf = client.get("/api/portfolio")
    assert pf.status_code == 200
    body = pf.json()
    assert body["count"] >= 1
    assert isinstance(body["tier_distribution"], dict)
    row = next(s for s in body["systems"] if s["id"] == aid)
    assert "obligations_date" in row
    assert row["art50_disclosure"] is True   # Art. 50(1) interaction duty

    for col in ("forensic_score", "forensic_band", "datagov_gaps_high", "gov_status",
                "next_review", "review_overdue", "documentation_complete"):
        assert col in row, col
    assert "overdue_review_count" in body and "incomplete_count" in body

    csv_text = client.get("/api/export.csv").text
    header = csv_text.splitlines()[0]
    for col in ("obligations_date", "art50_disclosure", "has_high_risk_obligations",
                "forensic_readiness", "governance_status", "review_overdue"):
        assert col in header

    reg = client.get("/api/register.csv")
    assert reg.status_code == 200
    reg_header = reg.text.splitlines()[0]
    for col in ("name", "purpose", "risk_tier", "human_oversight", "contact",
                "governance_status", "next_review", "in_public_register"):
        assert col in reg_header
    assert "Rollup Demo" in reg.text

    client.delete(f"/api/assessments/{aid}")
