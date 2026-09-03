"""Replay provider (sandbox AI-assist without a model) and the demo assets."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.classifier import classify  # noqa: E402
from app.llm import replay, service  # noqa: E402
from app.llm.config import settings  # noqa: E402


def _use(monkeypatch, name):
    monkeypatch.setattr(settings, "provider", name)


def test_status_is_labelled_as_replay(monkeypatch):
    _use(monkeypatch, "replay")
    st = service.status()
    assert st["enabled"] and st["provider"] == "replay" and st["replay"] is True
    assert "no live model" in st["model"]


def test_prefill_replays_the_closest_example_and_never_the_governance_sections(monkeypatch):
    _use(monkeypatch, "replay")
    out = service.prefill_from_text(
        "We score applicants for a supplementary health insurance package and propose a "
        "premium band; an underwriter decides. The model is licensed from a vendor.")
    assert out["mode"] == "auto" and out["provider"] == "replay"
    a = out["answers"]
    assert a["sys_name"].startswith("PolisPrijs")
    assert a["hr_essential_subarea"] == "insurance_life_health"
    assert not any(k.startswith(("dg_", "fr_", "gov_")) for k in a)
    assert any("Replay mode" in s for s in out["assumptions"])
    assert out["warnings"] == []                      # replayed fields validate cleanly
    # the engine still decides the tier from the draft
    assert classify(a)["tier"] == "high"


def test_prefill_is_deterministic_and_degrades_honestly(monkeypatch):
    _use(monkeypatch, "replay")
    d = "A chat assistant on a hosted large language model answers coverage questions."
    assert service.prefill_from_text(d)["answers"] == service.prefill_from_text(d)["answers"]
    out = service.prefill_from_text("qzx wvu ttt")     # nothing overlaps
    assert list(out["answers"]) == ["sys_description"]
    assert any("no shipped example" in s for s in out["assumptions"])


def test_best_match_ties_are_broken_alphabetically():
    lib = [{"id": "b", "name": "B", "keywords": {"claims"}, "answers": {}, "comment": ""},
           {"id": "a", "name": "A", "keywords": {"claims"}, "answers": {}, "comment": ""}]
    item, score = replay.best_match("claims scoring", lib)
    assert item["id"] == "a" and score == 1


def test_narrative_is_a_labelled_placeholder(monkeypatch):
    _use(monkeypatch, "replay")
    out = service.draft_narrative("human_oversight", {"sys_name": "x"})
    assert out["mode"] == "auto" and "[Replay draft" in out["text"]
    assert "human oversight" in out["text"].lower()


def test_mcp_transcript_asset_matches_the_engine():
    t = json.loads((ROOT / "static/demo/mcp_transcript.json").read_text(encoding="utf-8"))
    tools = [s["name"] for s in t["steps"] if s["role"] == "tool"]
    assert tools[:2] == ["get_questionnaire", "classify_ai_system"]
    assert "save_assessment" in tools and "generate_report" in tools
    classify_step = next(s for s in t["steps"] if s.get("name") == "classify_ai_system")
    answers = {k: v for k, v in json.loads((ROOT / "examples/health_insurance_pricing.json")
                                           .read_text(encoding="utf-8")).items()
               if not k.startswith("_")}
    assert classify_step["result"]["tier"] == classify(answers)["tier"]
    assert "Annex III(5)(c)" in classify_step["result"]["refs"]
