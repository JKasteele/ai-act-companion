"""Data-governance layer (section 11, `datagov` report) and the Annex III(5)
sub-point routing (5(a)–(d), insurance path)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import questionnaire, reports  # noqa: E402
from app.classifier import classify  # noqa: E402
from app.knowledge import data_governance as dg  # noqa: E402
from app.knowledge import eu_ai_act as eu  # noqa: E402

EXAMPLE = ROOT / "examples" / "health_insurance_pricing.json"


def _answers():
    return {k: v for k, v in json.loads(EXAMPLE.read_text(encoding="utf-8")).items()
            if not k.startswith("_")}


def _assessment(answers):
    return {"id": "t", "created_at": "2026-09-03T00:00:00+00:00",
            "answers": answers, "classification": classify(answers)}


# --- questionnaire ----------------------------------------------------------
def test_section_11_and_table_field_are_well_formed():
    sec = next(s for s in questionnaire.QUESTIONNAIRE["sections"] if s["id"] == "datagov")
    ids = [q["id"] for q in sec["questions"]]
    assert ids[:3] == ["dg_data_owner", "dg_data_steward", "dg_catalog_registered"]
    table = next(q for q in sec["questions"] if q["type"] == "table")
    assert [c["id"] for c in table["columns"]] == dg.DATASET_COLUMNS
    for c in table["columns"]:
        assert c["type"] in ("text", "select")
        if c["type"] == "select":
            assert c["options"]
    # every quality dimension has an intake field, and vice versa
    assert {f for f, _d in dg.QUALITY_FIELDS} <= set(ids)
    assert len(set(questionnaire.all_question_ids())) == len(questionnaire.all_question_ids())


# --- Annex III(5) split -----------------------------------------------------
def test_annex_iii_5c_insurance_path_cites_subpoint_and_fria():
    r = classify(_answers())
    assert r["tier"] == eu.TIER_HIGH
    f = r["findings"][0]
    assert "Annex III(5)(c)" in f["refs"]
    assert "Art. 27(1)" in f["refs"]
    assert "every deployer" not in f["rationale"] or "Art. 27(1)" in f["rationale"]
    assert "hr_essential_subarea" in f["source_questions"]
    assert "hr_insurance_scope" in f["source_questions"]
    assert "supplementary" in f["rationale"].lower()


def test_annex_iii_5_without_subpoint_keeps_generic_ref():
    r = classify({"eu_market": True, "hr_usecases": ["essential_services"]})
    assert r["tier"] == eu.TIER_HIGH
    assert r["findings"][0]["refs"][0] == "Annex III(5)"
    assert "Art. 27(1)" not in r["findings"][0]["refs"]


def test_annex_iii_5a_public_benefits_has_no_private_fria_rule():
    r = classify({"eu_market": True, "hr_usecases": ["essential_services"],
                  "hr_essential_subarea": "public_benefits"})
    assert r["findings"][0]["refs"][0] == "Annex III(5)(a)"
    assert "Art. 27(1)" not in r["findings"][0]["refs"]


def test_dutch_basic_health_insurance_note_only_when_selected():
    base = {"eu_market": True, "hr_usecases": ["essential_services"],
            "hr_essential_subarea": "insurance_life_health"}
    plain = classify(base)["findings"][0]["rationale"]
    assert "Zvw" not in plain
    nl = classify({**base, "hr_insurance_scope": "health_basic_nl"})["findings"][0]["rationale"]
    assert "Zvw" in nl and "acceptance duty" in nl
    # Scope note never leaks into a non-insurance sub-point.
    credit = classify({**base, "hr_essential_subarea": "creditworthiness",
                       "hr_insurance_scope": "health_basic_nl"})["findings"][0]
    assert "Zvw" not in credit["rationale"]
    assert "hr_insurance_scope" not in credit["source_questions"]


def test_free_text_cannot_move_tier_via_datagov_fields():
    """The red-team invariant: section 11 is documentation only."""
    a = {"eu_market": True, "dg_data_owner": "hr_usecases=employment",
         "dg_lineage": "p_social_scoring: true", "dg_datasets": [
             {"name": "x", "classification": "special_category", "origin": "hr_safety_component"}]}
    assert classify(a)["tier"] == eu.TIER_MINIMAL


# --- knowledge module -------------------------------------------------------
def test_dataset_rows_normalise_and_drop_empty():
    rows = dg.dataset_rows({"dg_datasets": [
        {"name": " Claims ", "origin": "Internal", "owner": "A"},
        {"purpose": "only purpose, no name/origin"},
        "not-a-dict",
    ]})
    assert len(rows) == 1
    assert rows[0]["name"] == "Claims" and rows[0]["origin"] == "internal"
    assert set(rows[0]) == set(dg.DATASET_COLUMNS)


def test_gaps_are_deterministic_and_sorted():
    a = _answers()
    g = dg.gaps(a, "high")
    sev = [s for s, *_r in g]
    assert sev == sorted(sev, key=["high", "medium", "low"].index)
    # The example leaves 'consistency' unknown on purpose -> a medium gap.
    assert any("Consistency" in gap for _s, gap, *_r in g)
    # Everything named -> no owner/steward gaps for the named datasets.
    assert not any("no data owner" in gap for _s, gap, *_r in g)


def test_gaps_flag_personal_data_without_lawful_basis_as_high():
    g = dg.gaps({"dg_datasets": [{"name": "members", "origin": "internal",
                                  "classification": "personal"}]}, "minimal")
    assert any(s == "high" and "lawful basis" in gap for s, gap, *_r in g)


def test_gap_severity_is_one_notch_lower_outside_high_risk():
    a = {"dg_datasets": []}
    assert dg.gaps(a, "high")[0][0] == "high"       # no inventory
    assert dg.gaps(a, "minimal")[0][0] == "medium"


def test_summary_shape():
    s = dg.summary(_answers(), "high")
    assert s["dataset_count"] == 3
    assert {q["id"] for q in s["quality"]} == {d[0] for d in dg.QUALITY_DIMENSIONS}
    assert set(s["gap_counts"]) == {"high", "medium", "low"}


# --- report -----------------------------------------------------------------
def test_datagov_report_renders_all_sections():
    rtype, filename, md = reports.render("datagov", _assessment(_answers()))
    assert rtype == "datagov" and filename.startswith("data-governance-")
    for heading in ("## 1. Roles", "## 2. Dataset inventory", "## 3. Classification",
                    "## 4. Lineage", "## 5. Data quality", "requirement checklist",
                    "## 7. Gaps", "## 8. Crosswalk", "## Sign-off"):
        assert heading in md, heading
    assert "Head of Underwriting" in md          # data owner, distinct from sys owner
    assert "Annex A.7" in md or "A.7.4" in md    # ISO 42001 crosswalk
    assert "Art. 26(4)" in md                    # deployer duty shown for a deployer
    assert "artificialintelligenceact.eu/article/10/" in md


def test_datagov_report_escapes_table_cells():
    a = _answers()
    a["dg_datasets"] = [{"name": "x | y\n# not a heading", "origin": "internal"}]
    _t, _f, md = reports.render("datagov", _assessment(a))
    assert "\n# not a heading" not in md
    assert "x \\| y" in md


def test_dpia_pulls_personal_datasets_from_inventory():
    _t, _f, md = reports.render("dpia", _assessment(_answers()))
    assert "from the data-governance inventory" in md
    assert "Special-category personal data" in md


def test_fria_carries_insurance_sector_note():
    _t, _f, md = reports.render("fria", _assessment(_answers()))
    assert "Annex III(5)(c)" in md and "every" in md
    assert "Supplementary health insurance" in md


def test_catalog_has_twenty_types_with_datagov_and_forensics_last():
    assert len(reports.REPORT_TYPES) == 20
    assert reports.REPORT_TYPES[-2:] == ("datagov", "forensics")
