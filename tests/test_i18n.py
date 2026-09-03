"""`--lang nl`: Dutch summary block prepended to any report."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import i18n, reports  # noqa: E402
from app.classifier import classify  # noqa: E402


def _example(name):
    return {k: v for k, v in json.loads((ROOT / "examples" / name).read_text(
        encoding="utf-8")).items() if not k.startswith("_")}


def _assessment(a):
    return {"id": "t", "created_at": "2026-09-03T00:00:00+00:00",
            "answers": a, "classification": classify(a)}


def test_english_is_unchanged_and_nl_prepends_summary():
    a = _example("health_insurance_pricing.json")
    en = reports.render("risk", _assessment(a))[2]
    nl = reports.render("risk", _assessment(a), lang="nl")[2]
    assert "Samenvatting (NL)" not in en
    assert "## Samenvatting (NL)" in nl
    assert nl.index("Samenvatting (NL)") < nl.index("## 1. System overview")
    assert "**Hoog risico**" in nl and "gebruiksverantwoordelijke" in nl
    assert "2 Dec 2027" in nl and "Digital Omnibus" in nl
    assert "Grondrechteneffectbeoordeling" in nl            # artifact translated
    assert "Forensische gereedheid" in nl and "Governancestatus" in nl
    # the English body is intact after the block
    assert en.split("\n## 1. System overview", 1)[1] in nl


def test_nl_summary_for_every_report_type_and_tiers():
    for name, tier_nl in (("social_scoring.json", "Verboden"),
                          ("support_chatbot.json", "Beperkt risico"),
                          ("spam_filter.json", "Minimaal risico")):
        a = _example(name)
        md = reports.render("risk", _assessment(a), lang="nl")[2]
        assert tier_nl in md
    a = _example("hiring_cv_screening.json")
    for t in reports.REPORT_TYPES:
        md = reports.render(t, _assessment(a), lang="nl")[2]
        assert "Samenvatting (NL)" in md


def test_summary_escapes_free_text_and_rejects_unknown_lang():
    a = {"eu_market": True, "sys_name": "x | y\n# not a heading", "t_interacts_humans": True}
    md = reports.render("risk", _assessment(a), lang="nl")[2]
    block = md.split("## Samenvatting (NL)")[1].split("## 1.")[0]
    assert "\n# not a heading" not in block and "x \\| y" in block
    with pytest.raises(ValueError):
        i18n.localise("# x", _assessment(a), "de")
