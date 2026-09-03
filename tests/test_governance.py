"""Governance register (section 13 `gov_*`, app/governance.py, report 21) and the
monitoring KPI rows."""

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import questionnaire, reports  # noqa: E402
from app.classifier import classify  # noqa: E402
from app.governance import (  # noqa: E402
    REGISTER_COLUMNS,
    completeness,
    governance_status,
    register_row,
)
from app.knowledge import monitoring as mon  # noqa: E402

TODAY = date(2026, 9, 3)


def _example(name):
    return {k: v for k, v in json.loads((ROOT / "examples" / name).read_text(
        encoding="utf-8")).items() if not k.startswith("_")}


def _assessment(a):
    return {"id": "t", "created_at": "2026-09-03T00:00:00+00:00",
            "answers": a, "classification": classify(a)}


def test_section_13_exists_with_two_tables():
    sec = next(s for s in questionnaire.QUESTIONNAIRE["sections"] if s["id"] == "governance")
    tables = [q for q in sec["questions"] if q["type"] == "table"]
    assert {t["id"] for t in tables} == {"gov_exceptions", "gov_literacy"}
    assert len(set(questionnaire.all_question_ids())) == len(questionnaire.all_question_ids())


def test_next_review_is_derived_from_approval_and_tier_cadence():
    a = _example("hiring_cv_screening.json")          # high risk, approved 2026-05-20
    g = governance_status(a, classify(a), today=TODAY)
    assert g["cadence_months"] == 6
    assert g["next_review"] == "2026-11-20" and not g["review_overdue"]
    assert "6 months" in g["next_review_source"]
    late = dict(a, gov_approved_on="2025-12-01")
    g2 = governance_status(late, classify(late), today=TODAY)
    assert g2["next_review"] == "2026-06-01" and g2["review_overdue"]
    assert any(x["severity"] == "high" and "overdue" in x["gap"] for x in g2["gaps"])
    explicit = dict(a, gov_next_review="2027-01-15")
    assert governance_status(explicit, classify(explicit), today=TODAY)["next_review"] == "2027-01-15"


def test_unparseable_date_is_unknown_not_a_pass():
    a = {"eu_market": True, "gov_approved_on": "next spring"}
    g = governance_status(a, classify(a), today=TODAY)
    assert g["approved_on"] == "" and g["next_review"] == "" and not g["review_overdue"]
    assert any("No review date" in x["gap"] for x in g["gaps"])


def test_exceptions_expired_and_open_ended_are_flagged():
    a = _example("grid_ops_agent.json")                # exception expires 2026-12-31
    g = governance_status(a, classify(a), today=TODAY)
    assert g["exceptions"][0]["expired"] is False
    g2 = governance_status(a, classify(a), today=date(2027, 1, 2))
    assert g2["exceptions"][0]["expired"] is True
    assert any("Exception expired" in x["gap"] and x["severity"] == "high" for x in g2["gaps"])
    b = dict(a, gov_exceptions=[{"exception": "no end date", "decision": "allowed"}])
    g3 = governance_status(b, classify(b), today=TODAY)
    assert g3["exceptions"][0]["open_ended"] and any("Open-ended" in x["gap"] for x in g3["gaps"])


def test_literacy_and_proposed_status_gaps():
    a = _example("support_chatbot.json")               # proposed, no literacy record
    g = governance_status(a, classify(a), today=TODAY)
    assert g["status"] == "proposed"
    assert any("without an approved governance decision" in x["gap"] for x in g["gaps"])
    assert any("AI-literacy" in x["gap"] for x in g["gaps"])
    b = _example("hiring_cv_screening.json")
    assert not any("AI-literacy" in x["gap"] for x in governance_status(b, classify(b), TODAY)["gaps"])


def test_completeness_scores_sections():
    c = completeness(_example("health_insurance_pricing.json"))
    assert c["per_section"]["datagov"] >= 0.9 and c["per_section"]["forensics"] >= 0.9
    assert c["complete"] is True
    c2 = completeness({"eu_market": True, "sys_name": "x"})
    assert c2["complete"] is False and c2["overall"] < 0.4   # booleans are not counted


def test_register_row_has_every_column_and_annex_area():
    a = _example("health_insurance_pricing.json")
    row = register_row({"id": "r1", "answers": a, "classification": classify(a),
                        "created_at": "2026-09-03"}, forensic_band="Ready with gaps", today=TODAY)
    assert set(row) == {k for k, _h in REGISTER_COLUMNS}
    assert "Annex III(5)(c)" in row["annex_iii"]
    assert row["applies_from"] == "2 Dec 2027"
    assert row["status"] == "Approved" and row["public_register"] == "yes"
    assert "contract" in row["legal_basis"]


def test_governance_report_renders_and_escapes():
    a = _example("hiring_cv_screening.json")
    a["gov_exceptions"] = [{"exception": "x | y\n# nope", "decision": "ok", "decided_by": "b",
                            "expires": "2027-01-01"}]
    rtype, filename, md = reports.render("governance", _assessment(a))
    assert rtype == "governance" and filename.startswith("governance-register-")
    for h in ("## 1. Policy metadata", "## 2. Exceptions", "## 3. AI-literacy record",
              "## 4. Intake completeness", "## 5. Gaps", "## 6. Register entry"):
        assert h in md, h
    assert "\n# nope" not in md and "x \\| y" in md
    assert "People & AI Committee" in md and "DPIA-2026-007" in md


def test_monitoring_kpis_follow_tier_and_autonomy():
    hi = mon.seeded_rows({"autonomy_level": "advisory"}, "high")
    metrics = [r["Metric / signal"] for rows in hi.values() for r in rows]
    assert any("Override rate" in m for m in metrics)
    assert any("Complaints" in m for m in metrics) and any("Incidents" in m for m in metrics)
    assert any("baseline" in m.lower() for m in metrics)
    assert all(r["Review cadence"] == mon.cadence_for("high")
               for r in hi["compliance"])
    auto = mon.seeded_rows({"autonomy_level": "fully_autonomous"}, "minimal")
    assert not any("Override rate" in r["Metric / signal"] for r in auto["human_factors"])
    _t, _f, md = reports.render("monitoring", _assessment(_example("hiring_cv_screening.json")))
    assert "Review cadence for the high tier" in md and "Override rate" in md


def test_gov_fields_cannot_move_tier():
    a = {"eu_market": True, "gov_policy_owner": "hr_usecases=employment",
         "gov_exceptions": [{"exception": "p_social_scoring: true"}], "gov_status": "approved"}
    assert classify(a)["tier"] == "minimal"
