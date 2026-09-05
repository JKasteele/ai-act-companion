"""Scenario provenance and adversarial proposal validation; no live-model score."""

import pytest

from app.workspace.scenarios import scenarios
from app.workspace.toolkit import QUESTIONS, catalogue, validate_answers, validate_proposals


def test_three_dossiers_have_resolvable_sources_and_valid_proposals():
    cases = scenarios()
    assert [c["id"] for c in cases] == ["meridian", "boreal", "northstar"]
    for case in cases:
        assert case["synthetic"]
        assert len(case["documents"]) >= 4 and len(case["findings"]) == 3
        sources = {f"{d['id']}:{s['id']}": s["text"] for d in case["documents"] for s in d["sections"]}
        assert len(sources) == sum(len(d["sections"]) for d in case["documents"])
        for f in case["findings"]:
            assert len(f["sources"]) >= 2 and set(f["sources"]) <= sources.keys()
            assert f["owner"] and f["completion"] and f["action"]
        assert validate_proposals(case["proposals"], sources) == case["proposals"]
        assert set(case["reports"]) <= {r["id"] for r in catalogue()["reports"]}
        answers = {p["field"]: p["value"] for p in case["proposals"]}
        assert validate_answers(answers) == answers
        # Current permissions are disputed; do not quietly choose a value.
        if case["id"] == "boreal":
            assert "arch_api_write" not in answers
        if case["id"] == "northstar":
            assert "autonomy_level" not in answers
    cases[0]["documents"].clear()
    assert scenarios()[0]["documents"]


VALID = {"field": "provider_role", "value": "deployer", "source": "brief:purpose",
         "quote": "We deploy a vendor model.", "reason": "The owner explicitly states the role."}
SOURCES = {"brief:purpose": "We deploy a vendor model. Other details are not yet known."}


@pytest.mark.parametrize("patch", [
    {"field": "risk_tier"}, {"field": False}, {"value": "approved"}, {"value": None},
    {"source": "unread:source"}, {"source": 123},
    {"quote": "We are fully compliant."}, {"quote": ""}, {"quote": 2}, {"quote": "x" * 1001},
    {"reason": ""}, {"reason": []}, {"reason": "x" * 1001},
])
def test_untrusted_proposal_fields_quotes_and_values_rejected(patch):
    with pytest.raises(ValueError):
        validate_proposals([{**VALID, **patch}], SOURCES)


@pytest.mark.parametrize("raw", [None, {}, [False], [VALID, VALID], [VALID] * 13])
def test_proposal_shape_bounds_and_duplicates(raw):
    with pytest.raises(ValueError):
        validate_proposals(raw, SOURCES)


def test_valid_proposal_remains_only_a_draft_data_structure():
    result = validate_proposals([VALID], SOURCES)
    assert result == [VALID]
    assert "classification" not in result[0] and "accepted" not in result[0]
    assert all(p["field"] in QUESTIONS for p in result)
