"""Tests for the hosted Anthropic provider and its spend guard (app/llm/budget.py,
app/llm/anthropic_provider.py, and the provider_for() fallback logic in service.py).

No network: `anthropic.Anthropic` is monkeypatched with a fake client that records
the kwargs passed to `messages.create` and returns a canned response object shaped
like the real SDK's (`.stop_reason`, `.content`, `.usage`).
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.llm import budget, service  # noqa: E402
from app.llm.config import settings  # noqa: E402


# --- fakes -------------------------------------------------------------------
class FakeUsage:
    def __init__(self, input_tokens=0, output_tokens=0,
                 cache_read_input_tokens=0, cache_creation_input_tokens=0):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_read_input_tokens = cache_read_input_tokens
        self.cache_creation_input_tokens = cache_creation_input_tokens


class FakeTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class FakeResponse:
    def __init__(self, text="OK", stop_reason="end_turn", usage=None):
        self.stop_reason = stop_reason
        self.content = [FakeTextBlock(text)] if text is not None else []
        self.usage = usage or FakeUsage()


class FakeMessages:
    def __init__(self, response_factory):
        self.response_factory = response_factory
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response_factory(kwargs)


class FakeClient:
    def __init__(self, response_factory):
        self.messages = FakeMessages(response_factory)


def install_fake_anthropic(monkeypatch, response_factory):
    """Patch anthropic.Anthropic so AnthropicProvider.generate() never hits the
    network. Returns a dict that will hold the constructed fake client under
    "client" once generate() has run (the provider builds the client lazily)."""
    import anthropic
    holder = {}

    def _make_client(*args, **kwargs):
        client = FakeClient(response_factory)
        holder["client"] = client
        return client

    monkeypatch.setattr(anthropic, "Anthropic", _make_client)
    return holder


def _canned(answers=None, assumptions=None):
    return json.dumps({"answers": answers or {}, "assumptions": assumptions or []})


# --- isolation -----------------------------------------------------------
@pytest.fixture(autouse=True)
def _isolated_budget(tmp_path, monkeypatch):
    """Every test in this file gets its own spend file and a clean per-IP
    counter, so nothing here can touch (or race with) the real data/ dir."""
    monkeypatch.setenv("AIACT_DATA_DIR", str(tmp_path))
    budget.reset_for_tests()
    yield
    budget.reset_for_tests()


@pytest.fixture
def with_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake-not-real")


@pytest.fixture
def as_anthropic(monkeypatch):
    monkeypatch.setattr(settings, "provider", "anthropic")


# --- (a) request shape + prefill happy path ---------------------------------
def test_prefill_via_anthropic_uses_expected_request_shape(monkeypatch, with_key, as_anthropic):
    canned = _canned({"eu_market": True, "hr_usecases": ["employment"]}, ["assumed EU deployment"])
    holder = install_fake_anthropic(
        monkeypatch,
        lambda kwargs: FakeResponse(text=canned, usage=FakeUsage(input_tokens=100, output_tokens=50)),
    )

    out = service.prefill_from_text("A CV screening model for hiring.")

    assert out["mode"] == "auto"
    assert out["provider"] == "anthropic"
    assert out["answers"]["hr_usecases"] == ["employment"]
    assert out["assumptions"] == ["assumed EU deployment"]

    call = holder["client"].messages.calls[0]
    assert call["model"] == "claude-haiku-4-5"   # default hosted model
    assert "output_config" not in call                  # Haiku rejects effort
    system = call["system"]
    assert len(system) == 2
    assert "cache_control" in system[1]
    assert system[1]["cache_control"] == {"type": "ephemeral"}
    assert system[1]["text"].startswith("FIELDS")
    assert "cache_control" not in system[0]
    user_msg = call["messages"][0]["content"]
    assert user_msg.startswith("DESCRIPTION OF THE AI SYSTEM")


# --- (b) budget accounting ---------------------------------------------------
def test_estimate_cost_matches_the_documented_rate():
    assert budget.estimate_cost({"input_tokens": 1_000_000}, "claude-sonnet-5") == 2.0


@pytest.fixture(autouse=True)
def _clear_prefill_cache():
    from app.llm import service as _svc
    _svc._PREFILL_CACHE.clear()
    yield
    _svc._PREFILL_CACHE.clear()


def test_record_grows_spent_and_shrinks_remaining():
    st0 = budget.state()
    budget.record(FakeUsage(input_tokens=100_000, output_tokens=100_000), "claude-sonnet-5")
    st1 = budget.state()
    assert st1["spent_usd"] > st0["spent_usd"]
    assert st1["remaining_usd"] < st0["remaining_usd"]


# --- (c) lifetime budget exhaustion -----------------------------------------
def test_prefill_falls_back_when_budget_exhausted(monkeypatch, with_key, as_anthropic):
    monkeypatch.setenv("AI_BUDGET_USD", "0.001")
    install_fake_anthropic(
        monkeypatch,
        lambda kwargs: FakeResponse(
            text=_canned(), usage=FakeUsage(input_tokens=10_000, output_tokens=10_000)),
    )

    out1 = service.prefill_from_text("desc one")
    assert out1["provider"] == "anthropic"

    out2 = service.prefill_from_text("desc two")
    assert out2["provider"] == "replay"
    assert out2["fallback_from"] == "anthropic"
    assert out2["fallback_reason"] == "budget"

    st = service.status()
    assert st["provider"] == "replay"
    assert st["fallback_from"] == "anthropic"
    assert st["fallback_reason"] == "budget"
    assert "budget" in st


# --- (d) daily call cap ------------------------------------------------------
def test_prefill_falls_back_when_daily_cap_hit(monkeypatch, with_key, as_anthropic):
    monkeypatch.setenv("AI_DAILY_CALLS", "1")
    install_fake_anthropic(
        monkeypatch,
        lambda kwargs: FakeResponse(text=_canned(), usage=FakeUsage(input_tokens=1, output_tokens=1)),
    )

    out1 = service.prefill_from_text("d1")
    assert out1["provider"] == "anthropic"

    out2 = service.prefill_from_text("d2")
    assert out2["provider"] == "replay"
    assert out2["fallback_reason"] == "daily_cap"


# --- (e) per-IP cap -----------------------------------------------------------
def test_prefill_per_ip_cap_other_ip_unaffected(monkeypatch, with_key, as_anthropic):
    monkeypatch.setenv("AI_CALLS_PER_IP_DAY", "1")
    install_fake_anthropic(
        monkeypatch,
        lambda kwargs: FakeResponse(text=_canned(), usage=FakeUsage(input_tokens=1, output_tokens=1)),
    )

    out1 = service.prefill_from_text("d1", ip="1.2.3.4")
    assert out1["provider"] == "anthropic"

    out2 = service.prefill_from_text("d2", ip="1.2.3.4")
    assert out2["provider"] == "replay"
    assert out2["fallback_reason"] == "per_ip_cap"

    out3 = service.prefill_from_text("d3", ip="5.6.7.8")
    assert out3["provider"] == "anthropic"


# --- (f) no API key -----------------------------------------------------------
def test_no_api_key_reports_unavailable_and_falls_back(monkeypatch, as_anthropic):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    st = service.status()
    assert st["provider"] == "replay"
    assert st["fallback_from"] == "anthropic"
    assert st["fallback_reason"] == "unavailable"
    assert "budget" in st

    out = service.prefill_from_text("desc")
    assert out["provider"] == "replay"
    assert out["fallback_from"] == "anthropic"
    assert out["fallback_reason"] == "unavailable"


# --- (g) refusal --------------------------------------------------------------
def test_refusal_returns_draft_with_warning_not_raise(monkeypatch, with_key, as_anthropic):
    install_fake_anthropic(
        monkeypatch,
        lambda kwargs: FakeResponse(
            text=None, stop_reason="refusal", usage=FakeUsage(input_tokens=5, output_tokens=0)),
    )

    out = service.prefill_from_text("desc")
    assert out["provider"] == "anthropic"
    assert out["answers"] == {}
    assert out["warnings"]


# --- (h) persistence -----------------------------------------------------------
def test_spend_persists_on_disk_across_state_reads(tmp_path):
    budget.record(FakeUsage(input_tokens=100_000, output_tokens=100_000), "claude-sonnet-5")
    st1 = budget.state()
    assert (tmp_path / "ai_spend.json").exists()
    st2 = budget.state()  # a fresh read; state() always reloads from disk
    assert st2["spent_usd"] == st1["spent_usd"] > 0


def test_workspace_id_is_sent_as_default_header(monkeypatch, tmp_path):
    """Identity-linked keys need the anthropic-workspace-id header on every call."""
    import anthropic as sdk

    from app.llm import budget
    from app.llm.anthropic_provider import AnthropicProvider
    from app.llm.config import settings

    monkeypatch.setenv("AIACT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    budget.reset_for_tests()
    monkeypatch.setattr(settings, "anthropic_workspace_id", "wrkspc_test123")
    seen = {}

    class _Usage:
        input_tokens = 10
        output_tokens = 5
        cache_read_input_tokens = 0
        cache_creation_input_tokens = 0

    class _Block:
        type = "text"
        text = "{\"answers\": {}, \"assumptions\": []}"

    class _Resp:
        stop_reason = "end_turn"
        content = [_Block()]
        usage = _Usage()

    class _Messages:
        def create(self, **kw):
            return _Resp()

    class _Client:
        def __init__(self, **kw):
            seen.update(kw)
            self.messages = _Messages()

    monkeypatch.setattr(sdk, "Anthropic", _Client)
    prov = AnthropicProvider()
    assert prov.status()["workspace_id"] == "wrkspc_test123"
    prov.generate("sys", "user text", as_json=True)
    assert seen["default_headers"] == {"anthropic-workspace-id": "wrkspc_test123"}
    monkeypatch.setattr(settings, "anthropic_workspace_id", "")
    AnthropicProvider().generate("sys", "user text", as_json=True)
    assert seen["default_headers"] is None


def test_live_call_failure_degrades_to_replay(monkeypatch, tmp_path):
    """Auth/credit/network errors at call time must not surface as a 502: the
    demo replays a draft and names the reason."""
    import anthropic as sdk

    from app.llm import budget, service
    from app.llm.config import settings

    monkeypatch.setenv("AIACT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "provider", "anthropic")
    budget.reset_for_tests()

    class _Messages:
        def create(self, **kw):
            raise RuntimeError("Your credit balance is too low to access the Anthropic API.")

    class _Client:
        def __init__(self, **kw):
            self.messages = _Messages()

    monkeypatch.setattr(sdk, "Anthropic", _Client)
    out = service.prefill_from_text("A chat assistant answers insured persons questions "
                                    "about coverage and looks up their claim status.")
    assert out["mode"] == "auto" and out["provider"] == "replay"
    assert out["fallback_from"] == "anthropic" and out["fallback_reason"] == "credits"
    assert out["answers"].get("sys_name")                      # a replayed draft, not empty
    assert budget.state()["calls_total"] == 0                  # nothing was billed
    nar = service.draft_narrative("human_oversight", {"sys_name": "x"})
    assert nar["provider"] == "replay" and nar["fallback_reason"] == "credits"


def _fake_sdk(monkeypatch, seen=None):
    import anthropic as sdk

    class _Usage:
        input_tokens = 10
        output_tokens = 5
        cache_read_input_tokens = 0
        cache_creation_input_tokens = 0

    class _Block:
        type = "text"
        text = '{"answers": {"sys_name": "Live draft"}, "assumptions": []}'

    class _Resp:
        stop_reason = "end_turn"
        content = [_Block()]
        usage = _Usage()

    class _Messages:
        def create(self, **kw):
            if seen is not None:
                seen.append(kw)
            return _Resp()

    class _Client:
        def __init__(self, **kw):
            self.messages = _Messages()

    monkeypatch.setattr(sdk, "Anthropic", _Client)


def test_cooldown_and_dedupe_cache_stop_rapid_repeats(monkeypatch, tmp_path):
    from app.llm import budget, service
    from app.llm.config import settings

    monkeypatch.setenv("AIACT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("AI_COOLDOWN_SECONDS", "60")
    monkeypatch.setattr(settings, "provider", "anthropic")
    budget.reset_for_tests()
    service._PREFILL_CACHE.clear()
    calls = []
    _fake_sdk(monkeypatch, calls)
    first = service.prefill_from_text("A brand new description one", ip="1.1.1.1")
    assert first["provider"] == "anthropic" and len(calls) == 1
    again = service.prefill_from_text("  a BRAND new   description one ", ip="1.1.1.1")
    assert again.get("cached") is True and len(calls) == 1          # served from cache
    other = service.prefill_from_text("A different description two", ip="1.1.1.1")
    assert other["provider"] == "replay" and other["fallback_reason"] == "cooldown"
    assert len(calls) == 1
    third = service.prefill_from_text("A different description two", ip="2.2.2.2")
    assert third["provider"] == "anthropic" and len(calls) == 2     # other client unaffected
    assert budget.state()["cooldown_seconds"] == 60.0
    assert budget.budget_usd() == 4.0 and budget.daily_cap() == 25


def test_client_ip_uses_the_proxy_appended_hop():
    from app.main import _client_ip

    class _Req:
        def __init__(self, xff, host="10.0.0.9"):
            self.headers = {"x-forwarded-for": xff} if xff else {}
            self.client = type("C", (), {"host": host})()

    assert _client_ip(_Req("1.2.3.4, 203.0.113.7")) == "203.0.113.7"   # spoofed first hop ignored
    assert _client_ip(_Req("203.0.113.7")) == "203.0.113.7"
    assert _client_ip(_Req("")) == "10.0.0.9"


def test_effort_is_sent_only_for_models_that_support_it(monkeypatch, tmp_path):
    from app.llm import budget
    from app.llm.anthropic_provider import AnthropicProvider
    from app.llm.config import settings

    monkeypatch.setenv("AIACT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    budget.reset_for_tests()
    calls = []
    _fake_sdk(monkeypatch, calls)
    monkeypatch.setattr(settings, "anthropic_model", "claude-sonnet-5")
    AnthropicProvider().generate("s", "u", as_json=True)
    assert calls[-1]["output_config"] == {"effort": "low"}
    monkeypatch.setattr(settings, "anthropic_model", "claude-haiku-4-5")
    AnthropicProvider().generate("s", "u", as_json=True)
    assert "output_config" not in calls[-1]
