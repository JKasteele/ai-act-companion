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
    assert len(r.json()["sections"]) == 9


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
