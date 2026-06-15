"""Defensive control-catalogue generator.

Pure function `generate_control_catalog(answers) -> dict`. The blue-team mirror of
the red-team test plan: it turns the architecture-aware AI security lens
(`security.assess_security`) into a prioritised, system-specific catalogue of
**controls to implement**, each cross-linked to the red-team test case(s) that
would verify it.

It introduces no new judgement, exactly like `redteam.generate_test_plan`:

  * **Priority = lens severity.** A control's priority is the architecture-aware
    severity of the parent OWASP risk it mitigates — the same number the test
    plan uses — so the catalogue is specific to the architecture rather than a
    generic hardening checklist.
  * **Same gates as the offense.** Conditional controls are gated on the
    architecture through the *same* `redteam.architecture_flags`/`gate_open`
    evaluation the test plan uses, so a control and the test that verifies it
    appear together (e.g. "enforce authorization at the API layer" and the
    cross-tenant test both appear only when the model reaches all-users data).
  * **Injection-proof.** Selection reads only the structured `sec_*`/`arch_*`
    fields (via the lens and the shared flags); free-text cannot add, drop or
    re-prioritise a control (asserted in the tests).

Framework anchors (NIST CSF 2.0 function, ISO/IEC 27001:2022 control titles) come
from the control template; the EU AI Act / NIST AI RMF references and the
mitigation summary come from the parent OWASP item — single source of truth.
"""

from .knowledge import ai_security as sec
from .knowledge import controls as ctl
from .knowledge import red_team as rt
from .knowledge import security_frameworks as sfw
from .redteam import architecture_flags, gate_open
from .security import SEVERITY_ORDER, assess_security

_CSF_NAME = {code: name for code, name, _intent, _cats in sfw.CSF_FUNCTIONS}


def _csf_cells(codes):
    """Resolve CSF function codes to '<Name> (<code>)' cells."""
    return [f"{_CSF_NAME.get(c, c)} ({c})" for c in codes]


def _iso_cells(ids):
    """Resolve ISO 27001:2022 ids to '<id> <public title>' cells."""
    return [f"{cid} {sfw.ISO_27001_TITLES.get(cid, '')}".strip() for cid in ids]


def generate_control_catalog(answers):
    """Return a prioritised, architecture-aware defensive control catalogue."""
    answers = answers or {}
    profile = assess_security(answers)
    risks = profile.get("risks", [])

    by_base = {}
    for r in risks:
        by_base[r["id"].split(":")[0]] = r
    fired_ids = set(by_base)
    flags = architecture_flags(answers, fired_ids)

    controls = []
    for base, risk in by_base.items():
        info = sec.OWASP_LLM_TOP10.get(base, {})
        for tmpl in ctl.CONTROLS.get(base, []):
            if not gate_open(tmpl["gate"], flags):
                continue
            controls.append({
                "ref": tmpl["ref"],
                "title": tmpl["title"],
                "priority": risk["severity"],
                "owasp": {"id": risk["id"], "name": risk["name"]},
                "control": tmpl["control"],
                "intent": tmpl["intent"],
                "verify": tmpl["verify"],
                "validated_by": list(tmpl["validated_by"]),
                "gate": tmpl["gate"],
                "gate_reason": rt.GATES.get(tmpl["gate"]) if tmpl["gate"] else None,
                "csf": _csf_cells(tmpl["csf"]),
                "iso": _iso_cells(tmpl["iso"]),
                "ai_act_refs": list(info.get("ai_act_refs", [])),
                "nist_refs": list(info.get("nist_refs", [])),
                "mitigation": info.get("mitigation", ""),
            })

    # Worst-first: by priority severity, then by stable control ref.
    controls.sort(key=lambda c: (-SEVERITY_ORDER.get(c["priority"], 0), c["ref"]))

    by_priority = {level: 0 for level in SEVERITY_ORDER}
    for c in controls:
        by_priority[c["priority"]] = by_priority.get(c["priority"], 0) + 1
    max_priority = (max((c["priority"] for c in controls),
                        key=lambda s: SEVERITY_ORDER.get(s, 0)) if controls else None)

    owasp_covered = sorted({c["owasp"]["id"] for c in controls})
    validated_refs = sorted({ref for c in controls for ref in c["validated_by"]})

    return {
        "controls": controls,
        "count": len(controls),
        "by_priority": by_priority,
        "max_priority": max_priority,
        "owasp_covered": owasp_covered,
        "validated_refs": validated_refs,
        "arch_provided": profile.get("arch_provided", False),
        "answered": profile.get("answered", False),
        "security_summary": profile.get("summary", ""),
        "provenance": ctl.PROVENANCE,
        "disclaimer": ctl.DISCLAIMER,
    }
