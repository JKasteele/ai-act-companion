"""Tests for the rule-based classifier.

Runs with pytest (`pytest`) or standalone (`python tests/test_classifier.py`).
"""

import json
import sys
from pathlib import Path

# Make the project root importable when run standalone.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import reports  # noqa: E402
from app.classifier import classify  # noqa: E402
from app.knowledge import eu_ai_act as eu  # noqa: E402

EXAMPLES = ROOT / "examples"


def _load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def test_hiring_is_high_risk():
    r = classify(_load("hiring_cv_screening.json"))
    assert r["tier"] == eu.TIER_HIGH
    assert any("Annex III(4)" in ref for f in r["findings"] for ref in f["refs"])
    assert r["high_risk_obligations"]  # high-risk obligations included


def test_chatbot_is_limited():
    r = classify(_load("support_chatbot.json"))
    assert r["tier"] == eu.TIER_LIMITED
    refs = [ref for f in r["transparency_obligations"] for ref in f["refs"]]
    assert "Art. 50(1)" in refs


def test_social_scoring_is_prohibited():
    r = classify(_load("social_scoring.json"))
    assert r["tier"] == eu.TIER_PROHIBITED
    assert any("Art. 5(1)(c)" in ref for f in r["findings"] for ref in f["refs"])


def test_spam_filter_is_minimal():
    r = classify(_load("spam_filter.json"))
    assert r["tier"] == eu.TIER_MINIMAL
    assert not r["findings"]


def test_non_eu_out_of_scope():
    r = classify({"eu_market": False, "p_social_scoring": True})
    assert r["tier"] == eu.TIER_MINIMAL  # Art. 2: outside scope


def test_art_6_3_derogation_note_without_profiling():
    answers = {"eu_market": True, "hr_usecases": ["employment"],
               "hr_art6_3_minor": True, "hr_does_profiling": False}
    r = classify(answers)
    assert r["tier"] == eu.TIER_HIGH  # stays high until documented
    assert any("6(3)" in ref for f in r["findings"] for ref in f["refs"])


def test_art_6_3_unavailable_with_profiling():
    answers = {"eu_market": True, "hr_usecases": ["employment"],
               "hr_art6_3_minor": True, "hr_does_profiling": True}
    r = classify(answers)
    rationale = " ".join(f["rationale"] for f in r["findings"])
    assert "always high-risk" in rationale


def test_art_6_3_profiling_note_without_minor_task():
    # Profiling + Annex III but no minor-task claim must still surface the
    # "derogation never available" warning (review finding M2).
    answers = {"eu_market": True, "hr_usecases": ["employment"],
               "hr_does_profiling": True, "hr_art6_3_minor": False}
    r = classify(answers)
    rationale = " ".join(f["rationale"] for f in r["findings"])
    assert "always high-risk" in rationale


def test_art2_research_exemption_out_of_scope():
    # Would be Annex III high-risk, but scientific-R&D exemption removes it from scope.
    answers = {"eu_market": True, "exempt_research": True,
               "hr_usecases": ["essential_services"], "hr_does_profiling": True}
    r = classify(answers)
    assert r["tier"] == eu.TIER_MINIMAL
    assert not r["findings"] and not r["high_risk_obligations"]
    assert r["applicability"]["basis"] == "Art. 2(6)"


def test_art2_military_exemption_overrides_prohibited():
    # Military/defence use is out of the entire Regulation's scope (Art. 2(3)),
    # so even an otherwise-prohibited practice does not classify.
    answers = {"eu_market": True, "exempt_military": True, "p_realtime_rbi_le": True}
    r = classify(answers)
    assert r["tier"] == eu.TIER_MINIMAL
    assert r["out_of_scope"]["ref"] == "Art. 2(3)"


def test_out_of_scope_emits_no_gpai_obligations():
    # Chapter V is part of the same Art. 2 scope: an out-of-scope GPAI model
    # must not carry GPAI obligations.
    answers = {"eu_market": False, "gpai_model": True}
    r = classify(answers)
    assert r["tier"] == eu.TIER_MINIMAL
    assert r["gpai_obligations"] == []


def test_deployer_obligations_exclude_provider_only_duties():
    answers = {"eu_market": True, "provider_role": "deployer",
               "hr_usecases": ["essential_services"], "hr_does_profiling": True}
    r = classify(answers)
    assert r["tier"] == eu.TIER_HIGH
    refs = {ref for ref, _desc in r["high_risk_obligations"]}
    # Deployer duties present, provider-only conformity/CE duties absent.
    assert "Art. 26" in refs and "Art. 27" in refs
    assert "Art. 43" not in refs and "Art. 47 + 48" not in refs and "Art. 49" not in refs


def test_provider_obligations_include_conformity_and_ce():
    answers = {"eu_market": True, "provider_role": "provider",
               "hr_usecases": ["essential_services"], "hr_does_profiling": True}
    r = classify(answers)
    refs = {ref for ref, _desc in r["high_risk_obligations"]}
    assert {"Art. 43", "Art. 47 + 48", "Art. 49"} <= refs
    # Provider is not shown the deployer-only duties.
    assert "Art. 26" not in refs and "Art. 27" not in refs


def test_open_source_gpai_carveout_present_without_systemic():
    answers = {"eu_market": True, "gpai_model": True, "gpai_open_source": True,
               "gpai_systemic": False}
    r = classify(answers)
    assert r["tier"] == eu.TIER_MINIMAL
    refs = [ref for f in r["gpai_obligations"] for ref in f["refs"]]
    assert "Art. 53(2)" in refs  # open-source carve-out surfaced
    # Minimal-tier GPAI now has a real applicability date (2 Aug 2025), not "-".
    assert r["applicability"]["date"] == "2 Aug 2025"


def test_omnibus_postponed_high_risk_dates():
    """Reg. (EU) 2026/1744 (Digital Omnibus on AI, in force 27 Jul 2026) moved
    Annex III high-risk to 2 Dec 2027 and Annex I to 2 Aug 2028. The old
    2 Aug 2026 date must not resurface for high-risk systems."""
    annex_iii = classify(_load("hiring_cv_screening.json"))
    assert annex_iii["tier"] == eu.TIER_HIGH
    assert annex_iii["applicability"]["date"] == "2 Dec 2027"
    assert "2026/1744" in annex_iii["applicability"]["what"]

    annex_i = classify({"eu_market": True, "hr_safety_component": True})
    assert annex_i["tier"] == eu.TIER_HIGH
    assert annex_i["applicability"]["date"] == "2 Aug 2028"

    # Art. 50 was NOT postponed: limited-risk systems are already in scope.
    limited = classify({"eu_market": True, "t_interacts_humans": True})
    assert limited["tier"] == eu.TIER_LIMITED
    assert limited["applicability"]["date"] == "2 Aug 2026"

    # The timeline itself records the amending act and the new dates.
    dates = {d for d, _w, _b in eu.TIMELINE}
    assert {"27 Jul 2026", "2 Dec 2027", "2 Aug 2028"} <= dates
    assert not any("Annex III" in w for d, w, _b in eu.TIMELINE if d == "2 Aug 2026")
    assert eu.AMENDMENTS and "2026/1744" in eu.AMENDMENTS[0][0]


def test_knowledge_base_metadata_in_report_header():
    """Every report says which state of the law it reflects."""
    assert eu.KNOWLEDGE_VERSION and len(eu.LAST_REVIEWED) == 10
    cls = classify(_load("hiring_cv_screening.json"))
    _t, _f, md = reports.render("risk", {"id": "x", "created_at": "now",
                                          "answers": _load("hiring_cv_screening.json"),
                                          "classification": cls})
    assert f"reviewed {eu.LAST_REVIEWED}" in md
    assert "2026/1744" in md


def test_open_source_carveout_suppressed_by_systemic_risk():
    answers = {"eu_market": True, "gpai_model": True, "gpai_open_source": True,
               "gpai_systemic": True}
    r = classify(answers)
    refs = [ref for f in r["gpai_obligations"] for ref in f["refs"]]
    assert "Art. 53(2)" not in refs  # carve-out withdrawn under systemic risk
    assert any("55" in ref for ref in refs)  # systemic obligations stand


def test_ai_literacy_recommended_for_in_scope_systems():
    r = classify({"eu_market": True})
    assert any("Art. 4" in a for a in r["recommended_artifacts"])
    # Out-of-scope systems do not carry the Art. 4 obligation.
    out = classify({"eu_market": False})
    assert not any("Art. 4" in a for a in out["recommended_artifacts"])


def test_annex_iii_finding_records_specific_usecase():
    r = classify({"eu_market": True, "hr_usecases": ["employment"]})
    sources = [s for f in r["findings"] for s in f["source_questions"]]
    assert "hr_usecases=employment" in sources


def test_techdoc_renders_all_nine_annex_iv_sections():
    answers = _load("hiring_cv_screening.json")
    assessment = {"id": "test-techdoc", "created_at": "2026-01-01T00:00:00+00:00",
                  "answers": answers, "classification": classify(answers)}
    _rtype, _filename, md = reports.render("techdoc", assessment)
    for heading in reports.ANNEX_IV_SECTIONS:
        assert heading in md, f"missing Annex IV section: {heading}"
    # Cites Art. 11 + Annex IV via a working AI Act Explorer link.
    assert "artificialintelligenceact.eu/article/11/" in md


def test_compliance_tracker_high_risk_rows_and_penalty():
    answers = _load("hiring_cv_screening.json")
    assessment = {"id": "test-comp", "created_at": "2026-01-01T00:00:00+00:00",
                  "answers": answers, "classification": classify(answers)}
    _rtype, _filename, md = reports.render("compliance", assessment)
    # The core high-risk obligation articles appear as rows.
    for art in ("article/9/", "article/10/", "article/11/", "article/12/",
                "article/13/", "article/14/", "article/15/"):
        assert art in md, f"missing obligation row for {art}"
    # High-risk penalty line (€15M / 3%) is shown; status never inferred.
    assert "€15,000,000" in md and "3%" in md
    assert "Not started" in md
    assert "In progress" not in md and "Done" not in md


def test_compliance_prohibited_shows_35m():
    answers = _load("social_scoring.json")
    assessment = {"id": "test-comp-p", "created_at": "2026-01-01T00:00:00+00:00",
                  "answers": answers, "classification": classify(answers)}
    _rtype, _filename, md = reports.render("compliance", assessment)
    assert "€35,000,000" in md and "7%" in md


def test_monitoring_renders_six_categories():
    from app.knowledge import monitoring as mon
    answers = _load("hiring_cv_screening.json")
    assessment = {"id": "test-mon", "created_at": "2026-01-01T00:00:00+00:00",
                  "answers": answers, "classification": classify(answers)}
    _rtype, _filename, md = reports.render("monitoring", assessment)
    for _cid, title, _what in mon.CATEGORIES:
        assert title in md, f"missing monitoring category: {title}"
    assert len([c for c in mon.CATEGORIES]) == 6
    # Cites Art. 72 and seeds the employment outcome-drift functionality row.
    assert "artificialintelligenceact.eu/article/72/" in md
    assert "Outcome drift across protected groups" in md


def _assess(answers):
    return {"id": "t", "created_at": "2026-01-01T00:00:00+00:00",
            "answers": answers, "classification": classify(answers)}


def test_declaration_of_conformity_cites_art47_and_flags_non_high_risk():
    _t, _f, md = reports.render("doc", _assess({"eu_market": True, "sys_name": "X"}))
    assert "artificialintelligenceact.eu/article/47/" in md
    assert "not high-risk" in md  # scope note for a non-high-risk system


def test_registration_maps_annex_iii_category():
    _t, _f, md = reports.render("registration", _assess(
        {"eu_market": True, "sys_name": "X", "hr_usecases": ["essential_services"]}))
    assert "artificialintelligenceact.eu/article/49/" in md
    assert "Annex III(5)" in md  # category pulled from hr_usecases


def test_gpai_report_toggles_open_source_carveout():
    oss = reports.render("gpai", _assess(
        {"eu_market": True, "gpai_model": True, "gpai_open_source": True}))[2]
    assert "Open-source carve-out" in oss and "Exempt (Art. 53(2))" in oss
    systemic = reports.render("gpai", _assess(
        {"eu_market": True, "gpai_model": True, "gpai_open_source": True,
         "gpai_systemic": True}))[2]
    # Systemic risk withdraws the carve-out and adds the Art. 55 duties.
    assert "Open-source carve-out" not in systemic
    assert "artificialintelligenceact.eu/article/55/" in systemic


def test_reports_render_for_all_types():
    answers = _load("hiring_cv_screening.json")
    assessment = {"id": "test-1", "created_at": "2026-01-01T00:00:00+00:00",
                  "answers": answers, "classification": classify(answers)}
    for t in reports.REPORT_TYPES:
        rtype, filename, md = reports.render(t, assessment)
        assert rtype == t
        assert filename.endswith(".md")
        assert len(md) > 200
        assert answers["sys_name"] in md


def _run_standalone():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR {fn.__name__}: {e!r}")
    print(f"\n{passed}/{len(fns)} tests passed.")
    return passed == len(fns)


if __name__ == "__main__":
    ok = _run_standalone()
    sys.exit(0 if ok else 1)
