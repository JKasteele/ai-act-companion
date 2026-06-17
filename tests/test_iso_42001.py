"""Tests for the ISO/IEC 42001 Annex A control mapping (app/knowledge/iso_42001.py).

Asserts the verified 38-control Annex A list is well-formed, every control maps to
a resolvable EU AI Act article, and the mapping renders in the risk report.

Runs with pytest or standalone (`python tests/test_iso_42001.py`).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import reports  # noqa: E402
from app.classifier import classify  # noqa: E402
from app.knowledge import eu_ai_act as eu  # noqa: E402
from app.knowledge import iso_42001 as iso  # noqa: E402


def test_has_38_annex_a_controls():
    assert len(iso.ANNEX_A_CONTROLS) == 38
    ids = [c[0] for c in iso.ANNEX_A_CONTROLS]
    assert len(set(ids)) == 38  # all unique


def test_controls_are_well_formed_and_categorised():
    for cid, title, refs in iso.ANNEX_A_CONTROLS:
        assert cid.startswith("A.")
        assert title and title.strip()
        cat = iso.annex_a_category(cid)
        assert cat in iso.ANNEX_A, f"{cid} -> {cat} not a known category"
        assert refs, f"{cid} has no EU AI Act anchor"


def test_every_anchor_is_a_resolvable_ai_act_article():
    # The whole point of the project: every citation is a real, linkable article.
    for cid, _title, refs in iso.ANNEX_A_CONTROLS:
        for ref in refs:
            assert eu.ref_url(ref), f"{cid}: '{ref}' does not resolve to an article URL"


def test_all_nine_categories_are_covered():
    cats = {iso.annex_a_category(c[0]) for c in iso.ANNEX_A_CONTROLS}
    assert cats == set(iso.ANNEX_A)


def test_annex_a_category_helper():
    assert iso.annex_a_category("A.6.2.8") == "A.6"
    assert iso.annex_a_category("A.2.2") == "A.2"
    assert iso.annex_a_category("A.10.4") == "A.10"


def test_mapping_renders_in_risk_report():
    answers = {"sys_name": "Annex A Demo", "eu_market": True,
               "hr_usecases": ["employment"], "data_personal": True}
    assessment = {"id": "iso", "created_at": "2026-01-01T00:00:00+00:00",
                  "answers": answers, "classification": classify(answers)}
    _rtype, _filename, md = reports.render("risk", assessment)
    assert "Annex A control mapping" in md
    assert "A.6.2.8" in md                       # a representative control id
    assert "AI system recording of event logs" in md
    assert "artificialintelligenceact.eu/article/12" in md  # its Art. 12 anchor


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
    sys.exit(0 if _run_standalone() else 1)
