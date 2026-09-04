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

from ._normalize import as_list as _as_list
from ._normalize import select_field as _select
from ._normalize import truthy as _truthy
from .knowledge import eu_ai_act as eu
from .knowledge import nist_rmf as nist


# --- normalisation helpers -------------------------------------------------
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

    role = (_select(answers, "provider_role") or "").lower()
    provider_gateway = (
        _truthy(answers.get("p_sexual_provider_intended"))
        or _truthy(answers.get("p_sexual_provider_foreseeable_unguarded"))
    )
    deployer_gateway = _truthy(answers.get("p_sexual_deployer_purpose"))
    if role == "provider":
        actor_gateway = provider_gateway
    elif role == "deployer":
        actor_gateway = deployer_gateway
    else:
        # "both" and unknown roles may trigger through either regulated act.
        actor_gateway = provider_gateway or deployer_gateway

    if actor_gateway:
        gateway_refs = []
        gateway_sources = []
        if provider_gateway and role != "deployer":
            gateway_refs.append("Art. 5(1a)(a)")
            if _truthy(answers.get("p_sexual_provider_intended")):
                gateway_sources.append("p_sexual_provider_intended")
            if _truthy(answers.get("p_sexual_provider_foreseeable_unguarded")):
                gateway_sources.append("p_sexual_provider_foreseeable_unguarded")
        if deployer_gateway and role != "provider":
            gateway_refs.append("Art. 5(1a)(b)")
            gateway_sources.append("p_sexual_deployer_purpose")
        for qid, info in eu.CONDITIONAL_PROHIBITED_PRACTICES.items():
            if _truthy(answers.get(qid)):
                findings.append(_finding(
                    eu.TIER_PROHIBITED,
                    [info["ref"], *gateway_refs],
                    info["title"],
                    f"The content condition in {info['ref']} is indicated and the "
                    f"applicable actor gateway in Art. 5(1a) is met: {info['summary']}",
                    [qid, *gateway_sources],
                ))
    return findings


def _check_high_risk(answers):
    findings = []

    # Route 1: Annex I regulated-product route (Art. 6(1)), narrowed by the
    # Art. 6(1a)-(1c) filters inserted in 2026.  The former one-question flag is
    # honoured only for saved assessments that contain none of the new fields.
    relation = _select(answers, "hr_annex_i_relation")
    has_details = any(key in answers for key in (
        "hr_annex_i_relation", "hr_safety_function",
        "hr_failure_endangers_health_safety", "hr_third_party_health_safety",
    ))
    if eu.annex_i_high_risk_trigger(answers):
        legacy_trigger = not has_details
        sources = ["hr_safety_component"] if legacy_trigger else [
            "hr_annex_i_relation", "hr_third_party_health_safety",
        ]
        if _select(answers, "hr_annex_i_section"):
            sources.append("hr_annex_i_section")
        if relation == "embedded_component":
            sources.extend(["hr_safety_function", "hr_failure_endangers_health_safety"])
        rationale = eu.ART_6_1["summary"]
        if str(_select(answers, "hr_annex_i_section") or "").upper() == "B":
            rationale += (
                " Because the product legislation is in Annex I Section B, amended "
                "Art. 2(2) limits this Regulation to Art. 6(1), Art. 60a and Arts. "
                "102–112; Arts. 57–59 apply only insofar as the product legislation "
                "integrates the relevant requirements."
            )
        elif str(_select(answers, "hr_annex_i_section") or "").upper() == "A":
            rationale += (
                " For Section A product legislation, Art. 2(13) permits future "
                "delegated acts to limit specified Arts. 9–15 and 17–25 duties where "
                "equivalent or higher product-law protection exists. No limitation "
                "should be assumed without checking the applicable delegated act."
            )
        findings.append(_finding(
            eu.TIER_HIGH,
            [eu.ART_6_1["ref"]] + (["Art. 2(2)"] if str(
                _select(answers, "hr_annex_i_section") or "").upper() == "B" else []),
            eu.ART_6_1["title"],
            rationale,
            sources,
        ))

    # Route 2: Annex III use cases (Art. 6(2)).
    usecases = [u for u in _as_list(answers.get("hr_usecases")) if u and u != "none"]
    does_profiling = _truthy(answers.get("hr_does_profiling"))
    minor_task = _truthy(answers.get("hr_art6_3_minor"))

    for uc in usecases:
        info = eu.HIGH_RISK_USECASES.get(uc)
        if not info:
            continue
        sources = ["hr_usecases", f"hr_usecases={uc}"]
        extra_refs = []
        # Annex III(5) is four different cases; narrow to the sub-point when
        # given, because 5(b)/(c) carry a FRIA duty for every deployer.
        sub = eu.ANNEX_III_5_SUBAREAS.get(_select(answers, "hr_essential_subarea")) \
            if uc == "essential_services" else None
        if sub:
            info = sub
            sources.append("hr_essential_subarea")
        rationale = (
            f"Use in {info['ref']} ({info['title']}): {info['summary']} "
            f"Therefore high-risk in principle on the basis of Art. 6(2)."
        )
        if sub and sub.get("fria_all_deployers"):
            rationale += (
                f" A deployer of a {info['ref']} system must carry out a "
                "fundamental rights impact assessment before first use, whether "
                "public or private (Art. 27(1))."
            )
            extra_refs.append("Art. 27(1)")
        scope_note = eu.INSURANCE_SCOPE_NOTES.get(_select(answers, "hr_insurance_scope")) \
            if sub and sub["ref"] == "Annex III(5)(c)" else None
        if scope_note:
            rationale += " Sector context: " + scope_note
            sources.append("hr_insurance_scope")
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
        elif does_profiling:
            rationale += (
                " Note: the Art. 6(3) derogation is NEVER available here because "
                "the system performs profiling of natural persons - an Annex III "
                "system that profiles is always high-risk (Art. 6(3) final "
                "subparagraph)."
            )
            refs = [info["ref"], "Art. 6(2)", "Art. 6(3)"]
        else:
            refs = [info["ref"], "Art. 6(2)"]
        findings.append(_finding(
            eu.TIER_HIGH, refs + extra_refs, f"High-risk: {info['title']}", rationale,
            sources,
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
    # gpai_model means the assessed organisation provides the model itself.
    # Merely integrating an upstream GPAI model (gpai_integrated) does not move
    # that upstream provider's Chapter V obligations to the integrator.
    if _truthy(answers.get("gpai_model")):
        info = eu.GPAI["model"]
        findings.append(_finding(
            "gpai", [info["ref"]], info["title"], info["summary"], ["gpai_model"],
        ))
        # Art. 53(2) open-source carve-out — only when there is no systemic risk.
        if _truthy(answers.get("gpai_open_source")) and not _truthy(answers.get("gpai_systemic")):
            info = eu.GPAI["open_source"]
            findings.append(_finding(
                "gpai", [info["ref"]], info["title"], info["summary"],
                ["gpai_open_source"],
            ))
    if _truthy(answers.get("gpai_model")) and _truthy(answers.get("gpai_systemic")):
        info = eu.GPAI["systemic"]
        findings.append(_finding(
            "gpai", [info["ref"]], info["title"], info["summary"], ["gpai_systemic"],
        ))
    return findings


def _recommended_artifacts(tier, answers, in_scope=True):
    """Which documents should you produce for this system?"""
    arts = ["AI risk assessment report"]
    # Art. 4 applies to in-scope providers and deployers. It requires support
    # measures, not a guaranteed individual literacy level or a prescribed
    # training record; the record below is practical evidence of those measures.
    section_b_only = eu.annex_i_section_b_only(answers)
    role = (_select(answers, "provider_role") or "").lower()
    if eu.art4_applies(answers, in_scope=in_scope):
        arts.append("AI literacy support-measures plan and evidence record (AI Act Art. 4)")
    elif in_scope and not section_b_only:
        arts.append("AI literacy actor-scope check (AI Act Art. 4: providers/deployers)")
    if _truthy(answers.get("data_personal")):
        arts.append("DPIA (data protection impact assessment, GDPR Art. 35)")
    if tier == eu.TIER_HIGH and section_b_only:
        arts.append("Annex I Section B applicability record (AI Act Art. 2(2))")
    elif tier == eu.TIER_HIGH:
        if role != "deployer":
            arts.append("Data governance & quality record (AI Act Art. 10)")
            arts.append("Bias/fairness audit report (AI Act Art. 10)")
            arts.append("Technical documentation (AI Act Art. 11 + Annex IV)")
        if role != "provider":
            arts.append("Deployer input-data and use record (AI Act Art. 26)")
            arts.append("Fundamental rights impact assessment - FRIA, where applicable "
                        "(AI Act Art. 27)")
        if _truthy(answers.get("data_special_category")):
            arts.append("Special-category bias-processing necessity & safeguards record "
                        "(AI Act Art. 4a; only if that exceptional basis is used)")
    elif tier == eu.TIER_PROHIBITED:
        arts.append("Prohibition decision and withdrawal/remediation record (AI Act Art. 5)")
    else:
        if _truthy(answers.get("data_personal")):
            arts.append("Data governance & quality record (good practice; GDPR Art. 5(1)(d))")
        arts.append("Bias audit checklist (good practice)")
    sec_signals = ("sec_is_llm", "sec_agentic", "sec_third_party_models",
                   "sec_public", "gpai_model", "gpai_integrated")
    if tier in (eu.TIER_HIGH, eu.TIER_PROHIBITED) or any(_truthy(answers.get(k)) for k in sec_signals):
        arts.append("AI security assessment (OWASP LLM Top 10 + MITRE ATLAS)")
    return arts


# --- public API ------------------------------------------------------------
def _out_of_scope(answers, ref, summary, description, sources=None):
    """Build the classification result for a system outside the AI Act's scope
    (Art. 2). Chapter V (GPAI) is part of the same scope, so no GPAI
    obligations are emitted here."""
    return {
        "tier": eu.TIER_MINIMAL,
        "tier_label": eu.TIER_LABELS[eu.TIER_MINIMAL],
        "tier_description": description,
        "summary": summary,
        "findings": [],
        "transparency_obligations": [],
        "gpai_obligations": [],
        "high_risk_obligations": [],
        "nist_crosswalk": [list(s) for s in nist.crosswalk_for_tier(eu.TIER_MINIMAL)],
        "recommended_artifacts": _recommended_artifacts(eu.TIER_MINIMAL, answers, in_scope=False),
        "applicability": {"date": "-", "what": summary, "basis": ref},
        "out_of_scope": {"ref": ref, "source_questions": sources or []},
        "disclaimer": eu.DISCLAIMER,
    }


def classify(answers):
    """Classify an AI system based on the intake answers."""
    answers = answers or {}

    # Applicability check (Art. 2): out of EU scope -> no AI Act requirements.
    if not _truthy(answers.get("eu_market")):
        return _out_of_scope(
            answers, "Art. 2",
            "Outside the territorial scope of the EU AI Act (Art. 2).",
            "According to the answers, none of the recorded Art. 2(1) actor or "
            "territorial routes applies: Union market placement/putting into "
            "service, an EU-established/located deployer, third-country actors "
            "whose system output is used in the Union, or a covered importer, "
            "distributor or product manufacturer. The EU AI Act then appears not "
            "to apply. Good "
            "governance (e.g. NIST AI RMF) remains recommended.",
            sources=["eu_market"],
        )

    # Subject-matter exemptions (Art. 2(3)/(6)/(8)/(10)): also out of scope.
    for qid, info in eu.SCOPE_EXEMPTIONS.items():
        if _truthy(answers.get(qid)):
            return _out_of_scope(
                answers, info["ref"],
                f"Out of scope: {info['title']} ({info['ref']}).",
                f"{info['summary']} The EU AI Act therefore appears not to apply "
                f"here (exemption under {info['ref']}). Good governance (e.g. "
                "NIST AI RMF) remains recommended.",
                sources=[qid],
            )

    high = _check_high_risk(answers)
    section_b_only = eu.annex_i_section_b_only(answers)
    # Amended Art. 2(2) is an exclusive scope rule for an Art. 6(1) system tied
    # only to Annex I Section B product law. Art. 5 and Art. 50 must therefore
    # not leak back in through generic questionnaire flags for that legal object.
    prohibited = [] if section_b_only else _check_prohibited(answers)
    transparency = [] if section_b_only else _check_transparency(answers)
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

    summary = _build_summary(tier, primary, transparency, gpai, answers)

    high_risk_obligations = (
        [list(o) for o in eu.high_risk_obligations_for_role(
            answers.get("provider_role"), answers
        )]
        if tier == eu.TIER_HIGH and not eu.annex_i_section_b_only(answers) else []
    )
    applicability = eu.applies_from(tier, answers)
    if tier == eu.TIER_PROHIBITED and applicability["date"] == eu.NEW_ART_5_APPLICATION_DATE:
        tier_description = (
            "The answers match a prohibited-practice rule introduced by Regulation "
            "(EU) 2026/1744. It applies from 2 Dec 2026; remediation and separate "
            "legal review are required before relying on continued EU deployment."
        )
    elif section_b_only:
        tier_description = (
            "Classified under Art. 6(1), with the limited Annex I Section B regime "
            "in Art. 2(2); the ordinary Chapter III high-risk compliance pack does "
            "not apply through this route."
        )
    else:
        tier_description = eu.TIER_DESCRIPTIONS[tier]

    return {
        "tier": tier,
        "tier_label": eu.TIER_LABELS[tier],
        "tier_description": tier_description,
        "summary": summary,
        "findings": primary,
        # Always show transparency separately: a high-risk system can, on top of
        # the high-risk obligations, also fall under Art. 50.
        "transparency_obligations": transparency,
        "gpai_obligations": gpai,
        "high_risk_obligations": high_risk_obligations,
        "nist_crosswalk": [list(s) for s in nist.crosswalk_for_tier(tier)],
        "recommended_artifacts": _recommended_artifacts(tier, answers),
        "applicability": applicability,
        "disclaimer": eu.DISCLAIMER,
    }


def _build_summary(tier, primary, transparency, gpai, answers):
    if tier == eu.TIER_PROHIBITED:
        refs = {ref for finding in primary for ref in finding.get("refs", [])}
        future_only = bool(refs) and all(
            "5(1)(ba)" in ref or "5(1)(bb)" in ref or "5(1a)" in ref
            for ref in refs
        )
        if future_only:
            s = ("The system matches an Art. 5(1)(ba)/(bb) prohibited practice. "
                 "That new prohibition applies from 2 Dec 2026; plan withdrawal "
                 "or remediation before that date and assess other law separately.")
        else:
            s = ("The system falls under one or more prohibited practices (Art. 5) "
                 "and may in principle not be offered or used in the EU.")
    elif tier == eu.TIER_HIGH:
        if eu.annex_i_section_b_only(answers):
            s = ("The system is classified through Art. 6(1), but Annex I Section B "
                 "triggers the limited Art. 2(2) regime rather than the ordinary "
                 "Chapter III high-risk compliance pack.")
        else:
            s = ("The system is high-risk (Art. 6). The applicable actor- and "
                 "route-specific high-risk obligations apply.")
    elif tier == eu.TIER_LIMITED:
        s = ("The system is subject to transparency obligations (Art. 50); no "
             "high-risk requirements based on the answers.")
    else:
        s = ("No prohibited, high-risk or transparency triggers found. The "
             "minimal-risk tier adds no system-specific duties; Art. 4 and other "
             "applicable law still require separate attention.")
    if tier != eu.TIER_LIMITED and transparency:
        s += " In addition, transparency obligations apply (Art. 50)."
    if gpai:
        s += (" Note: regardless of the system risk tier, general-purpose AI "
              "*model* obligations apply independently (Chapter V).")
    return s
