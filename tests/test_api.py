"""API smoke tests (FastAPI TestClient). Runs with pytest.

Guards the endpoints that the frontend depends on, including the /api/examples
robustness against non-object JSON files in examples/ (e.g. golden_set.json).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

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


def test_questionnaire_endpoint():
    r = client.get("/api/questionnaire")
    assert r.status_code == 200
    assert len(r.json()["sections"]) == 10


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

    csv_text = client.get("/api/export.csv").text
    header = csv_text.splitlines()[0]
    for col in ("obligations_date", "art50_disclosure", "has_high_risk_obligations"):
        assert col in header

    client.delete(f"/api/assessments/{aid}")
