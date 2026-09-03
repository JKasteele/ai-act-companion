"""Governance register: policy metadata, review cadence, exceptions, AI literacy
and intake completeness — the "is this system's governance actually being
maintained?" view that the portfolio and the register CSV draw on.

Pure functions, no I/O. Reads only the structured `gov_*` fields plus what the
other lenses already computed. Dates are ISO strings (YYYY-MM-DD); a date that
does not parse is treated as unknown, never as a pass.

Register columns follow the fields public algorithm registers ask for (the
Dutch Algoritmeregister: name, purpose, legal basis, human oversight, contact,
status), so an export can be handed to a register owner without re-typing.
"""

from datetime import date, datetime

from ._normalize import as_list, select_field, truthy
from .knowledge import eu_ai_act as eu

# Review cadence per risk tier, in months. Companion-derived good practice: the
# AI Act sets no fixed interval, but Art. 9(2) ("continuous iterative process")
# and Art. 72 imply a periodic review; supervisors (DNB, Jan 2026) flag missing
# post-deployment review as the common gap.
REVIEW_CADENCE_MONTHS = {
    eu.TIER_PROHIBITED: 0,
    eu.TIER_HIGH: 6,
    eu.TIER_LIMITED: 12,
    eu.TIER_MINIMAL: 24,
}

STATUS_LABELS = {
    "proposed": "Proposed", "approved": "Approved", "in_review": "In review",
    "exception": "Running under exception", "retired": "Retired",
}

# Columns of the AI-register export. (key, header)
REGISTER_COLUMNS = [
    ("id", "id"), ("sys_name", "name"), ("sys_description", "description"),
    ("intended_purpose", "purpose"), ("org_sector", "sector"), ("provider_role", "role"),
    ("tier", "risk_tier"), ("annex_iii", "annex_iii_area"), ("applies_from", "obligations_from"),
    ("legal_basis", "legal_basis"), ("personal_data", "personal_data"),
    ("automated_decision", "automated_decision"), ("human_oversight", "human_oversight"),
    ("autonomy_level", "autonomy_level"), ("sys_owner", "system_owner"),
    ("data_owner", "data_owner"), ("contact", "contact"), ("status", "governance_status"),
    ("approved_on", "approved_on"), ("approval_body", "approval_body"),
    ("next_review", "next_review"), ("review_overdue", "review_overdue"),
    ("public_register", "in_public_register"), ("dpia_ref", "dpia_reference"),
    ("forensic_band", "forensic_readiness"), ("completeness", "intake_completeness"),
    ("created_at", "created_at"),
]

# Which intake sections count towards "documentation complete". Section id ->
# the minimum share of its questions that must be answered.
_COMPLETENESS_SECTIONS = {
    "identification": 0.8, "prohibited": 1.0, "high_risk": 0.3, "transparency": 1.0,
    "data": 0.6, "autonomy": 0.6, "security": 0.5,
    "datagov": 0.5, "forensics": 0.5, "governance": 0.6,
}
# architecture, gpai and incident are situational and do not count towards "complete".


def parse_date(value):
    """ISO date string -> date, else None."""
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _add_months(d, months):
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return date(y, m, day)


def completeness(answers, questionnaire=None):
    """Share of answered questions per section and an overall flag.

    A question counts as answered when it has a non-empty value; boolean
    questions are left out of the count (see below), so the share reflects the
    text, select, multiselect and table fields that carry documentation."""
    from .questionnaire import QUESTIONNAIRE  # local import: avoid cycles at import time
    q = questionnaire or QUESTIONNAIRE
    answers = answers or {}
    per = {}
    complete = True
    for sec in q["sections"]:
        qs = sec["questions"]
        if not qs:
            continue
        # Booleans are excluded from the count: the engine treats an absent
        # boolean as "no" (the form always submits them, the CLI/MCP may leave
        # them out), so absence is a valid answer, not a gap. A section made of
        # booleans only (prohibited, transparency, incident) is always complete.
        counted = [item for item in qs if item.get("type") != "boolean"]
        if not counted:
            per[sec["id"]] = 1.0
            continue
        answered = 0
        for item in counted:
            v = answers.get(item["id"])
            if v is None or v == "" or v == [] or v == {}:
                continue
            answered += 1
        share = round(answered / len(counted), 2)
        per[sec["id"]] = share
        need = _COMPLETENESS_SECTIONS.get(sec["id"])
        if need is not None and share < need:
            complete = False
    return {"per_section": per, "complete": complete,
            "overall": round(sum(per.values()) / len(per), 2) if per else 0.0}


def exceptions(answers, today=None):
    """Normalised exception rows with an 'expired' flag."""
    today = today or date.today()
    rows = []
    for raw in as_list((answers or {}).get("gov_exceptions")):
        if not isinstance(raw, dict):
            continue
        exp = parse_date(raw.get("expires"))
        rows.append({
            "exception": str(raw.get("exception") or "").strip(),
            "decision": str(raw.get("decision") or "").strip(),
            "decided_by": str(raw.get("decided_by") or "").strip(),
            "expires": exp.isoformat() if exp else str(raw.get("expires") or "").strip(),
            "expired": bool(exp and exp < today),
            "open_ended": exp is None,
        })
    return [r for r in rows if r["exception"] or r["decision"]]


def literacy(answers):
    """AI-literacy record rows (Art. 4): role, training, date."""
    rows = []
    for raw in as_list((answers or {}).get("gov_literacy")):
        if not isinstance(raw, dict):
            continue
        row = {k: str(raw.get(k) or "").strip() for k in ("role", "training", "date")}
        if row["role"] or row["training"]:
            rows.append(row)
    return rows


def governance_status(answers, classification=None, today=None):
    """Policy metadata + derived review state for one system."""
    answers = answers or {}
    cls = classification or {}
    tier = cls.get("tier", eu.TIER_MINIMAL)
    today = today or date.today()
    cadence = REVIEW_CADENCE_MONTHS.get(tier, 24)

    approved = parse_date(answers.get("gov_approved_on"))
    explicit_next = parse_date(answers.get("gov_next_review"))
    if explicit_next:
        next_review = explicit_next
        next_source = "recorded"
    elif approved and cadence:
        next_review = _add_months(approved, cadence)
        next_source = f"approved_on + {cadence} months ({tier} tier cadence)"
    else:
        next_review = None
        next_source = "unknown"
    overdue = bool(next_review and next_review < today)

    status = select_field(answers, "gov_status") or "proposed"
    exc = exceptions(answers, today)
    lit = literacy(answers)
    comp = completeness(answers)

    gaps = []
    hi = "high" if tier == eu.TIER_HIGH else "medium"
    if status in ("proposed", "") and tier in (eu.TIER_HIGH, eu.TIER_LIMITED):
        gaps.append((hi, "System in use without an approved governance decision.",
                     "Take the classification and the risk assessment through the approval "
                     "body and record the decision date.", "Art. 17(1)(m); ISO 42001 A.2.2"))
    if not str(answers.get("gov_policy_owner") or "").strip():
        gaps.append(("medium", "No policy owner recorded.",
                     "Name the role accountable for this system's governance record.",
                     "ISO 42001 A.3.2"))
    if next_review is None:
        gaps.append(("medium", "No review date and no approval date to derive one from.",
                     f"Record the approval date; the {tier} tier cadence is every "
                     f"{cadence} months.", "Art. 9(2), Art. 72"))
    elif overdue:
        gaps.append((hi, f"Review overdue since {next_review.isoformat()}.",
                     "Re-run the classification and the risk assessment; record the new "
                     "review date.", "Art. 9(2), Art. 72; DNB sector letter Jan 2026"))
    for e in exc:
        if e["expired"]:
            gaps.append((hi, f"Exception expired: {e['exception'] or e['decision']}.",
                         "Renew with a new decision and end date, or close the exception.",
                         "ISO 42001 A.2.4"))
        elif e["open_ended"]:
            gaps.append(("medium", f"Open-ended exception: {e['exception'] or e['decision']}.",
                         "Give every exception an end date.", "ISO 42001 A.2.4"))
    if not lit:
        gaps.append(("medium", "No AI-literacy record.",
                     "Record which roles received which training and when (Art. 4 is in "
                     "force since 2 Feb 2025; supervision since 2 Aug 2026).",
                     "Art. 4"))
    if not comp["complete"]:
        weak = [s for s, share in comp["per_section"].items()
                if s in _COMPLETENESS_SECTIONS and share < _COMPLETENESS_SECTIONS[s]]
        gaps.append(("low", "Intake incomplete: " + ", ".join(weak) + ".",
                     "Complete those sections so the generated documentation stops "
                     "carrying placeholders.", "Art. 11, Art. 17(1)(k)"))
    if truthy(answers.get("data_personal")) and not str(answers.get("gov_dpia_ref") or "").strip():
        gaps.append(("low", "No DPIA reference recorded.",
                     "Link the DPIA (or the documented decision that none is needed).",
                     "GDPR Art. 35; AI Act Art. 26(9)"))
    order = {"high": 0, "medium": 1, "low": 2}
    gaps.sort(key=lambda g: order[g[0]])

    return {
        "tier": tier,
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "policy_owner": str(answers.get("gov_policy_owner") or "").strip(),
        "approval_body": str(answers.get("gov_approval_body") or "").strip(),
        "approved_on": approved.isoformat() if approved else "",
        "cadence_months": cadence,
        "next_review": next_review.isoformat() if next_review else "",
        "next_review_source": next_source,
        "review_overdue": overdue,
        "exceptions": exc,
        "literacy": lit,
        "completeness": comp,
        "public_register": truthy(answers.get("gov_public_register")),
        "contact": str(answers.get("gov_register_contact") or "").strip(),
        "dpia_ref": str(answers.get("gov_dpia_ref") or "").strip(),
        "gaps": [{"severity": s, "gap": g, "action": a, "ref": r} for s, g, a, r in gaps],
    }


def register_row(full, forensic_band="", today=None):
    """One AI-register row (dict keyed by REGISTER_COLUMNS keys) for a stored
    assessment dict {id, answers, classification, created_at}."""
    answers = full.get("answers") or {}
    cls = full.get("classification") or {}
    gov = governance_status(answers, cls, today)
    findings = cls.get("findings") or []
    annex = ", ".join(sorted({r for f in findings for r in f.get("refs", [])
                              if str(r).startswith("Annex III")}))
    legal = ", ".join(sorted({str(r.get("legal_basis") or "") for r in
                              as_list(answers.get("dg_datasets")) if isinstance(r, dict)
                              and r.get("legal_basis")}))
    return {
        "id": full.get("id", ""),
        "sys_name": answers.get("sys_name", ""),
        "sys_description": answers.get("sys_description", ""),
        "intended_purpose": answers.get("intended_purpose", ""),
        "org_sector": answers.get("org_sector", ""),
        "provider_role": answers.get("provider_role", ""),
        "tier": cls.get("tier", ""),
        "annex_iii": annex,
        "applies_from": (cls.get("applicability") or {}).get("date", ""),
        "legal_basis": legal,
        "personal_data": "yes" if truthy(answers.get("data_personal")) else "no",
        "automated_decision": "yes" if truthy(answers.get("automated_decision")) else "no",
        "human_oversight": answers.get("human_oversight", ""),
        "autonomy_level": answers.get("autonomy_level", ""),
        "sys_owner": answers.get("sys_owner", ""),
        "data_owner": answers.get("dg_data_owner", ""),
        "contact": gov["contact"],
        "status": gov["status_label"],
        "approved_on": gov["approved_on"],
        "approval_body": gov["approval_body"],
        "next_review": gov["next_review"],
        "review_overdue": "yes" if gov["review_overdue"] else "no",
        "public_register": "yes" if gov["public_register"] else "no",
        "dpia_ref": gov["dpia_ref"],
        "forensic_band": forensic_band,
        "completeness": f"{int(gov['completeness']['overall'] * 100)}%",
        "created_at": full.get("created_at", ""),
    }
