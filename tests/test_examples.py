"""Every shipped example is a valid, complete, self-consistent intake."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import questionnaire, reports  # noqa: E402
from app.classifier import classify  # noqa: E402
from app.governance import governance_status  # noqa: E402
from app.knowledge import sector_frameworks as sfx  # noqa: E402

EXAMPLES = sorted(p for p in (ROOT / "examples").glob("*.json") if p.name != "golden_set.json")
VALID = set(questionnaire.all_question_ids())
EXPECTED_TIER = {
    "foundation_model": "minimal", "grid_ops_agent": "high",
    "health_insurance_pricing": "high", "health_insurer_claims_fraud": "minimal",
    "health_insurer_service_assistant": "limited", "hiring_cv_screening": "high",
    "social_scoring": "prohibited", "spam_filter": "minimal", "support_chatbot": "limited",
}


def _load(p):
    return {k: v for k, v in json.loads(p.read_text(encoding="utf-8")).items()
            if not k.startswith("_")}


def test_examples_use_only_known_fields_and_expected_tiers():
    assert {p.stem for p in EXAMPLES} == set(EXPECTED_TIER)
    for p in EXAMPLES:
        a = _load(p)
        unknown = [k for k in a if k not in VALID]
        assert not unknown, (p.name, unknown)
        assert classify(a)["tier"] == EXPECTED_TIER[p.stem], p.name


def test_three_insurer_examples_cover_three_tiers_and_the_dora_hook():
    insurers = {p.stem: _load(p) for p in EXAMPLES if p.stem.startswith("health_insur")}
    tiers = {classify(a)["tier"] for a in insurers.values()}
    assert tiers == {"high", "minimal", "limited"}
    for name, a in insurers.items():
        assert sfx.is_financial_entity(a), name
        assert sfx.dora_reasons(a), name          # each relies on a vendor model or dataset
    # the service assistant is agentic and still in review; the claims scorer is approved
    assert governance_status(insurers["health_insurer_service_assistant"])["status"] == "in_review"
    assert governance_status(insurers["health_insurer_claims_fraud"])["status"] == "approved"


def test_every_example_renders_every_report_in_both_languages():
    for p in EXAMPLES:
        a = _load(p)
        assessment = {"id": p.stem, "created_at": "2026-09-03T00:00:00+00:00",
                      "answers": a, "classification": classify(a)}
        for t in reports.REPORT_TYPES:
            for lang in ("en", "nl"):
                _rt, _fn, md = reports.render(t, assessment, lang=lang)
                assert len(md) > 200, (p.name, t, lang)
