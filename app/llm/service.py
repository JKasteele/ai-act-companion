"""High-level AI services. Orchestrates provider + prompts + validation.

GUARANTEE (human-in-the-loop): no function here stores an assessment or submits
anything. All output is a DRAFT that the user reviews in the frontend and only
then classifies (manually).
"""

import re

from . import budget, prompts
from .base import extract_json, get_provider, validate_answers

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

    raw = provider.generate(system, user, as_json=True)
    result = _parse_prefill_payload(raw)
    result["mode"] = "auto"
    result["provider"] = provider.name
    if provider.name == "anthropic":
        budget.note_ip(ip)
    elif configured.name == "anthropic":
        result["fallback_from"] = "anthropic"
        result["fallback_reason"] = getattr(provider, "fallback_reason", "")
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

    text = provider.generate(system, user, as_json=False)
    # Strip any <think> blocks from reasoning models.
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL | re.IGNORECASE).strip()
    result = {"mode": "auto", "provider": provider.name, "field": field,
              "text": text, "hitl_notice": HITL_NOTICE}
    if provider.name == "anthropic":
        budget.note_ip(ip)
    elif configured.name == "anthropic":
        result["fallback_from"] = "anthropic"
        result["fallback_reason"] = getattr(provider, "fallback_reason", "")
    return result
