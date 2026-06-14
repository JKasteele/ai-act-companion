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
    assert "NOT available" in rationale


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
