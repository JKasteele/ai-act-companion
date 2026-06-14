"""Prompt builders for the AI layer.

The prompts are provider-agnostic (used both for Ollama and for the 'manual'
provider, where the user pastes the prompt into their own LLM session).
"""

import json

from ..questionnaire import QUESTIONNAIRE

_SYSTEM = (
    "You are an AI governance assistant. You help PRE-FILL an intake "
    "questionnaire for an EU AI Act risk assessment based on a free-text "
    "description of an AI system.\n\n"
    "STRICT RULES:\n"
    "- Only fill in fields for which you have reasonable grounds in the text. "
    "Leave unknown fields OUT (do not guess).\n"
    "- Do not invent facts. When in doubt: leave out and mention it under "
    "'assumptions'.\n"
    "- Your output is a DRAFT that a human reviews afterwards; it is never "
    "submitted automatically.\n"
    "- Respond with valid JSON only, with no extra text or explanation around it."
)


def _schema_digest():
    """Compact description of the fillable fields for the model."""
    lines = []
    for section in QUESTIONNAIRE["sections"]:
        lines.append(f"## {section['title']}")
        for q in section["questions"]:
            t = q["type"]
            if t in ("select", "radio", "multiselect"):
                opts = ", ".join(o["value"] for o in q.get("options", []))
                kind = f"{t} (choose from: {opts})"
            elif t == "boolean":
                kind = "boolean (true/false)"
            else:
                kind = t
            lines.append(f"- {q['id']} [{kind}]: {q['label']}")
    return "\n".join(lines)


def build_prefill_prompt(description):
    """Return (system, user) for the prefill task."""
    user = (
        "FIELDS (id [type]: question):\n"
        f"{_schema_digest()}\n\n"
        "DESCRIPTION OF THE AI SYSTEM:\n"
        f"\"\"\"\n{description.strip()}\n\"\"\"\n\n"
        "Return JSON with exactly this structure:\n"
        "{\n"
        '  "answers": { "<field-id>": <value>, ... },\n'
        '  "assumptions": ["<assumption or uncertainty in English>", ...]\n'
        "}\n\n"
        "Use true/false for booleans, an array of allowed option values for "
        "multiselect, and exactly one of the allowed values for select/radio. "
        "Be sure to fill in sys_name, sys_description and intended_purpose if "
        "they can be inferred.\n"
        "BE CONSERVATIVE with hr_usecases: only include an area if it follows "
        "explicitly from the description; otherwise choose [\"none\"]. Set a "
        "prohibited-practice field (p_*) or transparency field (t_*) to true "
        "only on clear indications. Note any doubt under 'assumptions'."
    )
    return _SYSTEM, user


# Fields for which a narrative AI text is useful, with a per-field instruction.
NARRATIVE_FIELDS = {
    "sys_description": "a clear technical and functional description of the AI system",
    "intended_purpose": "the intended purpose and context of use of the system",
    "human_oversight": "the measures for effective human oversight (EU AI Act Art. 14): who oversees, with which means, and at what thresholds intervention happens",
    "data_sources": "a short description of the origin of the training and input data",
}


def build_narrative_prompt(field, answers):
    """Return (system, user) for drafting a single narrative section."""
    what = NARRATIVE_FIELDS.get(field, "the requested section")
    context = {k: v for k, v in (answers or {}).items() if v not in (None, "", [])}
    system = (
        "You are an AI governance assistant that drafts narrative sections for "
        "an EU AI Act risk assessment. Write concisely, factually and in "
        "English. Do not invent facts that do not follow from the context; mark "
        "missing information with [to be completed]. The text is a DRAFT for "
        "human review. Respond with the text only, without headings or "
        "explanation."
    )
    user = (
        f"Draft {what}.\n\n"
        f"CONTEXT (already known answers):\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        "Write 2-5 sentences."
    )
    return system, user
