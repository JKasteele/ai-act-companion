"""ALTAI / EIOPA / DNB SAFEST crosswalks and the DORA third-party hook
(app/knowledge/sector_frameworks.py)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import questionnaire, reports  # noqa: E402
from app.classifier import classify  # noqa: E402
from app.knowledge import sector_frameworks as sfx  # noqa: E402

VALID_IDS = set(questionnaire.all_question_ids())


def _answers(name="health_insurance_pricing.json"):
    return {k: v for k, v in json.loads((ROOT / "examples" / name).read_text(
        encoding="utf-8")).items() if not k.startswith("_")}


def _assessment(a):
    return {"id": "t", "created_at": "2026-09-03T00:00:00+00:00",
            "answers": a, "classification": classify(a)}


def test_altai_has_seven_requirements_with_valid_evidence_fields():
    assert [r[0] for r in sfx.ALTAI] == [str(i) for i in range(1, 8)]
    for _rid, _t, _asks, _act, _iso, fields in sfx.ALTAI:
        assert fields and set(fields) <= VALID_IDS, fields


def test_eiopa_six_and_safest_spells_safest():
    assert len(sfx.EIOPA_PRINCIPLES) == 6
    assert "".join(letter for letter, *_r in sfx.DNB_SAFEST) == "SAFEST"


def test_altai_evidence_separates_answered_from_missing():
    rows = sfx.altai_evidence({"autonomy_level": "advisory", "can_override": False})
    human = next(r for r in rows if r[1] == "Human agency and oversight")
    assert set(human[5]) == {"autonomy_level", "can_override"}   # False still counts
    assert "human_oversight" in human[6]


def test_dora_hook_fires_only_for_financial_entities():
    a = _answers()
    assert sfx.is_financial_entity(a)
    reasons = sfx.dora_reasons(a)
    assert any("third-party" in r for r in reasons)
    assert any("Area statistics" in r for r in reasons)      # vendor dataset named
    a["org_sector"] = "healthcare"
    assert sfx.dora_reasons(a) == []
    # A financial-entity deployer with no explicit vendor signals still has a supplier.
    assert sfx.dora_reasons({"org_sector": "banking_credit", "provider_role": "deployer"})


def test_risk_report_has_altai_always_and_sector_block_only_for_finance():
    _t, _f, md = reports.render("risk", _assessment(_answers()))
    assert "### 5.3 ALTAI" in md and "Human agency and oversight" in md
    assert "### 5.4 Insurance & financial sector" in md
    assert "Data governance and record keeping" in md and "SAFEST" in md
    assert "artificialintelligenceact.eu/article/26/" in md   # Art. 26(5)-(6) hook linked
    _t, _f, md2 = reports.render("risk", _assessment(_answers("hiring_cv_screening.json")))
    assert "### 5.3 ALTAI" in md2
    assert "### 5.4" not in md2


def test_compliance_tracker_has_dora_section_for_insurer():
    _t, _f, md = reports.render("compliance", _assessment(_answers()))
    assert "## ICT third-party risk (DORA Art. 28–30)" in md
    assert "DORA Art. 30(3)" in md and "Art. 25" in md
    assert "Area statistics" in md
    _t, _f, md2 = reports.render("compliance", _assessment(_answers("hiring_cv_screening.json")))
    assert "DORA" not in md2


def test_sector_fields_cannot_move_tier():
    a = {"eu_market": True, "org_sector": "insurance", "sec_third_party_models": True}
    assert classify(a)["tier"] == "minimal"
