"""Model Card generator (Mitchell et al., 2019).

Pure function `generate_model_card(answers) -> dict`. Produces a Model Card
skeleton pre-filled from the intake answers, leaving the parts that require
measurement or judgement as `[to be completed]`. A light, well-known transparency
artifact whose natural EU AI Act anchor is **Art. 13** (transparency / information
to deployers).

Deterministic and AI-free. The pre-filled cells reflect the answers verbatim;
the section structure is fixed regardless of any free-text content.
"""

# The nine Model Card sections (Mitchell et al., 2019). Kept as a single source of
# truth so the renderer and its test agree on the headings.
MODEL_CARD_SECTIONS = [
    "Model details",
    "Intended use",
    "Factors",
    "Metrics",
    "Evaluation data",
    "Training data",
    "Quantitative analyses",
    "Ethical considerations",
    "Caveats and recommendations",
]

PROVENANCE = (
    "Structure adapted from the Model Cards framework (Mitchell et al., 2019). "
    "Pre-filled cells come from the intake answers; everything requiring "
    "measurement or judgement is left for the human to complete."
)

DISCLAIMER = (
    "This Model Card is a transparency-documentation aid (EU AI Act Art. 13). It "
    "is pre-filled from the provided answers and is not a substitute for a "
    "completed evaluation or for legal advice."
)


def _val(answers, key):
    v = answers.get(key)
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) if v else None
    return str(v)


def generate_model_card(answers):
    """Return the pre-filled Model Card field values for the given answers."""
    answers = answers or {}
    g = {k: _val(answers, k) for k in (
        "sys_name", "sys_version", "sys_owner", "provider_role",
        "intended_purpose", "sys_description", "lifecycle_stage",
        "data_sources", "human_oversight", "autonomy_level", "can_override",
        "data_personal", "data_special_category", "data_biometric",
        "automated_decision", "affects_vulnerable",
    )}
    return {
        "sections": list(MODEL_CARD_SECTIONS),
        "prefilled": g,
        "provenance": PROVENANCE,
        "disclaimer": DISCLAIMER,
    }
