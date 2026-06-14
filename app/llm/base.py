"""Provider interface, parsing/validation and factory for the AI layer.

Two kinds of providers:
  - non-interactive (e.g. Ollama): calls an LLM itself via .generate().
  - interactive (manual): calls nothing; the user pastes the prompt into their
    own LLM session and pastes the answer back. .interactive == True.
"""

import json
import re

from ..questionnaire import QUESTIONNAIRE


class LLMProvider:
    name = "base"
    interactive = False

    def status(self):
        """Return a dict with availability info for the frontend."""
        return {"provider": self.name, "interactive": self.interactive, "available": False}

    def generate(self, system, user, as_json=True):
        """Call the model and return the raw text (non-interactive)."""
        raise NotImplementedError


# --- parsing & validatie ---------------------------------------------------
def _question_index():
    idx = {}
    for section in QUESTIONNAIRE["sections"]:
        for q in section["questions"]:
            idx[q["id"]] = q
    return idx


_QIDX = _question_index()


def _coerce_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in {"true", "ja", "yes", "1"}
    return None


def extract_json(text):
    """Extract the first JSON object from raw model output.

    Robust against ```json ... ``` fences and <think>...</think> from
    reasoning models.
    """
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"```(?:json)?", "", text).strip("` \n\t")
    # Try directly, otherwise the first {...} block.
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except (json.JSONDecodeError, ValueError):
            return None
    return None


def validate_answers(raw_answers):
    """Validate/coerce raw answers against the questionnaire schema.

    Returns (clean_answers, warnings). Unknown fields and invalid enum values
    are dropped (no silent errors).
    """
    clean, warnings = {}, []
    if not isinstance(raw_answers, dict):
        return clean, ["AI output contained no 'answers' object."]

    for key, value in raw_answers.items():
        q = _QIDX.get(key)
        if not q:
            warnings.append(f"Unknown field ignored: {key}")
            continue
        t = q["type"]
        if value in (None, ""):
            continue

        if t == "boolean":
            b = _coerce_bool(value)
            if b is None:
                warnings.append(f"Invalid boolean for {key}: {value!r}")
            else:
                clean[key] = b
        elif t in ("select", "radio"):
            allowed = {o["value"] for o in q.get("options", [])}
            if value in allowed:
                clean[key] = value
            else:
                warnings.append(f"Invalid option for {key}: {value!r}")
        elif t == "multiselect":
            allowed = {o["value"] for o in q.get("options", [])}
            vals = value if isinstance(value, list) else [value]
            kept = [v for v in vals if v in allowed]
            dropped = [v for v in vals if v not in allowed]
            if dropped:
                warnings.append(f"Invalid options for {key}: {dropped}")
            if kept:
                clean[key] = kept
        else:  # text / textarea
            clean[key] = str(value)
    return clean, warnings


# --- factory ---------------------------------------------------------------
def get_provider():
    """Instantiate the provider based on the configuration."""
    from .config import settings
    name = settings.provider
    if name == "ollama":
        from .ollama import OllamaProvider
        return OllamaProvider()
    if name == "manual":
        from .manual import ManualProvider
        return ManualProvider()
    return None  # 'none' or unknown -> AI layer off
