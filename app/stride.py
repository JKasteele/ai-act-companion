"""STRIDE threat-model lens.

Pure function `generate_stride_model(answers) -> dict`. Renders the system across
the six STRIDE categories, driven by the security-architecture fields (section 9)
and the *same* architecture-aware severity engine as the OWASP LLM Top 10 lens
(`security.py`). Four categories (Tampering, Information disclosure, Denial of
service, Elevation of privilege) reuse `security.severity_for` for the OWASP
family they map to, so the STRIDE view and the security lens agree by
construction. Two categories have no faithful single-OWASP proxy and are scored
directly from one structured field: Spoofing from `arch_auth_strength`,
Repudiation from `arch_logging`.

Deterministic and AI-free. Severity reads only the structured arch_* fields
(never narrative/free-text), so crafted text cannot move a severity — the same
injection invariant as the security lens (asserted in the tests).
"""

from .knowledge import stride as st
from .security import SEVERITY_ORDER, arch_view, severity_for


def _truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "ja", "on", "1"}
    return bool(value)


def _spoofing_severity(arch):
    auth = arch["auth"]
    if auth == "none":
        return "Critical", ("no authentication — any actor is unauthenticated "
                            "(arch_auth_strength=none).")
    if auth == "weak":
        return "High", ("weak/shared credentials are spoofable "
                        "(arch_auth_strength=weak).")
    if auth == "strong-sso":
        return "Low", ("strong SSO/MFA makes impersonation hard "
                       "(arch_auth_strength=strong-sso).")
    return "Medium", ("authentication strength not specified — conservative "
                      "default (complete section 9 to refine).")


def _repudiation_severity(arch):
    if arch["logging"]:
        return "Low", ("interactions are logged with user identity and bounded "
                       "retention (arch_logging=yes).")
    return "High", ("interactions are not attributably logged with bounded "
                    "retention (arch_logging=no) — actions can be repudiated.")


def _field_answer(answers, field):
    """Render an arch_* field value as a friendly 'Answer (from intake)' cell."""
    raw = answers.get(field)
    if raw is None or raw == "":
        return "not specified"
    if field in st.FIELD_LABELS:
        key = raw.strip().lower() if isinstance(raw, str) else raw
        return st.FIELD_LABELS[field].get(key, str(raw))
    # booleans
    return "Yes" if _truthy(raw) else "No"


def generate_stride_model(answers):
    """Return the STRIDE threat model for the given answers (six categories)."""
    answers = answers or {}
    arch = arch_view(answers)

    categories = []
    for cat in st.STRIDE:
        if cat["code"] == "S":
            severity, rationale = _spoofing_severity(arch)
        elif cat["code"] == "R":
            severity, rationale = _repudiation_severity(arch)
        else:
            severity, rationale = severity_for(cat["owasp"], answers)
        categories.append({
            "code": cat["code"],
            "name": cat["name"],
            "summary": cat["summary"],
            "questions": list(cat["questions"]),
            "fields": [{
                "id": f,
                "question": st.FIELD_QUESTIONS.get(f, f),
                "answer": _field_answer(answers, f),
            } for f in cat["arch"]],
            "owasp": cat["owasp"],
            "ai_act_refs": list(cat["ai_act_refs"]),
            "severity": severity,
            "severity_rationale": rationale,
        })

    max_severity = (max((c["severity"] for c in categories),
                        key=lambda s: SEVERITY_ORDER.get(s, 0))
                    if categories else None)

    summary = (
        "STRIDE threat model across the six categories, with the architecture-"
        f"aware severity from the AI security lens. Highest severity: "
        f"**{max_severity}**."
    )
    if not arch["provided"]:
        summary += (" Complete the security-architecture section (9) for "
                    "architecture-aware severities; current ratings use "
                    "conservative defaults.")

    return {
        "categories": categories,
        "count": len(categories),
        "max_severity": max_severity,
        "arch_provided": arch["provided"],
        "summary": summary,
        "provenance": st.PROVENANCE,
        "disclaimer": st.DISCLAIMER,
    }
