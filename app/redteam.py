"""AI red-team test-plan generator.

Pure function `generate_test_plan(answers) -> dict`. Turns the architecture-aware
AI security lens (`security.assess_security`) into a prioritised, system-specific
adversarial **test plan**: a catalogue of test cases to scope an *authorized*
purple-team exercise.

Two design properties, mirroring the rest of the toolkit:

  * **Deterministic & explainable.** Which test cases appear, and their
    priority, are a pure function of the structured intake. Priority of a test
    case = the architecture-aware *severity* of its parent OWASP risk, computed
    by the security lens — so the plan adapts to the specific architecture
    (e.g. a Critical cross-tenant test only appears when the LLM is the only
    access-control boundary over all-users data) instead of being a generic
    checklist. Each conditional test carries a one-line reason naming the gate.
  * **Injection-proof.** Selection reads only the structured sec_*/arch_* fields
    (via the lens); free-text is inert, so crafted prose cannot add, drop or
    re-prioritise a test (the red-team invariant — asserted in the tests).

This is a planning aid, not an executor: it contains no live payloads and runs
nothing. See `app/knowledge/red_team.py` for the templates and safety scope.
"""

from .knowledge import ai_security as sec
from .knowledge import red_team as rt
from .security import SEVERITY_ORDER, assess_security


def _truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "ja", "on", "1"}
    return bool(value)


def _select(answers, key):
    v = answers.get(key)
    return v.strip().lower() if isinstance(v, str) else ""


def _flags(answers, fired_ids):
    """Structured signals the gate evaluator needs. Reads only sec_*/arch_*."""
    def a(key):
        return _truthy(answers.get(key))

    rag = a("arch_rag_modifiable") or "LLM08" in fired_ids
    return {
        "external": a("sec_external_data"),
        "rag": rag,
        "indirect": a("sec_external_data") or rag,
        "agentic_or_write": (a("sec_agentic") or a("sec_outputs_to_systems")
                             or a("arch_api_write") or a("arch_downstream_actions")),
        "cross_tenant": _select(answers, "arch_data_scope") == "all-users",
        "no_rate_limits": not a("arch_rate_limits"),
        "auth": _select(answers, "arch_auth_strength"),
        "public": a("sec_public"),
    }


def _gate_open(gate, flags):
    """A template with no gate always applies (its parent risk already fired);
    a gated template applies only when its named condition holds."""
    return True if gate is None else bool(flags.get(gate))


def _access_note(flags):
    """One-line tester-access posture derived from the auth model — shapes the
    rules of engagement rather than any single test."""
    if flags["public"] and flags["auth"] in ("none", ""):
        return ("The interface is reachable by untrusted/external users with no "
                "or weak authentication, so an external attacker is in scope; "
                "test from an unauthenticated position.")
    if flags["auth"] == "none":
        return ("No authentication is required; test from an unauthenticated "
                "position.")
    if flags["auth"] == "weak":
        return ("Authentication is weak (e.g. shared/static credentials); assume "
                "a low-effort credential-holder.")
    if flags["auth"] == "strong-sso":
        return ("Strong authentication (SSO/MFA) is in place; test as a valid "
                "low-privilege account and focus on authorization boundaries.")
    return ("Authentication posture not stated; test as a low-privilege user and "
            "record the access required for each finding.")


def generate_test_plan(answers):
    """Return a prioritised, architecture-aware red-team test plan."""
    answers = answers or {}
    profile = assess_security(answers)
    risks = profile.get("risks", [])

    # base OWASP id (e.g. "LLM01") -> {severity, name, atlas, controls}
    by_base = {}
    for r in risks:
        base = r["id"].split(":")[0]
        by_base[base] = r
    fired_ids = set(by_base)
    flags = _flags(answers, fired_ids)

    cases = []
    for base, risk in by_base.items():
        info = sec.OWASP_LLM_TOP10.get(base, {})
        for tmpl in rt.TEST_CASES.get(base, []):
            if not _gate_open(tmpl["gate"], flags):
                continue
            atlas = [{"id": tid, "name": tname} for tid, tname in info.get("atlas", [])]
            cases.append({
                "ref": tmpl["ref"],
                "title": tmpl["title"],
                "priority": risk["severity"],
                "owasp": {"id": risk["id"], "name": risk["name"]},
                "atlas": atlas,
                "atlas_note": info.get("atlas_note"),
                "objective": tmpl["objective"],
                "gate": tmpl["gate"],
                "gate_reason": rt.GATES.get(tmpl["gate"]) if tmpl["gate"] else None,
                "preconditions": tmpl["preconditions"],
                "method": tmpl["method"],
                "success_criteria": tmpl["success_criteria"],
                "detection": tmpl["detection"],
                "ai_act_refs": list(info.get("ai_act_refs", [])),
                "nist_refs": list(info.get("nist_refs", [])),
                "mitigation": info.get("mitigation", ""),
            })

    # Worst-first: by priority severity, then by stable test ref.
    cases.sort(key=lambda c: (-SEVERITY_ORDER.get(c["priority"], 0), c["ref"]))

    by_priority = {level: 0 for level in SEVERITY_ORDER}
    for c in cases:
        by_priority[c["priority"]] = by_priority.get(c["priority"], 0) + 1
    max_priority = (max((c["priority"] for c in cases),
                        key=lambda s: SEVERITY_ORDER.get(s, 0)) if cases else None)

    # Coverage: every OWASP item that has a test in this plan, plus the unique
    # ATLAS techniques referenced.
    owasp_covered = sorted({c["owasp"]["id"] for c in cases})
    atlas_covered = sorted({t["id"] for c in cases for t in c["atlas"]})

    return {
        "cases": cases,
        "count": len(cases),
        "by_priority": by_priority,
        "max_priority": max_priority,
        "owasp_covered": owasp_covered,
        "atlas_covered": atlas_covered,
        "access_note": _access_note(flags),
        "arch_provided": profile.get("arch_provided", False),
        "answered": profile.get("answered", False),
        "security_summary": profile.get("summary", ""),
        "provenance": rt.PROVENANCE,
        "disclaimer": rt.DISCLAIMER,
    }
