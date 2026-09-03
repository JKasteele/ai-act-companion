"""Sector and self-assessment frameworks organisations actually adopt next to
the EU AI Act: ALTAI (EU HLEG), the EIOPA AI governance principles and DNB's
SAFEST principles for the (Dutch) financial sector, plus the DORA hook for AI
suppliers as ICT third-party providers.

Provenance / honesty:
  * ALTAI — "Assessment List for Trustworthy Artificial Intelligence", EU
    High-Level Expert Group on AI (2020). Public; only the seven requirement
    titles and one-line paraphrases are used.
  * EIOPA — "Artificial Intelligence governance principles: towards ethical and
    trustworthy AI in the European insurance sector" (2021). Six principles,
    titles + paraphrase.
  * DNB — "General principles for the use of Artificial Intelligence in the
    financial sector" (2019), the SAFEST principles. Titles + paraphrase.
  * DORA — Regulation (EU) 2022/2554, applicable since 17 Jan 2025. Article
    references to the ICT third-party risk chapter (Art. 28–30) and incident
    reporting (Art. 17–19).
  * The EU AI Act anchors and the ISO/IEC 42001 anchors are Companion-derived
    analytical alignments ("most-relevant anchor"), NOT official crosswalks.
"""

from .._normalize import as_list, select_field, truthy

# --- ALTAI: the seven requirements for trustworthy AI ------------------------
# (id, requirement, what it asks, EU AI Act anchors, ISO/IEC 42001 anchors,
#  intake fields that evidence it)
ALTAI = [
    ("1", "Human agency and oversight",
     "Fundamental rights, human agency (no undue reliance or manipulation), "
     "human oversight (human-in/on/in-command).",
     "Art. 14, Art. 26(2), Art. 5(1)(a–b)", "A.6.2.5, A.9.2",
     ["autonomy_level", "can_override", "human_oversight"]),
    ("2", "Technical robustness and safety",
     "Resilience to attack, fallback plans, accuracy, reliability and "
     "reproducibility.",
     "Art. 15, Art. 9", "A.6.2.4, A.6.2.6",
     ["sec_is_llm", "sec_third_party_models", "sec_external_data", "sec_agentic",
      "arch_auth_strength", "arch_access_control_layer", "arch_rate_limits"]),
    ("3", "Privacy and data governance",
     "Privacy, quality and integrity of data, access to data.",
     "Art. 10, Art. 10(5); GDPR", "A.7.2–A.7.6",
     ["data_personal", "data_special_category", "dg_data_owner", "dg_data_steward",
      "dg_datasets", "dg_lineage", "dg_q_representativeness"]),
    ("4", "Transparency",
     "Traceability, explainability, communication that one interacts with AI.",
     "Art. 12, Art. 13, Art. 50", "A.6.2.8, A.8.2, A.8.5",
     ["t_interacts_humans", "t_synthetic_content", "arch_logging"]),
    ("5", "Diversity, non-discrimination and fairness",
     "Avoidance of unfair bias, accessibility and universal design, "
     "stakeholder participation.",
     "Art. 10(2)(f–g), Art. 27", "A.5.4, A.7.4",
     ["hr_does_profiling", "affects_vulnerable", "dg_q_representativeness"]),
    ("6", "Societal and environmental well-being",
     "Sustainability, social impact, impact on society and democracy.",
     "Art. 27, Art. 95, Recital 27", "A.5.5",
     ["affects_vulnerable", "data_scale"]),
    ("7", "Accountability",
     "Auditability, minimisation and reporting of negative impacts, trade-offs, "
     "redress.",
     "Art. 9, Art. 17, Art. 72, Art. 73, Art. 26", "A.2.2, A.3.2, A.5.2, A.8.3",
     ["sys_owner", "dg_data_owner", "provider_role", "lifecycle_stage"]),
]

# --- EIOPA AI governance principles (2021) --------------------------------------
# (principle, paraphrase, EU AI Act anchors)
EIOPA_PRINCIPLES = [
    ("Proportionality", "Governance measures scale with the impact of the use case on "
                        "consumers and the insurer.", "Art. 9(3), Art. 6, Recital 59"),
    ("Fairness and non-discrimination", "Outcomes are fair; no unlawful discrimination, "
                                        "incl. via proxies; price-optimisation limits.",
     "Art. 10(2)(f–g), Art. 27; Annex III(5)(c)"),
    ("Transparency and explainability", "Explanations adapted to the audience "
                                        "(consumer, supervisor); disclosure of AI use.",
     "Art. 13, Art. 50, Art. 86"),
    ("Human oversight", "Humans understand, monitor and can intervene in the system; "
                        "roles and responsibilities are assigned.", "Art. 14, Art. 26(2)"),
    ("Data governance and record keeping", "Data quality, lawful use and traceability; "
                                           "records that allow auditing of the AI system.",
     "Art. 10, Art. 12, Art. 19, Art. 26(6)"),
    ("Robustness and performance", "Accuracy, resilience and monitoring throughout the "
                                   "lifecycle.", "Art. 15, Art. 72"),
]

# --- DNB SAFEST principles (2019) -------------------------------------------------
# (letter, principle, paraphrase, EU AI Act anchors)
DNB_SAFEST = [
    ("S", "Soundness", "AI applications are reliable, accurate and behave predictably; "
                       "risks are managed.", "Art. 9, Art. 15"),
    ("A", "Accountability", "Clear ownership; the board is accountable for AI outcomes.",
     "Art. 17, Art. 26; ISO 42001 A.3.2"),
    ("F", "Fairness", "AI does not disadvantage customers or groups unfairly.",
     "Art. 10(2)(f–g), Art. 27"),
    ("E", "Ethics", "AI use is consistent with the institution's values and with what "
                    "society expects.", "Art. 27, Recital 27"),
    ("S", "Skills", "Staff, management and supervisors have the skills to develop, use "
                    "and challenge AI.", "Art. 4 (AI literacy), Art. 14(4)"),
    ("T", "Transparency", "The institution can explain how and why AI is used, to "
                          "customers and to the supervisor.", "Art. 13, Art. 50, Art. 86"),
]

# --- Financial-entity hooks inside the AI Act itself --------------------------------
# The AI Act lets regulated financial institutions satisfy some obligations through
# their existing financial-services governance. (ref, what it allows)
FINANCIAL_ENTITY_HOOKS = [
    ("Art. 9(10)", "Risk-management steps may be part of, or combined with, the risk "
                   "management procedures required under other Union law (e.g. DORA "
                   "ICT risk management, Solvency II)."),
    ("Art. 17(4)", "For providers that are financial institutions, the quality "
                   "management system may be met by internal governance arrangements "
                   "under Union financial-services law."),
    ("Art. 18(3)", "Document retention: financial institutions keep the technical "
                   "documentation as part of the documentation kept under "
                   "financial-services law."),
    ("Art. 26(5)–(6)", "Deployers that are financial institutions: monitoring and "
                       "log-keeping are deemed fulfilled by complying with internal "
                       "governance rules under financial-services law; logs kept at "
                       "least 6 months."),
    ("Art. 74(6)", "Market surveillance for AI systems used by financial institutions "
                   "falls to the financial supervisor (in NL: DNB/AFM) where the "
                   "Member State so decides."),
]

# --- DORA: AI supplier as ICT third-party service provider ------------------------
# (ref, check, why it matters for AI)
DORA_VENDOR_CHECKLIST = [
    ("DORA Art. 28(1)–(2)", "AI supplier included in the ICT third-party risk strategy "
                            "and the register of information (contractual arrangements).",
     "A hosted model, an AI platform or a licensed dataset is an ICT service."),
    ("DORA Art. 28(4)", "Pre-contract due diligence: critical/important-function "
                        "assessment, supplier's ICT security, sub-outsourcing chain.",
     "Model providers subcontract compute and data; know the chain (AI Act Art. 25)."),
    ("DORA Art. 29", "Concentration risk assessed (single model provider / cloud region).",
     "Foundation-model markets are concentrated; plan substitutability."),
    ("DORA Art. 30(2)", "Contract covers: service description, data locations, "
                        "availability/integrity/confidentiality of data, data return on "
                        "exit, incident assistance, cooperation with authorities, "
                        "termination rights.",
     "Add: model-change and deprecation notice, log access, Art. 13 information."),
    ("DORA Art. 30(3)", "For critical or important functions: full audit and access "
                        "rights, participation in threat-led penetration testing, exit "
                        "strategies and transition periods.",
     "Insurance pricing or claims handling is typically an important function."),
    ("DORA Art. 17–19", "AI-related ICT incidents flow into the ICT incident process "
                        "and, if major, into the 4h / 24h / 72h / 1-month reporting.",
     "Run the AI Act Art. 73 clock and the DORA clock in parallel; one incident, "
     "two reports."),
    ("GDPR Art. 28", "Data-processing agreement with the AI supplier (sub-processors, "
                     "instructions, deletion, audit).",
     "Prompts and training feedback are personal data flows."),
    ("AI Act Art. 25", "Value-chain responsibilities agreed in writing (who is provider, "
                       "who is deployer, what a 'substantial modification' would be).",
     "A deployer that fine-tunes or re-purposes may become the provider."),
]

FINANCIAL_SECTORS = {"insurance", "banking_credit", "other_financial"}

PROVENANCE = (
    "ALTAI (EU HLEG, 2020), EIOPA AI governance principles (2021) and DNB SAFEST "
    "(2019) are reproduced as titles with one-line paraphrases; the EU AI Act and "
    "ISO/IEC 42001 anchors are a Companion-derived analytical alignment, not an "
    "official mapping. DORA references: Regulation (EU) 2022/2554."
)


def sector(answers):
    return select_field(answers or {}, "org_sector")


def is_financial_entity(answers):
    return sector(answers) in FINANCIAL_SECTORS


def dora_reasons(answers):
    """Why the DORA third-party hook fires, as a list of reasons (empty = no hook).

    Fires for a financial entity that relies on external AI/ML components or
    vendor-supplied datasets, in any role (a provider that buys a foundation
    model is a DORA customer of that supplier as much as a deployer is)."""
    answers = answers or {}
    if not is_financial_entity(answers):
        return []
    reasons = []
    if truthy(answers.get("sec_third_party_models")):
        reasons.append("relies on third-party / foundation models or external ML components")
    vendor_sets = [r.get("name") or "(unnamed)" for r in as_list(answers.get("dg_datasets"))
                   if isinstance(r, dict) and str(r.get("origin", "")).lower() == "external_vendor"]
    if vendor_sets:
        reasons.append("uses vendor-supplied datasets: " + ", ".join(str(v) for v in vendor_sets))
    if select_field(answers, "provider_role") == "deployer" and not reasons:
        reasons.append("deployer role: the AI system itself is supplied by a provider")
    return reasons


def altai_evidence(answers):
    """Per ALTAI requirement, which intake fields are answered (evidence
    pointers, not a score): [(id, title, asks, act, iso, answered, missing)]."""
    answers = answers or {}
    out = []
    for rid, title, asks, act, iso, fields in ALTAI:
        answered = [f for f in fields if _present(answers.get(f))]
        missing = [f for f in fields if f not in answered]
        out.append((rid, title, asks, act, iso, answered, missing))
    return out


def _present(v):
    if v is None:
        return False
    if isinstance(v, bool):
        return True
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return str(v).strip() != ""
