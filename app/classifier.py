"""Rule-based EU AI Act risk classifier.

Pure function: `classify(answers) -> dict`. No I/O, no AI - fully deterministic
and testable. Every conclusion ('finding') carries the responsible article and
the question ids that triggered the rule.

Decision logic (highest severity wins):
    Art. 5   -> prohibited
    Art. 6   -> high risk (Annex I safety component or Annex III), with the
                Art. 6(3) nuance
    Art. 50  -> limited risk (transparency)
    else     -> minimal risk
GPAI obligations (Chapter V) are independent of the tier and listed separately.
"""

from .knowledge import eu_ai_act as eu
from .knowledge import nist_rmf as nist


# --- normalisation helpers -------------------------------------------------
def _truthy(value):
    """Coerce various 'yes' representations to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "ja", "on", "1"}
    return bool(value)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _finding(tier, refs, title, rationale, sources):
    return {
        "tier": tier,
        "refs": refs if isinstance(refs, list) else [refs],
        "title": title,
        "rationale": rationale,
        "source_questions": sources,
    }


# --- rules -----------------------------------------------------------------
def _check_prohibited(answers):
    findings = []
    for qid, info in eu.PROHIBITED_PRACTICES.items():
        if _truthy(answers.get(qid)):
            findings.append(_finding(
                eu.TIER_PROHIBITED,
                [info["ref"]],
                info["title"],
                f"The indicated practice falls under a prohibited AI practice "
                f"({info['ref']}): {info['summary']}",
                [qid],
            ))
    return findings


def _check_high_risk(answers):
    findings = []

    # Route 1: safety component under harmonisation legislation (Art. 6(1)).
    if _truthy(answers.get("hr_safety_component")):
        findings.append(_finding(
            eu.TIER_HIGH,
            [eu.ART_6_1["ref"]],
            eu.ART_6_1["title"],
            eu.ART_6_1["summary"],
            ["hr_safety_component"],
        ))

    # Route 2: Annex III use cases (Art. 6(2)).
    usecases = [u for u in _as_list(answers.get("hr_usecases")) if u and u != "none"]
    does_profiling = _truthy(answers.get("hr_does_profiling"))
    minor_task = _truthy(answers.get("hr_art6_3_minor"))

    for uc in usecases:
        info = eu.HIGH_RISK_USECASES.get(uc)
        if not info:
            continue
        rationale = (
            f"Use in {info['ref']} ({info['title']}): {info['summary']} "
            f"Therefore high-risk in principle on the basis of Art. 6(2)."
        )
        # Art. 6(3) nuance: only possible if there is NO profiling.
        if minor_task and not does_profiling:
            rationale += (
                " NOTE: it was indicated that this is only a narrow/preparatory "
                "task without materially influencing decision-making and "
                "without profiling. The Art. 6(3) derogation may apply - the "
                "provider must document that assessment (Art. 6(4)). Treat as "
                "high-risk until this is substantiated and recorded."
            )
            refs = [info["ref"], "Art. 6(2)", eu.ART_6_3["ref"], "Art. 6(4)"]
        elif minor_task and does_profiling:
            rationale += (
                " The Art. 6(3) derogation is NOT available HERE because the "
                "system performs profiling of natural persons."
            )
            refs = [info["ref"], "Art. 6(2)", "Art. 6(3)"]
        else:
            refs = [info["ref"], "Art. 6(2)"]
        findings.append(_finding(
            eu.TIER_HIGH, refs, f"High-risk: {info['title']}", rationale, ["hr_usecases"],
        ))
    return findings


def _check_transparency(answers):
    findings = []
    for qid, info in eu.TRANSPARENCY_OBLIGATIONS.items():
        if _truthy(answers.get(qid)):
            findings.append(_finding(
                eu.TIER_LIMITED,
                [info["ref"]],
                info["title"],
                f"Transparency obligation ({info['ref']}): {info['summary']}",
                [qid],
            ))
    return findings


def _check_gpai(answers):
    findings = []
    if _truthy(answers.get("gpai_model")):
        info = eu.GPAI["model"]
        findings.append(_finding(
            "gpai", [info["ref"]], info["title"], info["summary"], ["gpai_model"],
        ))
    if _truthy(answers.get("gpai_systemic")):
        info = eu.GPAI["systemic"]
        findings.append(_finding(
            "gpai", [info["ref"]], info["title"], info["summary"], ["gpai_systemic"],
        ))
    return findings


def _recommended_artifacts(tier, answers):
    """Which documents should you produce for this system?"""
    arts = ["AI risk assessment report"]
    if _truthy(answers.get("data_personal")):
        arts.append("DPIA (data protection impact assessment, GDPR Art. 35)")
    if tier in (eu.TIER_HIGH, eu.TIER_PROHIBITED):
        arts.append("Bias/fairness audit report (AI Act Art. 10)")
        arts.append("Technical documentation (AI Act Art. 11 + Annex IV)")
        arts.append("Fundamental rights impact assessment - FRIA (AI Act Art. 27)")
    else:
        arts.append("Bias audit checklist (good practice)")
    sec_signals = ("sec_is_llm", "sec_agentic", "sec_third_party_models",
                   "sec_public", "gpai_model")
    if tier in (eu.TIER_HIGH, eu.TIER_PROHIBITED) or any(_truthy(answers.get(k)) for k in sec_signals):
        arts.append("AI security assessment (OWASP LLM Top 10 + MITRE ATLAS)")
    return arts


# --- public API ------------------------------------------------------------
def classify(answers):
    """Classify an AI system based on the intake answers."""
    answers = answers or {}

    # Applicability check (Art. 2): out of EU scope -> no AI Act requirements.
    if not _truthy(answers.get("eu_market")):
        return {
            "tier": eu.TIER_MINIMAL,
            "tier_label": eu.TIER_LABELS[eu.TIER_MINIMAL],
            "tier_description": (
                "According to the answers, the system is not placed on the "
                "market/used in the EU and does not affect persons in the EU. "
                "The EU AI Act then appears not to apply (Art. 2). Good "
                "governance (e.g. NIST AI RMF) remains recommended."
            ),
            "summary": "Outside the territorial scope of the EU AI Act (Art. 2).",
            "findings": [],
            "transparency_obligations": [],
            "gpai_obligations": _check_gpai(answers),
            "high_risk_obligations": [],
            "nist_crosswalk": [list(s) for s in nist.crosswalk_for_tier(eu.TIER_MINIMAL)],
            "recommended_artifacts": _recommended_artifacts(eu.TIER_MINIMAL, answers),
            "applicability": {"date": "-", "what": "Outside the EU AI Act's scope (Art. 2).",
                              "basis": "Art. 2"},
            "disclaimer": eu.DISCLAIMER,
        }

    prohibited = _check_prohibited(answers)
    high = _check_high_risk(answers)
    transparency = _check_transparency(answers)
    gpai = _check_gpai(answers)

    # Determine the highest tier that is triggered.
    risk_findings = prohibited + high + transparency
    if prohibited:
        tier = eu.TIER_PROHIBITED
    elif high:
        tier = eu.TIER_HIGH
    elif transparency:
        tier = eu.TIER_LIMITED
    else:
        tier = eu.TIER_MINIMAL

    # Findings that exactly match the determining tier (for the main rationale).
    primary = [f for f in risk_findings if f["tier"] == tier]

    summary = _build_summary(tier, primary, transparency, gpai)

    high_risk_obligations = (
        [list(o) for o in eu.HIGH_RISK_OBLIGATIONS] if tier == eu.TIER_HIGH else []
    )

    return {
        "tier": tier,
        "tier_label": eu.TIER_LABELS[tier],
        "tier_description": eu.TIER_DESCRIPTIONS[tier],
        "summary": summary,
        "findings": primary,
        # Always show transparency separately: a high-risk system can, on top of
        # the high-risk obligations, also fall under Art. 50.
        "transparency_obligations": transparency,
        "gpai_obligations": gpai,
        "high_risk_obligations": high_risk_obligations,
        "nist_crosswalk": [list(s) for s in nist.crosswalk_for_tier(tier)],
        "recommended_artifacts": _recommended_artifacts(tier, answers),
        "applicability": eu.applies_from(tier, answers),
        "disclaimer": eu.DISCLAIMER,
    }


def _build_summary(tier, primary, transparency, gpai):
    if tier == eu.TIER_PROHIBITED:
        s = ("The system falls under one or more prohibited practices (Art. 5) "
             "and may in principle not be offered or used in the EU.")
    elif tier == eu.TIER_HIGH:
        s = ("The system is high-risk (Art. 6). The full set of high-risk "
             "obligations applies.")
    elif tier == eu.TIER_LIMITED:
        s = ("The system is subject to transparency obligations (Art. 50); no "
             "high-risk requirements based on the answers.")
    else:
        s = ("No prohibited, high-risk or transparency triggers found. Minimal "
             "risk - voluntary codes of conduct recommended (Art. 95).")
    if tier != eu.TIER_LIMITED and transparency:
        s += " In addition, transparency obligations apply (Art. 50)."
    if gpai:
        s += " GPAI obligations apply on top of this (Chapter V)."
    return s
