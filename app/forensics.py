"""Forensic-readiness assessment (evidence register + readiness score).

Pure function `assess_forensic_readiness(answers, classification=None) -> dict`.
Deterministic and AI-free: the score is a function of the structured `fr_*`
fields plus the structural fields that decide which artefacts are relevant
(`sec_agentic`, `sec_is_llm`, `arch_rag_modifiable`, `provider_role`,
`sec_third_party_models`, `data_*`, `org_sector`). Free text never moves the
score (asserted in tests/test_forensics.py, mirroring incident.py).

The tool describes which evidence should exist and where — it is not a SIEM.
"""

from ._normalize import as_list, select_field, truthy
from .knowledge import eu_ai_act as eu
from .knowledge import forensics as fx
from .knowledge import sector_frameworks as sfx

_INTEGRITY_SCORE = {"none": 0, "access_only": 0, "hashing": 1, "hash_chain_worm": 2, "signed": 2}
_VENDOR_SCORE = {"own_logs_sufficient": 2, "contractual_access": 2, "portal_only": 1, "none": 0}
_RETENTION_SCORE = {"lt6": 0, "6": 1, "7_24": 2, "gt24": 2}


def _band(total):
    for upper, label in fx.BANDS:
        if total <= upper:
            return label
    return fx.BANDS[-1][1]


def _relevant(relevance, ctx):
    """Is an artefact relevant for this system? (n/a otherwise)"""
    if relevance == "always":
        return True
    if relevance == "llm":
        return ctx["llm"] or ctx["rag"]
    if relevance == "agentic":
        return ctx["agentic"]
    if relevance == "provider":
        return ctx["role"] in ("provider", "both", "")
    if relevance == "high":
        return ctx["tier"] == "high"
    return True


def _context(answers, tier):
    return {
        "llm": truthy(answers.get("sec_is_llm")),
        "rag": truthy(answers.get("arch_rag_modifiable")),
        "agentic": truthy(answers.get("sec_agentic")),
        "role": select_field(answers, "provider_role"),
        "third_party": truthy(answers.get("sec_third_party_models")),
        "personal": truthy(answers.get("data_personal")),
        "special": truthy(answers.get("data_special_category")),
        "profiling": truthy(answers.get("hr_does_profiling")) or
        truthy(answers.get("automated_decision")),
        "tier": tier,
        "financial": sfx.is_financial_entity(answers),
        "sector": sfx.sector(answers),
    }


def evidence_register(answers, tier="minimal"):
    """One row per artefact: status 'in_place' | 'gap' | 'n/a' plus anchors."""
    answers = answers or {}
    ctx = _context(answers, tier)
    scope = set(as_list(answers.get("fr_log_scope")))
    integrity = select_field(answers, "fr_integrity")
    rows = []
    for aid, name, proves, refs, where, relevance in fx.EVIDENCE_ARTEFACTS:
        if aid == "lineage":
            present = bool(str(answers.get("dg_lineage") or "").strip())
        elif aid == "integrity":
            present = _INTEGRITY_SCORE.get(integrity, 0) >= 1
        else:
            present = aid in scope
        if not _relevant(relevance, ctx):
            status = "n/a"
        else:
            status = "in_place" if present else "gap"
        rows.append({"id": aid, "artefact": name, "proves": proves, "refs": refs,
                     "where": where, "status": status})
    return rows


def _dimension_scores(answers, ctx):
    scope = set(as_list(answers.get("fr_log_scope")))
    needed = {"inference_io", "model_version"}
    if ctx["agentic"]:
        needed.add("tool_calls")
    if ctx["rag"]:
        needed.add("retrieval_snapshot")
    if not scope:
        s_scope = 0
    elif needed <= scope and len(scope) >= 5:
        s_scope = 2
    else:
        s_scope = 1

    months = select_field(answers, "fr_retention_months")
    basis = select_field(answers, "fr_retention_basis")
    s_ret = _RETENTION_SCORE.get(months, 0)
    if months == "lt6" and basis == "gdpr_limited":
        s_ret = 1  # a documented GDPR-driven shorter term is allowed (Art. 19(1))

    s_int = _INTEGRITY_SCORE.get(select_field(answers, "fr_integrity"), 0)
    s_time = 2 if truthy(answers.get("fr_time_sync")) else 0
    pinned = truthy(answers.get("fr_model_pinned"))
    versioned = truthy(answers.get("fr_prompt_versioned")) or not ctx["llm"]
    s_model = 2 if (pinned and versioned) else (1 if pinned else 0)
    s_over = 2 if truthy(answers.get("fr_override_logged")) else 0

    vendor = select_field(answers, "fr_vendor_log_access")
    if not vendor and not ctx["third_party"] and ctx["role"] in ("provider", "both"):
        vendor = "own_logs_sufficient"
    s_vendor = _VENDOR_SCORE.get(vendor, 0)
    s_hold = 2 if truthy(answers.get("fr_legal_hold")) else 0

    return {"scope": s_scope, "retention": s_ret, "integrity": s_int, "time": s_time,
            "model_version": s_model, "override": s_over, "vendor": s_vendor,
            "legal_hold": s_hold}


def _gaps(answers, ctx, scores, register):
    """(severity, gap, action, ref) — deterministic, sorted high → low."""
    hi = "high" if ctx["tier"] == "high" else "medium"
    out = []
    scope = set(as_list(answers.get("fr_log_scope")))
    if scores["scope"] == 0:
        out.append((hi, "Nothing is recorded per inference.",
                    "Log input, output, timestamp, calling identity and the exact model "
                    "version for every inference.", "Art. 12(1)–(2)"))
    if ctx["agentic"] and "tool_calls" not in scope:
        out.append((hi, "Agentic system without a tool-call trace.",
                    "Log every tool call with tool, arguments, invoking identity, permission "
                    "and approval state, with correlation ids.", "Art. 12(2), Art. 14; AML.M0024"))
    if ctx["rag"] and "retrieval_snapshot" not in scope:
        out.append(("medium", "Modifiable knowledge base without a retrieval snapshot.",
                    "Record which documents/chunks were in the context per response "
                    "(immutable retrieval log).", "Art. 12(2); OWASP LLM08"))
    if ctx["profiling"] and scores["override"] == 0:
        out.append((hi, "Decisions about people without override logging.",
                    "Log who reviewed, who deviated from the model advice, when and why — "
                    "otherwise Art. 14 / GDPR Art. 22 human oversight cannot be evidenced.",
                    "Art. 14(4); GDPR Art. 22(3)"))
    elif scores["override"] == 0:
        out.append(("medium", "Human-oversight events are not logged.",
                    "Log reviews and overrides with reason.", "Art. 14(4), Art. 26(2)"))
    if scores["model_version"] < 2:
        out.append(("medium", "Model revision and/or prompt version not pinned per inference.",
                    "Record the exact model revision (and prompt-template version + hash) in "
                    "every inference record.", "Art. 12(2), Annex IV(2)(b)"))
    months = select_field(answers, "fr_retention_months")
    basis = select_field(answers, "fr_retention_basis")
    if months == "lt6" and basis != "gdpr_limited":
        out.append((hi, "Retention below the six-month floor without a recorded GDPR basis.",
                    "Either keep logs ≥ 6 months, or document the data-protection reason for "
                    "a shorter term (Art. 19(1) 'unless provided otherwise').",
                    "Art. 19(1), Art. 26(6)"))
    elif not months:
        out.append(("medium", "No retention period recorded.",
                    "Set a retention period and its basis (AI Act floor, financial-services "
                    "term, or a GDPR-limited term).", "Art. 19, Art. 26(6)"))
    if scores["integrity"] == 0:
        out.append((hi, "Logs are not tamper-evident.",
                    "Hash or hash-chain the records, store in WORM/append-only storage "
                    "isolated from the monitored system, log access to the logs.",
                    "ISO 27001 5.28, 8.15; NIS2 guidance §3.2.5"))
    elif scores["integrity"] == 1:
        out.append(("low", "Hashing without an independent time anchor / WORM.",
                    "Add append-only storage or signed records with a trusted timestamp.",
                    "ISO 27001 8.15, 8.17"))
    if scores["time"] == 0:
        out.append(("medium", "No synchronised time source across evidence sources.",
                    "Synchronise clocks (NTP/PTP) for application, gateway, workflow and "
                    "data-access logs so timelines can be correlated.",
                    "ISO 27001 8.17; CIS 8.4"))
    if scores["vendor"] == 0:
        out.append((hi if ctx["third_party"] else "medium",
                    "No access to the supplier's evidence.",
                    "Agree information, technical access and assistance in writing (AI Act "
                    "Art. 25(4)); for critical functions use DORA Art. 30(3) audit rights.",
                    "Art. 25(4), Art. 13; DORA Art. 30(3)"))
    elif scores["vendor"] == 1:
        out.append(("low", "Supplier evidence only via a portal.",
                    "Export and retain supplier-side logs under your own retention and "
                    "integrity controls.", "Art. 25(4); DORA Art. 28"))
    if scores["legal_hold"] == 0:
        out.append((hi, "No legal-hold / evidence-freeze procedure.",
                    "Define who can declare a hold, how log rotation is stopped and how the "
                    "running model version is pinned — Art. 73 forbids altering the system "
                    "before reporting.", "Art. 73; ISO 27001 5.28"))
    if not str(answers.get("fr_evidence_owner") or "").strip():
        out.append(("medium", "No owner of the evidence file.",
                    "Name the role accountable for the evidence register and for holds.",
                    "Art. 17(1)(m); ISO 42001 A.3.2"))
    if not truthy(answers.get("fr_drill")):
        out.append(("low", "Evidence retrieval not exercised in the last 12 months.",
                    "Run a tabletop: pick a past decision and reconstruct model version, "
                    "prompt, input, output and reviewer within one working day.",
                    "Rowlingson step 8; ISO 27001 5.24"))
    pii = select_field(answers, "fr_log_pii")
    if pii == "full" and ctx["special"]:
        out.append(("high", "Full prompt/response content incl. special-category data in logs.",
                    "Log a case-id or a hash of the input instead, or pseudonymise and move "
                    "full content to a separate archive with stricter access and shorter "
                    "retention.", "GDPR Art. 5(1)(c), Art. 9, Art. 32"))
    elif pii == "full" and ctx["personal"]:
        out.append(("medium", "Full personal-data content in logs.",
                    "Consider hashing or pseudonymising log content; keep full content only "
                    "under legal hold.", "GDPR Art. 5(1)(c), Art. 32"))
    for r in register:
        if r["status"] == "gap" and r["id"] not in ("inference_io", "tool_calls",
                                                    "retrieval_snapshot", "integrity",
                                                    "human_override", "model_version"):
            out.append(("low", f"Artefact missing: {r['artefact']}.",
                        f"Make sure it exists and is retained ({r['where']}).", r["refs"]))
    order = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda g: order[g[0]])
    return out


def reporting_clocks(answers, tier="minimal"):
    """Which reporting regimes can run in parallel for this system."""
    answers = answers or {}
    ctx = _context(answers, tier)
    rows = []
    ai_deadlines = " · ".join(f"{deadline} ({case})" for case, deadline, _b in eu.ART_73_TIMELINE)
    rows.append({
        "regime": "EU AI Act Art. 73", "trigger": "serious incident (Art. 3(49))",
        "starts": "causal link established, or reasonably likely",
        "deadlines": ai_deadlines,
        "recipient": "market surveillance authority" + (
            " — for financial institutions the financial supervisor (Art. 74(6))"
            if ctx["financial"] else ""),
        "applies": tier == "high",
        "note": "Providers report; deployers inform the provider (Art. 26(5)) and, if the "
                "provider cannot be reached, report directly.",
    })
    for regime, trigger, starts, deadlines, recipient, condition, note in fx.OTHER_CLOCKS:
        if condition == "personal_data":
            applies = ctx["personal"]
        elif condition == "financial":
            applies = ctx["financial"]
        elif condition == "nis2":
            applies = (not ctx["financial"]) and ctx["sector"] in ("healthcare", "public_sector",
                                                                    "other", "general")
        else:
            applies = True
        rows.append({"regime": regime, "trigger": trigger, "starts": starts,
                     "deadlines": deadlines, "recipient": recipient, "applies": applies,
                     "note": note})
    return rows


def assess_forensic_readiness(answers, classification=None):
    """Return register rows, dimension scores, total, band, gaps, conflicts and clocks."""
    answers = answers or {}
    tier = (classification or {}).get("tier", "minimal")
    ctx = _context(answers, tier)
    register = evidence_register(answers, tier)
    scores = _dimension_scores(answers, ctx)
    total = sum(scores.values())
    gaps = _gaps(answers, ctx, scores, register)
    conflicts = [g for g in gaps if "floor" in g[1] or "special-category" in g[1]]
    return {
        "tier": tier,
        "register": register,
        "scores": scores,
        "total": total,
        "max": fx.MAX_SCORE,
        "band": _band(total),
        "gaps": [{"severity": s, "gap": g, "action": a, "ref": r} for s, g, a, r in gaps],
        "conflicts": [{"severity": s, "gap": g, "action": a, "ref": r}
                      for s, g, a, r in conflicts],
        "clocks": reporting_clocks(answers, tier),
        "financial_entity": ctx["financial"],
        "provenance": fx.PROVENANCE,
    }
