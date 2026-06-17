"""Tests for the Model Card generator (app/modelcard.py).

Asserts the card is deterministic, has all nine Model Card sections, pre-fills
from the intake, and leaves unknown parts as [to be completed].

Runs with pytest or standalone (`python tests/test_modelcard.py`).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import reports  # noqa: E402
from app.modelcard import MODEL_CARD_SECTIONS, generate_model_card  # noqa: E402

_ANSWERS = {
    "sys_name": "TalentMatch", "sys_version": "1.0", "sys_owner": "Example Ltd.",
    "intended_purpose": "Support recruiters in pre-selecting candidates.",
    "sys_description": "Ranks incoming CVs by suitability.",
    "data_sources": "Internal ATS database with synthetic CVs.",
    "human_oversight": "A recruiter reviews every shortlist.",
    "autonomy_level": "advisory", "data_personal": True,
}


def test_has_nine_sections():
    assert len(MODEL_CARD_SECTIONS) == 9
    card = generate_model_card(_ANSWERS)
    assert card["sections"] == MODEL_CARD_SECTIONS


def test_is_deterministic():
    assert generate_model_card(_ANSWERS) == generate_model_card(dict(_ANSWERS))


def test_prefills_from_intake():
    g = generate_model_card(_ANSWERS)["prefilled"]
    assert g["sys_name"] == "TalentMatch"
    assert g["data_sources"].startswith("Internal ATS")
    assert g["data_personal"] == "Yes"
    # An unanswered field is None (rendered as [to be completed]).
    assert g["data_biometric"] is None


def test_model_card_report_renders():
    assessment = {"id": "mc", "created_at": "2026-01-01T00:00:00+00:00",
                  "answers": _ANSWERS, "classification": {},
                  "model_card": generate_model_card(_ANSWERS)}
    rtype, filename, md = reports.render("modelcard", assessment)
    assert rtype == "modelcard"
    assert filename.endswith(".md")
    assert "Model Card" in md
    for section in MODEL_CARD_SECTIONS:
        assert section in md
    assert "TalentMatch" in md
    assert "Support recruiters" in md            # pre-filled intended purpose
    assert "[to be completed]" in md             # gaps left for the human
    assert "artificialintelligenceact.eu/article/13" in md  # Art. 13 anchor


def test_renders_with_minimal_answers():
    assessment = {"id": "m", "created_at": "2026-01-01T00:00:00+00:00",
                  "answers": {"sys_name": "Bare"}, "classification": {}}
    _rtype, _filename, md = reports.render("modelcard", assessment)
    assert "Bare" in md
    assert len(md) > 200


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
