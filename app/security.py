"""AI security lens.

Pure function `assess_security(answers) -> dict`. Maps an AI system to the
applicable OWASP Top 10 for LLM Applications (2025) items, each carrying the
relevant MITRE ATLAS techniques and EU AI Act / NIST AI RMF controls. Relevance
is driven by the security-context intake answers (sec_*) plus a few governance
answers, so the lens adapts to the kind of system.

Deterministic and AI-free, like the governance classifier.
"""

from .knowledge import ai_security as sec

# --- architecture-aware severity -------------------------------------------
# Severity is a PURE function of the structured arch_* fields (booleans/selects);
# it never reads narrative/free-text, so crafted text cannot move a severity
# (the red-team invariant). Each severity carries a rationale naming the
# architecture fact(s) that set it — the same explainability contract as the
# governance classifier.
SEVERITY_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
_SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]

# OWASP items grouped by how their severity is driven by the architecture.
_INJECTION_FAMILY = {"LLM01", "LLM02", "LLM07", "LLM08"}   # injection / disclosure
_TAMPERING_FAMILY = {"LLM05", "LLM06"}                     # integrity / agency


def _truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "ja", "on", "1"}
    return bool(value)


def _select(answers, key):
    v = answers.get(key)
    return v.strip().lower() if isinstance(v, str) else ""


def _arch_view(answers):
    """Normalised view of the architecture-context fields. Reads ONLY arch_*
    keys — never narrative/free-text — so severity is injection-proof."""
    return {
        "auth": _select(answers, "arch_auth_strength"),
        "api_write": _truthy(answers.get("arch_api_write")),
        "downstream": _truthy(answers.get("arch_downstream_actions")),
        "acl": _select(answers, "arch_access_control_layer"),
        "scope": _select(answers, "arch_data_scope"),
        "rag_mod": _truthy(answers.get("arch_rag_modifiable")),
        "identity": _select(answers, "arch_identity_model"),
        "logging": _truthy(answers.get("arch_logging")),
        "rate_limits": _truthy(answers.get("arch_rate_limits")),
        "provided": any(answers.get(k) for k in (
            "arch_auth_strength", "arch_api_write", "arch_downstream_actions",
            "arch_access_control_layer", "arch_data_scope", "arch_rag_modifiable",
            "arch_identity_model", "arch_logging", "arch_rate_limits")),
    }


def arch_view(answers):
    """Public alias of the normalised architecture-context view (`_arch_view`).

    Exposed so other deterministic lenses (e.g. the STRIDE threat model) read the
    SAME structured `arch_*` fields and stay injection-proof in the same way."""
    return _arch_view(answers or {})


def severity_for(oid, answers):
    """Public: the architecture-aware (severity, rationale) for one OWASP id.

    The STRIDE threat model reuses this so each category that maps to an OWASP
    family carries exactly the severity the security lens reports — the offense
    and the threat-model agree by construction rather than by re-derivation."""
    return _severity_for(oid, _arch_view(answers or {}))


def _bump(level):
    return _SEVERITY_LEVELS[min(_SEVERITY_LEVELS.index(level) + 1,
                                len(_SEVERITY_LEVELS) - 1)]


def _severity_for(oid, arch):
    """Return (severity, rationale) for one OWASP item from the arch view."""
    if oid in _INJECTION_FAMILY:
        if arch["auth"] == "none":
            return "Critical", ("no authentication — any anonymous user can drive "
                                "the model (arch_auth_strength=none).")
        if arch["api_write"]:
            return "Critical", ("the model has write access to backend data, so a "
                                "successful injection can change data "
                                "(arch_api_write=yes).")
        if arch["acl"] == "llm-prompt" and arch["scope"] == "all-users":
            return "Critical", ("the LLM/prompt is the only access-control boundary "
                                "over all users' data (arch_access_control_layer="
                                "llm-prompt, arch_data_scope=all-users).")
        if arch["acl"] == "none":
            return "High", "no real access control around the model (arch_access_control_layer=none)."
        if arch["rag_mod"]:
            return "High", ("retrieval runs over a user-modifiable knowledge base, "
                            "enabling indirect injection (arch_rag_modifiable=yes).")
        if arch["scope"] == "all-users":
            return "High", ("broad (all-users) data scope widens the disclosure "
                            "blast radius (arch_data_scope=all-users).")
        if (arch["scope"] == "own-user" and not arch["api_write"]
                and arch["auth"] == "strong-sso"):
            return "Medium", ("defence-in-depth: own-user data only, read-only, "
                              "behind strong SSO (arch_data_scope=own-user, "
                              "arch_api_write=no, arch_auth_strength=strong-sso).")
        return "High", ("security-architecture context is incomplete; assuming no "
                        "compensating controls (conservative default — complete "
                        "section 9 to refine).")
    if oid in _TAMPERING_FAMILY:
        if arch["api_write"] and arch["downstream"]:
            level, why = "Critical", ("write access AND unreviewed downstream "
                                      "actions (arch_api_write=yes, "
                                      "arch_downstream_actions=yes).")
        elif arch["api_write"] or arch["downstream"]:
            level, why = "High", "write access or unreviewed downstream actions is present."
        else:
            level, why = "Low", ("read-only and no unreviewed downstream actions "
                                 "→ integrity risk re-rated to Low.")
        if arch["identity"] == "shared-service-account" and arch["acl"] != "api-backend":
            level = _bump(level)
            why += (" Elevated: a shared service account without API-layer RBAC "
                    "lets every user inherit its reach "
                    "(arch_identity_model=shared-service-account).")
        return level, why
    if oid == "LLM10":
        if not arch["rate_limits"]:
            return "High", ("no rate limits / quotas / cost caps "
                            "(arch_rate_limits=no) — exposed to resource exhaustion.")
        return "Medium", "rate limits / quotas are in place (arch_rate_limits=yes)."
    if oid == "LLM04":
        if arch["rag_mod"]:
            return "High", "a user-modifiable RAG corpus can be poisoned (arch_rag_modifiable=yes)."
        return "Medium", "default integrity risk for third-party/external data."
    # LLM03 (supply chain), LLM09 (misinformation): baseline.
    return "Medium", "baseline risk; not strongly amplified by the stated architecture."


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
        "LLM05": (outputs_to_systems or agentic,
                  "output reaches downstream systems (or tools/actions) without review"),
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

    arch = _arch_view(answers)

    risks = []
    for oid, (applies, reason) in rules.items():
        if not applies:
            continue
        info = sec.OWASP_LLM_TOP10[oid]
        severity, severity_rationale = _severity_for(oid, arch)
        risks.append({
            "id": info["id"],
            "name": info["name"],
            "why": reason,
            "summary": info["summary"],
            "severity": severity,
            "severity_rationale": severity_rationale,
            "atlas": [{"id": tid, "name": tname} for tid, tname in info["atlas"]],
            "atlas_note": info.get("atlas_note"),
            "ai_act_refs": list(info["ai_act_refs"]),
            "nist_refs": list(info["nist_refs"]),
            "mitigation": info["mitigation"],
        })

    # Sort by descending severity so the report leads with the worst.
    risks.sort(key=lambda r: SEVERITY_ORDER.get(r["severity"], 0), reverse=True)
    max_severity = (max((r["severity"] for r in risks),
                        key=lambda s: SEVERITY_ORDER.get(s, 0)) if risks else None)

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
            "mapped to MITRE ATLAS and EU AI Act Art. 15. "
            f"Highest architecture-aware severity: **{max_severity}**."
        )
        if not arch["provided"]:
            summary += (" Complete the security-architecture section (9) for "
                        "architecture-aware severities; current ratings use "
                        "conservative defaults.")

    return {
        "risks": risks,
        "summary": summary,
        "max_severity": max_severity,
        "arch_provided": arch["provided"],
        "answered": answered,
        "provenance": sec.PROVENANCE,
        "disclaimer": sec.DISCLAIMER,
    }
