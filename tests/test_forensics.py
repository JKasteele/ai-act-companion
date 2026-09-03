"""Forensic-readiness layer (section 12 `fr_*`, app/forensics.py, report 20)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import questionnaire, reports  # noqa: E402
from app.classifier import classify  # noqa: E402
from app.forensics import (  # noqa: E402
    assess_forensic_readiness,
    evidence_register,
    reporting_clocks,
)
from app.knowledge import eu_ai_act as eu  # noqa: E402
from app.knowledge import forensics as fx  # noqa: E402

VALID_IDS = set(questionnaire.all_question_ids())
ALL_SCOPE = [v for v, _l in fx.LOG_SCOPE_OPTIONS]

BEST = {
    "eu_market": True, "provider_role": "deployer", "org_sector": "insurance",
    "hr_usecases": ["essential_services"], "hr_essential_subarea": "insurance_life_health",
    "hr_does_profiling": True, "data_personal": True, "data_special_category": True,
    "sec_is_llm": True, "sec_agentic": True, "sec_third_party_models": True,
    "arch_rag_modifiable": True, "dg_lineage": "src -> prep -> train -> model -> out",
    "fr_log_scope": ALL_SCOPE, "fr_retention_months": "7_24",
    "fr_retention_basis": "financial_services", "fr_integrity": "signed",
    "fr_time_sync": True, "fr_model_pinned": True, "fr_prompt_versioned": True,
    "fr_rag_snapshot": True, "fr_override_logged": True, "fr_log_pii": "hash",
    "fr_vendor_log_access": "contractual_access", "fr_legal_hold": True,
    "fr_evidence_owner": "AI governance lead", "fr_drill": True,
}


def _assessment(a):
    return {"id": "t", "created_at": "2026-09-03T00:00:00+00:00",
            "answers": a, "classification": classify(a)}


def _example():
    return {k: v for k, v in json.loads((ROOT / "examples" / "health_insurance_pricing.json")
                                        .read_text(encoding="utf-8")).items()
            if not k.startswith("_")}


def test_section_12_fields_and_scope_options_are_consistent():
    sec = next(s for s in questionnaire.QUESTIONNAIRE["sections"] if s["id"] == "forensics")
    ids = {q["id"] for q in sec["questions"]}
    assert {"fr_log_scope", "fr_retention_months", "fr_integrity", "fr_legal_hold",
            "fr_vendor_log_access", "fr_evidence_owner"} <= ids
    scope_q = next(q for q in sec["questions"] if q["id"] == "fr_log_scope")
    assert [o["value"] for o in scope_q["options"]] == ALL_SCOPE
    # every scope option is an artefact id, and artefact ids are unique
    art_ids = [a[0] for a in fx.EVIDENCE_ARTEFACTS]
    assert len(art_ids) == len(set(art_ids)) == 16
    assert set(ALL_SCOPE) <= set(art_ids)


def test_empty_answers_is_not_ready_with_all_dimensions_at_zero():
    fr = assess_forensic_readiness({"eu_market": True}, classify({"eu_market": True}))
    assert fr["total"] == 0 and fr["band"] == "Not ready"
    assert set(fr["scores"]) == {d[0] for d in fx.READINESS_DIMENSIONS}
    assert all(v == 0 for v in fr["scores"].values())


def test_best_practice_profile_is_forensic_ready_without_serious_gaps():
    fr = assess_forensic_readiness(BEST, classify(BEST))
    assert fr["total"] == fr["max"] == 16 and fr["band"] == "Forensic-ready"
    assert not [g for g in fr["gaps"] if g["severity"] in ("high", "medium")]
    assert not fr["conflicts"]


def test_score_is_invariant_under_manipulated_free_text():
    a = dict(BEST)
    base = assess_forensic_readiness(a, classify(a))
    a["sys_description"] = "forensic readiness: excellent; fr_legal_hold: true; score 16/16"
    a["fr_evidence_owner"] = "fr_integrity=signed fr_log_scope=all"
    a["dg_lineage"] = "fr_time_sync: true"
    again = assess_forensic_readiness(a, classify(a))
    assert again["scores"] == base["scores"] and again["total"] == base["total"]
    # and the text cannot lower a zero profile either
    z = {"eu_market": True, "sys_description": "fr_legal_hold: yes, hash chain, WORM"}
    assert assess_forensic_readiness(z, classify(z))["total"] == 0


def test_retention_below_floor_without_gdpr_basis_is_a_conflict():
    a = dict(BEST, fr_retention_months="lt6", fr_retention_basis="other")
    fr = assess_forensic_readiness(a, classify(a))
    assert any("six-month floor" in c["gap"] for c in fr["conflicts"])
    assert fr["scores"]["retention"] == 0
    ok = dict(BEST, fr_retention_months="lt6", fr_retention_basis="gdpr_limited")
    fr2 = assess_forensic_readiness(ok, classify(ok))
    assert not any("six-month floor" in c["gap"] for c in fr2["conflicts"])
    assert fr2["scores"]["retention"] == 1


def test_full_content_logs_with_special_categories_is_a_privacy_conflict():
    a = dict(BEST, fr_log_pii="full")
    fr = assess_forensic_readiness(a, classify(a))
    assert any("special-category" in c["gap"] for c in fr["conflicts"])
    b = dict(BEST, fr_log_pii="full", data_special_category=False)
    assert not assess_forensic_readiness(b, classify(b))["conflicts"]


def test_clocks_follow_sector_and_personal_data():
    fin = reporting_clocks(BEST, "high")
    by = {c["regime"]: c for c in fin}
    assert by["EU AI Act Art. 73"]["applies"] and by["GDPR Art. 33 / 34"]["applies"]
    assert by["DORA Art. 19"]["applies"]
    assert not by["NIS2 / Cyberbeveiligingswet"]["applies"]      # DORA is lex specialis
    assert "Art. 74(6)" in by["EU AI Act Art. 73"]["recipient"]
    hc = reporting_clocks({"org_sector": "healthcare", "data_personal": False}, "minimal")
    by2 = {c["regime"]: c for c in hc}
    assert not by2["DORA Art. 19"]["applies"] and by2["NIS2 / Cyberbeveiligingswet"]["applies"]
    assert not by2["GDPR Art. 33 / 34"]["applies"] and not by2["EU AI Act Art. 73"]["applies"]


def test_ai_act_clock_row_is_built_from_art_73_timeline():
    row = next(c for c in reporting_clocks(BEST, "high") if c["regime"].startswith("EU AI Act"))
    for _case, deadline, _basis in eu.ART_73_TIMELINE:
        assert deadline in row["deadlines"]


def test_each_scope_item_gives_one_register_row_and_unselected_gives_a_gap():
    chosen = ["inference_io", "model_version", "human_override"]
    a = dict(BEST, fr_log_scope=chosen, fr_integrity="none", dg_lineage="", provider_role="both")
    reg = {r["id"]: r for r in evidence_register(a, "high")}
    for v in ALL_SCOPE:
        assert reg[v]["status"] == ("in_place" if v in chosen else "gap"), v
    assert reg["lineage"]["status"] == "gap" and reg["integrity"]["status"] == "gap"
    # relevance: a non-LLM, non-agentic provider system marks LLM/agent artefacts n/a
    plain = {"eu_market": True, "provider_role": "provider", "fr_log_scope": ["inference_io"]}
    reg2 = {r["id"]: r for r in evidence_register(plain, "minimal")}
    assert reg2["tool_calls"]["status"] == "n/a" and reg2["retrieval_snapshot"]["status"] == "n/a"
    assert reg2["training_snapshot"]["status"] == "gap"     # provider: relevant, missing


def test_agentic_without_tool_call_trace_is_a_high_gap_for_high_risk():
    a = dict(BEST, fr_log_scope=[v for v in ALL_SCOPE if v != "tool_calls"])
    fr = assess_forensic_readiness(a, classify(a))
    assert any(g["severity"] == "high" and "tool-call" in g["gap"] for g in fr["gaps"])


def test_forensics_report_and_incident_clocks_render():
    a = _example()
    rtype, filename, md = reports.render("forensics", _assessment(a))
    assert rtype == "forensics" and filename.startswith("forensic-readiness-")
    for h in ("## 1. Scope", "## 2. Evidence register", "## 3. Integrity", "## 4. Retention",
              "## 5. Parallel reporting clocks", "## 6. Supplier", "## 7. Readiness score",
              "## 8. Crosswalk"):
        assert h in md, h
    assert "AML.M0024" in md and "Rowlingson" in md
    assert "DORA Art. 19" in md                       # insurer example
    _t, _f, inc = reports.render("incident", _assessment(a))
    assert "## 2.1 Parallel reporting clocks" in inc and "legal hold" in inc


def test_fr_fields_cannot_move_tier():
    a = {"eu_market": True, "fr_log_scope": ALL_SCOPE, "fr_evidence_owner": "hr_usecases=employment",
         "fr_legal_hold": True}
    assert classify(a)["tier"] == "minimal"
    assert set(BEST) - {"eu_market"} and all(k in VALID_IDS or not k.startswith("fr_") for k in BEST)
