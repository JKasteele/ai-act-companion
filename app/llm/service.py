"""High-level AI services. Orchestrates provider + prompts + validation.

GUARANTEE (human-in-the-loop): no function here stores an assessment or submits
anything. All output is a DRAFT that the user reviews in the frontend and only
then classifies (manually).
"""

import logging
import re
import time

from . import budget, prompts
from .base import extract_json, get_provider, validate_answers

logger = logging.getLogger(__name__)

# Added to every AI response, so the frontend always shows it.
HITL_NOTICE = (
    "AI-generated DRAFT. Review and correct every field before you classify. "
    "Nothing is submitted or stored automatically."
)


def provider_for(ip=None):
    """The provider to actually use for one call, applying the spend guard.

    The configured provider may be `anthropic` (a real, billed model), so every
    call is gated: if the lifetime budget, daily call cap or per-IP daily cap is
    exhausted - or no API key is configured - this returns a ReplayProvider
    instead, with `.fallback_reason` set so callers can say why. Any other
    configured provider (ollama/manual/replay/none) passes through unchanged.
    """
    p = get_provider()
    if p is not None and p.name == "anthropic":
        if not p.status()["available"]:
            reason = "unavailable"
        else:
            ok, reason = budget.allow(ip)
            if ok:
                return p
        from .replay import ReplayProvider
        fallback = ReplayProvider()
        fallback.fallback_reason = reason
        return fallback
    return p


def _call_live_or_replay(provider, system, user, as_json):
    """Call `provider`. Only the hosted provider can fail at call time (auth,
    credits, network); when it does the demo must keep working, so log the
    failure for the operator and return a replayed draft instead of a 502.
    Returns (raw_output, provider_used, error_reason_or_None)."""
    try:
        return provider.generate(system, user, as_json=as_json), provider, None
    except Exception as e:  # noqa: BLE001
        if provider.name != "anthropic":
            raise
        from .replay import ReplayProvider
        logger.warning("Live AI call failed, replaying a draft instead: %s", e)
        replay = ReplayProvider()
        reason = "credits" if "credit balance" in str(e).lower() else "error"
        replay.fallback_reason = reason
        return replay.generate(system, user, as_json=as_json), replay, reason


def status():
    provider = get_provider()
    if provider is None:
        return {"enabled": False, "provider": "none",
                "reason": "AI layer disabled (LLM_PROVIDER=none)."}
    st = provider.status()
    st["enabled"] = True
    st["hitl_notice"] = HITL_NOTICE
    if provider.name == "anthropic":
        st["budget"] = budget.state()
        effective = provider_for()
        if effective.name != provider.name:
            replay_st = effective.status()
            replay_st["enabled"] = True
            replay_st["hitl_notice"] = HITL_NOTICE
            replay_st["fallback_from"] = provider.name
            replay_st["fallback_reason"] = getattr(effective, "fallback_reason", "")
            replay_st["budget"] = budget.state()
            return replay_st
    return st


def _parse_prefill_payload(raw_text):
    """Turn raw model output into a validated draft."""
    data = extract_json(raw_text)
    warnings = []
    if data is None:
        data = {}
        if raw_text:
            warnings.append("AI response was not valid JSON; no fields extracted.")
        else:
            # e.g. an Anthropic refusal (stop_reason == "refusal") returns "".
            warnings.append("AI returned no output (possibly refused or empty response).")
    raw_answers = data.get("answers", data)  # tolerate a flat answer object
    assumptions = data.get("assumptions", [])
    if not isinstance(assumptions, list):
        assumptions = [str(assumptions)]
    answers, val_warnings = validate_answers(raw_answers)
    warnings.extend(val_warnings)
    return {
        "answers": answers,
        "assumptions": assumptions,
        "warnings": warnings,
        "hitl_notice": HITL_NOTICE,
    }


# Identical descriptions within an hour get the earlier live draft back at no
# cost (a bot replaying the same text stops costing money after one call).
_PREFILL_CACHE: dict[str, tuple[float, dict]] = {}
_PREFILL_TTL = 3600.0
_PREFILL_CACHE_MAX = 200


def _cache_key(description):
    return " ".join(description.lower().split())


def _cache_get(key):
    hit = _PREFILL_CACHE.get(key)
    if hit and time.monotonic() - hit[0] < _PREFILL_TTL:
        return dict(hit[1], cached=True)
    return None


def _cache_put(key, result):
    if len(_PREFILL_CACHE) >= _PREFILL_CACHE_MAX:
        _PREFILL_CACHE.pop(next(iter(_PREFILL_CACHE)))
    _PREFILL_CACHE[key] = (time.monotonic(), dict(result))


def prefill_from_text(description, ip=None):
    """Pre-fill the questionnaire based on a free-text description.

    Non-interactive (Ollama, Anthropic): calls the model and returns a draft.
    Interactive (manual): returns a paste-ready prompt.

    `ip` is only used to apply the Anthropic spend guard's per-IP cap
    (provider_for()); every other provider ignores it.
    """
    configured = get_provider()
    if configured is None:
        return {"mode": "disabled", "hitl_notice": HITL_NOTICE}

    key = _cache_key(description)
    if configured.name == "anthropic":
        cached = _cache_get(key)
        if cached:
            return cached
    provider = provider_for(ip)
    system, user = prompts.build_prefill_prompt(description)

    if provider.interactive:
        return {
            "mode": "manual",
            "provider": provider.name,
            "prompt": provider.build_prompt(system, user),
            "instructions": (
                "Paste this prompt into your own LLM session (e.g. Claude), "
                "copy the JSON answer and paste it back below to pre-fill the "
                "questionnaire."
            ),
            "hitl_notice": HITL_NOTICE,
        }

    raw, provider, error_reason = _call_live_or_replay(provider, system, user, as_json=True)
    result = _parse_prefill_payload(raw)
    result["mode"] = "auto"
    result["provider"] = provider.name
    if provider.name == "anthropic":
        budget.note_ip(ip)
        _cache_put(key, result)
    elif configured.name == "anthropic":
        result["fallback_from"] = "anthropic"
        result["fallback_reason"] = error_reason or getattr(provider, "fallback_reason", "")
    return result


def parse_completion(pasted_text):
    """Parse an LLM answer pasted back by the user (manual flow)."""
    result = _parse_prefill_payload(pasted_text)
    result["mode"] = "parsed"
    return result


def draft_narrative(field, answers, ip=None):
    """Draft a single narrative section (draft).

    `ip` is only used to apply the Anthropic spend guard's per-IP cap
    (provider_for()); every other provider ignores it.
    """
    configured = get_provider()
    if configured is None:
        return {"mode": "disabled", "hitl_notice": HITL_NOTICE}

    provider = provider_for(ip)
    system, user = prompts.build_narrative_prompt(field, answers)

    if provider.interactive:
        return {
            "mode": "manual",
            "provider": provider.name,
            "prompt": provider.build_prompt(system, user),
            "hitl_notice": HITL_NOTICE,
        }

    text, provider, error_reason = _call_live_or_replay(provider, system, user, as_json=False)
    # Strip any <think> blocks from reasoning models.
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL | re.IGNORECASE).strip()
    result = {"mode": "auto", "provider": provider.name, "field": field,
              "text": text, "hitl_notice": HITL_NOTICE}
    if provider.name == "anthropic":
        budget.note_ip(ip)
    elif configured.name == "anthropic":
        result["fallback_from"] = "anthropic"
        result["fallback_reason"] = error_reason or getattr(provider, "fallback_reason", "")
    return result
