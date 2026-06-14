"""High-level AI services. Orchestrates provider + prompts + validation.

GUARANTEE (human-in-the-loop): no function here stores an assessment or submits
anything. All output is a DRAFT that the user reviews in the frontend and only
then classifies (manually).
"""

from . import prompts
from .base import extract_json, get_provider, validate_answers

# Added to every AI response, so the frontend always shows it.
HITL_NOTICE = (
    "AI-generated DRAFT. Review and correct every field before you classify. "
    "Nothing is submitted or stored automatically."
)


def status():
    provider = get_provider()
    if provider is None:
        return {"enabled": False, "provider": "none",
                "reason": "AI layer disabled (LLM_PROVIDER=none)."}
    st = provider.status()
    st["enabled"] = True
    st["hitl_notice"] = HITL_NOTICE
    return st


def _parse_prefill_payload(raw_text):
    """Turn raw model output into a validated draft."""
    data = extract_json(raw_text) or {}
    raw_answers = data.get("answers", data)  # tolerate a flat answer object
    assumptions = data.get("assumptions", [])
    if not isinstance(assumptions, list):
        assumptions = [str(assumptions)]
    answers, warnings = validate_answers(raw_answers)
    return {
        "answers": answers,
        "assumptions": assumptions,
        "warnings": warnings,
        "hitl_notice": HITL_NOTICE,
    }


def prefill_from_text(description):
    """Pre-fill the questionnaire based on a free-text description.

    Non-interactive (Ollama): calls the model and returns a draft.
    Interactive (manual): returns a paste-ready prompt.
    """
    provider = get_provider()
    if provider is None:
        return {"mode": "disabled", "hitl_notice": HITL_NOTICE}

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
    return result


def parse_completion(pasted_text):
    """Parse an LLM answer pasted back by the user (manual flow)."""
    result = _parse_prefill_payload(pasted_text)
    result["mode"] = "parsed"
    return result


def draft_narrative(field, answers):
    """Draft a single narrative section (draft)."""
    provider = get_provider()
    if provider is None:
        return {"mode": "disabled", "hitl_notice": HITL_NOTICE}

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
    import re
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL | re.IGNORECASE).strip()
    return {"mode": "auto", "provider": provider.name, "field": field,
            "text": text, "hitl_notice": HITL_NOTICE}
