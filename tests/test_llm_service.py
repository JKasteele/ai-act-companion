"""Tests for the optional AI layer (app/llm/*) and its API endpoints.

The AI layer may ONLY draft/pre-fill; it never classifies or stores. These tests
cover the orchestration in service.py, the deterministic `manual` provider, and
the Ollama auto path with the HTTP call mocked (no network). The end-to-end
guarantee — hostile model output cannot reach the classifier — is proven in
test_red_team.py; here we cover the plumbing.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.llm import service  # noqa: E402
from app.llm.config import settings  # noqa: E402


@pytest.fixture
def provider(monkeypatch):
    """Set the active provider for a test (patches the settings singleton)."""
    def _set(name):
        monkeypatch.setattr(settings, "provider", name)
    return _set


# --- status ----------------------------------------------------------------
def test_status_disabled_when_provider_none(provider):
    provider("none")
    st = service.status()
    assert st["enabled"] is False and st["provider"] == "none"


def test_status_manual_is_enabled_and_carries_hitl(provider):
    provider("manual")
    st = service.status()
    assert st["enabled"] is True and st["provider"] == "manual"
    assert st["interactive"] is True and st["hitl_notice"]


# --- manual (interactive) flow ---------------------------------------------
def test_prefill_manual_returns_paste_ready_prompt(provider):
    provider("manual")
    out = service.prefill_from_text("A CV screening model for hiring.")
    assert out["mode"] == "manual"
    assert "CV screening model" in out["prompt"]
    assert out["hitl_notice"]


def test_draft_narrative_manual_returns_prompt(provider):
    provider("manual")
    out = service.draft_narrative("sys_description", {"sys_name": "X"})
    assert out["mode"] == "manual" and out["prompt"]


def test_prefill_disabled_when_off(provider):
    provider("none")
    assert service.prefill_from_text("anything")["mode"] == "disabled"


# --- parse_completion validates and strips injected fields -----------------
def test_parse_completion_keeps_only_schema_fields(provider):
    provider("manual")
    pasted = ('{"answers": {"eu_market": true, "hr_usecases": ["employment"], '
              '"tier": "minimal", "evil": "x"}}')
    out = service.parse_completion(pasted)
    assert out["mode"] == "parsed"
    assert out["answers"] == {"eu_market": True, "hr_usecases": ["employment"]}
    assert any("tier" in w or "evil" in w for w in out["warnings"])


# --- Ollama auto path with the HTTP call mocked ----------------------------
def test_prefill_auto_path_with_mocked_generate(provider, monkeypatch):
    provider("ollama")
    from app.llm import ollama
    canned = '{"answers": {"eu_market": true, "hr_usecases": ["employment"]}, ' \
             '"assumptions": ["assumed EU deployment"]}'
    monkeypatch.setattr(ollama.OllamaProvider, "generate",
                        lambda self, system, user, as_json=True: canned)
    out = service.prefill_from_text("hiring model")
    assert out["mode"] == "auto" and out["provider"] == "ollama"
    assert out["answers"]["hr_usecases"] == ["employment"]
    assert out["assumptions"] == ["assumed EU deployment"]


def test_narrative_auto_strips_think_tags(provider, monkeypatch):
    provider("ollama")
    from app.llm import ollama
    monkeypatch.setattr(
        ollama.OllamaProvider, "generate",
        lambda self, system, user, as_json=False: "<think>reason</think>Final text.")
    out = service.draft_narrative("sys_description", {"sys_name": "X"})
    assert out["mode"] == "auto"
    assert out["text"] == "Final text."


# --- API endpoints ---------------------------------------------------------
def _client():
    from fastapi.testclient import TestClient

    from app.main import app
    return TestClient(app)


def test_ai_status_endpoint_returns_200():
    r = _client().get("/api/ai/status")
    assert r.status_code == 200
    assert "provider" in r.json() or "enabled" in r.json()


def test_ai_prefill_rejects_empty_description():
    r = _client().post("/api/ai/prefill", json={"description": "   "})
    assert r.status_code == 400


def test_ai_parse_endpoint_validates_pasted_json():
    r = _client().post("/api/ai/parse",
                       json={"text": '{"answers": {"eu_market": true, "tier": "x"}}'})
    assert r.status_code == 200
    body = r.json()
    assert body["answers"] == {"eu_market": True}
    assert body["mode"] == "parsed"
