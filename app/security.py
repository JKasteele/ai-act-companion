"""AI security lens.

Pure function `assess_security(answers) -> dict`. Maps an AI system to the
applicable OWASP Top 10 for LLM Applications (2025) items, each carrying the
relevant MITRE ATLAS techniques and EU AI Act / NIST AI RMF controls. Relevance
is driven by the security-context intake answers (sec_*) plus a few governance
answers, so the lens adapts to the kind of system.

Deterministic and AI-free, like the governance classifier.
"""

from .knowledge import ai_security as sec


def _truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "ja", "on", "1"}
    return bool(value)


def assess_security(answers):
    """Return the applicable AI-security risks for the given answers."""
    answers = answers or {}

    def a(key):
        return _truthy(answers.get(key))

    is_llm = a("sec_is_llm")
    external = a("sec_external_data")
    public = a("sec_public")
    agentic = a("sec_agentic")
    third_party = a("sec_third_party_models") or a("gpai_model")
    outputs_to_systems = a("sec_outputs_to_systems")
    personal = a("data_personal") or a("data_special_category") or a("data_biometric")
    large_scale = answers.get("data_scale") == "large"

    # rule -> reason. Each maps to an OWASP id.
    rules = {
        "LLM01": (is_llm and (external or public or agentic),
                  "LLM/generative system exposed to untrusted or retrieved input"),
        "LLM02": (personal,
                  "processes personal/special-category data that could be disclosed"),
        "LLM03": (third_party,
                  "relies on third-party/foundation models or external components"),
        "LLM04": (external,
                  "ingests untrusted external/user data that could poison the model"),
        "LLM05": (outputs_to_systems,
                  "output is passed to downstream systems without human review"),
        "LLM06": (agentic,
                  "can autonomously take actions or call tools"),
        "LLM07": (is_llm,
                  "uses a system prompt that may leak"),
        "LLM08": (is_llm and (personal or third_party),
                  "likely uses embeddings/RAG over sensitive or external content"),
        "LLM09": (is_llm,
                  "generative output may be inaccurate (hallucination) yet relied upon"),
        "LLM10": (public or large_scale,
                  "exposed/large-scale: vulnerable to resource exhaustion or extraction"),
    }

    risks = []
    for oid, (applies, reason) in rules.items():
        if not applies:
            continue
        info = sec.OWASP_LLM_TOP10[oid]
        risks.append({
            "id": info["id"],
            "name": info["name"],
            "why": reason,
            "summary": info["summary"],
            "atlas": [{"id": tid, "name": tname} for tid, tname in info["atlas"]],
            "atlas_note": info.get("atlas_note"),
            "ai_act_refs": list(info["ai_act_refs"]),
            "nist_refs": list(info["nist_refs"]),
            "mitigation": info["mitigation"],
        })

    answered = any(a(k) for k in (
        "sec_is_llm", "sec_third_party_models", "sec_external_data",
        "sec_agentic", "sec_public", "sec_outputs_to_systems"))

    if not risks:
        summary = (
            "No AI-security risks were triggered by the answers. "
            + ("Provide the AI security context (section 8) for a meaningful "
               "assessment." if not answered else
               "Baseline hardening and monitoring still apply.")
        )
    else:
        summary = (
            f"{len(risks)} OWASP Top 10 for LLM Applications (2025) item(s) apply, "
            "mapped to MITRE ATLAS and EU AI Act Art. 15."
        )

    return {
        "risks": risks,
        "summary": summary,
        "answered": answered,
        "provenance": sec.PROVENANCE,
        "disclaimer": sec.DISCLAIMER,
    }
