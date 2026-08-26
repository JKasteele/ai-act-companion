"""EU AI Act (Regulation (EU) 2024/1689) as a structured knowledge base.

The classifier references the identifiers in this file so that every conclusion
is traceable to a concrete article or annex. Citations are summarised
paraphrases; always consult the consolidated regulation for the exact text.

Disclaimer: this is a self-assessment aid, not legal advice.
"""

import re

from .._normalize import truthy

REGULATION = "Regulation (EU) 2024/1689 (EU AI Act)"
CELEX = "32024R1689"
EURLEX_URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"
_EXPLORER = "https://artificialintelligenceact.eu"
_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
          "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11}


def ref_url(ref):
    """Resolve a citation token (e.g. 'Art. 5(1)(a)', 'Annex III(4)') to a
    public deep link on the AI Act Explorer, or None if it can't be parsed.

    Article numbers take precedence (a token like 'Art. 11 + Annex IV' links to
    the article); a pure 'Annex ...' token links to that annex.
    """
    if not ref:
        return None
    m = re.search(r"Art\.?\s*(\d+)", ref)
    if m:
        return f"{_EXPLORER}/article/{int(m.group(1))}/"
    m = re.search(r"Annex\s+([IVX]+)", ref)
    if m and m.group(1) in _ROMAN:
        return f"{_EXPLORER}/annex/{_ROMAN[m.group(1)]}/"
    return None

# --- Risk tiers (ascending severity) ---------------------------------------
TIER_PROHIBITED = "prohibited"
TIER_HIGH = "high"
TIER_LIMITED = "limited"
TIER_MINIMAL = "minimal"

TIER_ORDER = {
    TIER_MINIMAL: 0,
    TIER_LIMITED: 1,
    TIER_HIGH: 2,
    TIER_PROHIBITED: 3,
}

TIER_LABELS = {
    TIER_PROHIBITED: "Prohibited (unacceptable risk)",
    TIER_HIGH: "High risk",
    TIER_LIMITED: "Limited risk (transparency obligations)",
    TIER_MINIMAL: "Minimal risk",
}

TIER_DESCRIPTIONS = {
    TIER_PROHIBITED: (
        "The system (potentially) falls under a prohibited AI practice in "
        "Article 5 and may not be placed on the market, put into service or "
        "used in the Union."
    ),
    TIER_HIGH: (
        "The system is high-risk. Extensive obligations apply (e.g. risk "
        "management system, data governance, technical documentation, logging, "
        "human oversight, conformity assessment and CE marking)."
    ),
    TIER_LIMITED: (
        "The system is subject to transparency obligations (Article 50): "
        "users/affected persons must be informed about the interaction with AI "
        "or about generated/manipulated content."
    ),
    TIER_MINIMAL: (
        "No mandatory AI Act requirements. Voluntary codes of conduct are "
        "encouraged (Article 95). Good governance is still recommended."
    ),
}

# --- Article 5: prohibited practices ---------------------------------------
# Key = question id in the intake; read 1-to-1 by the classifier.
PROHIBITED_PRACTICES = {
    "p_manipulation": {
        "ref": "Art. 5(1)(a)",
        "title": "Subliminal, manipulative or deceptive techniques",
        "summary": (
            "Techniques that materially distort behaviour beyond a person's "
            "awareness and that (are likely to) cause harm."
        ),
    },
    "p_vulnerability": {
        "ref": "Art. 5(1)(b)",
        "title": "Exploitation of vulnerabilities",
        "summary": (
            "Exploiting vulnerabilities due to age, disability or a specific "
            "socio-economic situation to materially distort behaviour with "
            "(likely) harm."
        ),
    },
    "p_social_scoring": {
        "ref": "Art. 5(1)(c)",
        "title": "Social scoring",
        "summary": (
            "Evaluation/classification of persons based on social behaviour or "
            "characteristics leading to detrimental or unfavourable treatment "
            "in an unrelated context or that is disproportionate."
        ),
    },
    "p_predictive_policing": {
        "ref": "Art. 5(1)(d)",
        "title": "Predictive policing based on profiling",
        "summary": (
            "Assessing the risk that a person will commit a criminal offence "
            "based solely on profiling or personality traits."
        ),
    },
    "p_facial_scraping": {
        "ref": "Art. 5(1)(e)",
        "title": "Untargeted scraping of facial images",
        "summary": (
            "Untargeted scraping of facial images from the internet or CCTV to "
            "build or expand facial recognition databases."
        ),
    },
    "p_emotion_work_edu": {
        "ref": "Art. 5(1)(f)",
        "title": "Emotion recognition in the workplace/education",
        "summary": (
            "Inferring emotions of persons in the workplace or in educational "
            "institutions (except for medical or safety reasons)."
        ),
    },
    "p_biometric_categorization_sensitive": {
        "ref": "Art. 5(1)(g)",
        "title": "Biometric categorisation of sensitive attributes",
        "summary": (
            "Biometric categorisation that infers a person's race, political "
            "opinions, trade union membership, religion, sex life or sexual "
            "orientation."
        ),
    },
    "p_realtime_rbi_le": {
        "ref": "Art. 5(1)(h)",
        "title": "Real-time remote biometric identification (RBI) for law enforcement",
        "summary": (
            "Real-time remote biometric identification in publicly accessible "
            "spaces for law enforcement, except for an exhaustively listed set "
            "of pre-authorised exceptions."
        ),
    },
}

# --- Article 6 + Annex III: high-risk use cases ----------------------------
ART_6_1 = {
    "ref": "Art. 6(1) jo. Annex I",
    "title": "Safety component under Union harmonisation legislation",
    "summary": (
        "The AI system is a product, or the safety component of a product, "
        "covered by the harmonisation legislation listed in Annex I and "
        "required to undergo a third-party conformity assessment."
    ),
}

ART_6_3 = {
    "ref": "Art. 6(3)",
    "title": "Derogation: no significant risk",
    "summary": (
        "A system in Annex III is not high-risk if it does not pose a "
        "significant risk to health, safety or fundamental rights - e.g. a "
        "narrow procedural task, improving the result of a previously completed "
        "human activity, detecting decision patterns/deviations, or a "
        "preparatory task. This does NOT apply if the system performs profiling "
        "of natural persons. The provider must document this assessment "
        "(Art. 6(4))."
    ),
}

# Key = option id in the 'hr_usecases' multiselect.
HIGH_RISK_USECASES = {
    "biometrics": {
        "ref": "Annex III(1)",
        "title": "Biometrics",
        "summary": (
            "Remote biometric identification, biometric categorisation by "
            "sensitive attributes, and emotion recognition (insofar as not "
            "prohibited under Art. 5)."
        ),
    },
    "critical_infra": {
        "ref": "Annex III(2)",
        "title": "Critical infrastructure",
        "summary": (
            "Safety components in the management/operation of critical digital "
            "infrastructure, road traffic and the supply of water, gas, heating "
            "and electricity."
        ),
    },
    "education": {
        "ref": "Annex III(3)",
        "title": "Education and vocational training",
        "summary": (
            "Access/admission, evaluation of learning outcomes, assessment of "
            "the appropriate level of education and monitoring/detection of "
            "prohibited behaviour during tests."
        ),
    },
    "employment": {
        "ref": "Annex III(4)",
        "title": "Employment, workforce management and access to self-employment",
        "summary": (
            "Recruitment and selection, decisions on terms/promotion/"
            "termination, task allocation based on behaviour/traits, and "
            "monitoring/evaluation of performance."
        ),
    },
    "essential_services": {
        "ref": "Annex III(5)",
        "title": "Access to essential private and public services",
        "summary": (
            "Assessment of eligibility for public benefits, creditworthiness/"
            "credit scoring, risk assessment/pricing in life and health "
            "insurance, and triage of emergency services."
        ),
    },
    "law_enforcement": {
        "ref": "Annex III(6)",
        "title": "Law enforcement",
        "summary": (
            "Risk assessments, polygraphs, evaluation of evidence and profiling "
            "in the context of law enforcement."
        ),
    },
    "migration_border": {
        "ref": "Annex III(7)",
        "title": "Migration, asylum and border control",
        "summary": (
            "Polygraphs, risk assessments, examination of applications for "
            "asylum/visa/residence and detection/recognition in a border "
            "context."
        ),
    },
    "justice_democracy": {
        "ref": "Annex III(8)",
        "title": "Administration of justice and democratic processes",
        "summary": (
            "Assisting a judicial authority in researching/interpreting facts "
            "and law, and influencing the outcome of elections/referenda or "
            "voting behaviour."
        ),
    },
}

# Core obligations for high-risk (summarised), for the report.
# Each row is (ref, description, role) where role is which actor the duty falls
# on: "provider", "deployer", or "both". A pure deployer must not be shown the
# provider-only conformity-assessment / CE-marking duties, and vice versa. Use
# high_risk_obligations_for_role() to filter, never the raw list.
HIGH_RISK_OBLIGATIONS = [
    ("Art. 9", "Risk management system throughout the entire lifecycle.", "provider"),
    ("Art. 10", "Data governance and quality criteria for training, "
                "validation and test data (incl. bias examination).", "provider"),
    ("Art. 11 + Annex IV", "Draw up and keep technical documentation up to date.",
     "provider"),
    ("Art. 12", "Automatic recording of events (logging).", "provider"),
    ("Art. 13", "Transparency and provision of information to deployers.", "provider"),
    ("Art. 14", "Effective human oversight (designed in by the provider).", "provider"),
    ("Art. 15", "Accuracy, robustness and cybersecurity.", "provider"),
    ("Art. 16", "Overview of provider obligations for high-risk systems.", "provider"),
    ("Art. 17", "Quality management system.", "provider"),
    ("Art. 20", "Corrective actions and duty to inform (withdrawal/recall).",
     "provider"),
    ("Art. 22", "Authorised representative in the Union (for providers "
                "established outside the EU).", "provider"),
    ("Art. 25", "Responsibilities along the AI value chain (a deployer that "
                "substantially modifies a system, or puts its name on it, may "
                "become a provider).", "both"),
    ("Art. 43", "Conformity assessment before putting into service.", "provider"),
    ("Art. 47 + 48", "EU declaration of conformity and CE marking.", "provider"),
    ("Art. 49", "Registration in the EU database for high-risk systems.", "provider"),
    ("Art. 72", "Post-market monitoring.", "provider"),
    ("Art. 26", "Obligations for deployers (use per instructions, human "
                "oversight, monitoring, keep logs).", "deployer"),
    ("Art. 27", "Fundamental rights impact assessment (FRIA), where applicable.",
     "deployer"),
]


def high_risk_obligations_for_role(role):
    """Return the (ref, description) high-risk obligations for a given Art. 3
    role. Provider-only and deployer-only duties are filtered so the guidance
    is not wrong for the actor. Unknown/"both"/"other" -> show everything."""
    role = (role or "").strip().lower()
    if role == "provider":
        keep = {"provider", "both"}
    elif role == "deployer":
        keep = {"deployer", "both"}
    else:
        keep = {"provider", "deployer", "both"}
    return [(ref, desc) for ref, desc, r in HIGH_RISK_OBLIGATIONS if r in keep]


# --- Article 2: scope exemptions -------------------------------------------
# Key = intake question id. If any is set, the system is out of the AI Act's
# scope and the specific paragraph is cited.
SCOPE_EXEMPTIONS = {
    "exempt_military": {
        "ref": "Art. 2(3)",
        "title": "Military, defence or national-security use",
        "summary": (
            "AI systems placed on the market, put into service or used "
            "exclusively for military, defence or national-security purposes "
            "fall outside the AI Act."
        ),
    },
    "exempt_research": {
        "ref": "Art. 2(6)",
        "title": "Scientific research and development",
        "summary": (
            "AI systems and models developed and put into service for the sole "
            "purpose of scientific research and development are excluded."
        ),
    },
    "exempt_premarket": {
        "ref": "Art. 2(8)",
        "title": "Pre-market research, testing and development",
        "summary": (
            "Research, testing and development activity concerning AI systems "
            "prior to being placed on the market is excluded — this does NOT "
            "cover testing in real-world conditions."
        ),
    },
    "exempt_personal": {
        "ref": "Art. 2(10)",
        "title": "Purely personal, non-professional use",
        "summary": (
            "Use of an AI system by a natural person in the course of a purely "
            "personal, non-professional activity is excluded."
        ),
    },
}

# --- Article 50: transparency obligations ----------------------------------
TRANSPARENCY_OBLIGATIONS = {
    "t_interacts_humans": {
        "ref": "Art. 50(1)",
        "title": "Interaction with natural persons",
        "summary": (
            "Persons must be informed that they are interacting with an AI "
            "system, unless this is obvious."
        ),
    },
    "t_synthetic_content": {
        "ref": "Art. 50(2)",
        "title": "Marking of synthetic content",
        "summary": (
            "AI-generated/manipulated audio, image, video or text must be "
            "marked as artificially generated in a machine-readable format."
        ),
    },
    "t_emotion_or_biometric_cat": {
        "ref": "Art. 50(3)",
        "title": "Emotion recognition / biometric categorisation",
        "summary": (
            "Inform affected persons about the operation of an emotion "
            "recognition or biometric categorisation system (insofar as "
            "permitted)."
        ),
    },
    "t_deepfake": {
        "ref": "Art. 50(4)",
        "title": "Deepfakes",
        "summary": (
            "Content constituting a deepfake must be disclosed as artificially "
            "generated/manipulated."
        ),
    },
}

# --- General-purpose AI (GPAI), Chapter V ----------------------------------
GPAI = {
    "model": {
        "ref": "Art. 53 (jo. Art. 3(63))",
        "title": "Obligations for providers of GPAI models",
        "summary": (
            "Technical documentation, information for downstream providers, a "
            "copyright policy and a summary of the training data."
        ),
    },
    "systemic": {
        "ref": "Art. 51 + 55",
        "title": "GPAI model with systemic risk",
        "summary": (
            "In case of systemic risk (e.g. >= 10^25 FLOP training compute or "
            "designation): model evaluations, adversarial testing, risk "
            "mitigation, incident reporting and cybersecurity."
        ),
    },
    "open_source": {
        "ref": "Art. 53(2)",
        "title": "Open-source GPAI model — reduced obligations",
        "summary": (
            "Released under a free and open-source licence with public weights "
            "and usage information: exempt from the technical-documentation "
            "(Art. 53(1)(a)) and downstream-information (Art. 53(1)(b)) duties. "
            "The copyright policy (Art. 53(1)(c)) and the training-content "
            "summary (Art. 53(1)(d)) still apply. This carve-out does NOT apply "
            "to GPAI models with systemic risk."
        ),
    },
}

# --- Article 99 / 101: administrative fines --------------------------------
# Figures are the ceilings stated in the Regulation; the text is paraphrased.
# Keyed so the report can show only the rows relevant to the triggered tier.
PENALTIES = {
    "prohibited": {
        "ref": "Art. 99(3)",
        "what": "Non-compliance with the prohibited practices (Art. 5).",
        "max": "up to €35,000,000 or 7% of total worldwide annual turnover, "
               "whichever is higher",
    },
    "high_other": {
        "ref": "Art. 99(4)",
        "what": "Non-compliance with obligations other than Art. 5 — providers, "
                "deployers, importers, distributors, authorised representatives "
                "and notified bodies, including the high-risk and transparency "
                "obligations.",
        "max": "up to €15,000,000 or 3% of total worldwide annual turnover, "
               "whichever is higher",
    },
    "incorrect_info": {
        "ref": "Art. 99(5)",
        "what": "Supplying incorrect, incomplete or misleading information to "
                "notified bodies or competent authorities.",
        "max": "up to €7,500,000 or 1% of total worldwide annual turnover, "
               "whichever is higher",
    },
    "gpai": {
        "ref": "Art. 101",
        "what": "Fines for providers of general-purpose AI models (imposed by "
                "the Commission).",
        "max": "up to €15,000,000 or 3% of total worldwide annual turnover, "
               "whichever is higher",
    },
}

PENALTIES_SME_NOTE = (
    "For SMEs and start-ups, each fine is capped at the **lower** of the "
    "percentage or the fixed amount (Art. 99(6))."
)

# --- Article 3(49) + Article 73: serious incidents -------------------------
# A "serious incident" (Art. 3(49)) is an incident or malfunctioning of an AI
# system that directly or indirectly leads to any of the four limbs below.
# Each limb lists the intake key(s) (section 10) that mark it as met.
SERIOUS_INCIDENT = {
    "ref": "Art. 3(49)",
    "title": "Serious incident",
    "summary": (
        "An incident or malfunctioning of an AI system that directly or "
        "indirectly leads to any of: the death of a person or serious harm to "
        "health; serious and irreversible disruption of critical infrastructure; "
        "infringement of fundamental-rights obligations under Union law; or "
        "serious harm to property or the environment."
    ),
    # (limb ref, description, intake keys that mark it met)
    "limbs": [
        ("Art. 3(49)(a)",
         "the death of a person, or serious harm to a person's health",
         ["inc_death", "inc_health"]),
        ("Art. 3(49)(b)",
         "serious and irreversible disruption of the management or operation "
         "of critical infrastructure",
         ["inc_critical_infra"]),
        ("Art. 3(49)(c)",
         "infringement of obligations under Union law intended to protect "
         "fundamental rights",
         ["inc_fundamental_rights"]),
        ("Art. 3(49)(d)",
         "serious harm to property or the environment",
         ["inc_property_env"]),
    ],
}

# Article 73 reporting deadlines (provider -> market surveillance authority):
# report "without undue delay" and in any event no later than the limit below,
# after establishing the causal link (or its reasonable likelihood).
# (case, deadline, legal basis)
ART_73_TIMELINE = [
    ("General serious incident", "15 days", "Art. 73"),
    ("Widespread infringement, or a serious and irreversible disruption of "
     "the management or operation of critical infrastructure", "2 days", "Art. 73"),
    ("Death of a person", "10 days", "Art. 73"),
]

ART_73_NOTE = (
    "Report without undue delay to the market surveillance authority of the "
    "Member State(s) where the incident occurred, and in any event within the "
    "limit above. An initial — possibly incomplete — report may be filed first "
    "and followed by a complete report. Deployers must inform the provider "
    "(and, where the provider cannot be reached, report directly)."
)

DISCLAIMER = (
    "This report was generated by AI Act Companion as an aid for a structured "
    "self-assessment. It is NOT legal advice and does not replace an assessment "
    "by a qualified lawyer or the competent supervisory authority. "
    "Classification is based on the answers provided by the user."
)

# --- Phased applicability (Art. 113 + transitional provisions) -------------
# (date, what applies, legal basis)
TIMELINE = [
    ("1 Aug 2024", "Entry into force.", "Art. 113"),
    ("2 Feb 2025", "Prohibited practices (Art. 5) and AI literacy (Art. 4) apply.",
     "Art. 113(a)"),
    ("2 May 2025", "GPAI codes of practice due (in practice published Jul 2025).",
     "Art. 56(9)"),
    ("2 Aug 2025", "GPAI obligations (Ch. V), governance, notifying authorities "
     "and penalties apply (except the Art. 101 GPAI fines).", "Art. 113(b)"),
    ("2 Feb 2026", "Commission guidance on high-risk classification due.", "Art. 6(5)"),
    ("2 Aug 2026", "General application: most obligations, incl. Annex III "
     "high-risk systems and Art. 50 transparency.", "Art. 113"),
    ("2 Aug 2027", "High-risk systems under Art. 6(1)/Annex I (regulated "
     "products); GPAI models already on the market must comply.",
     "Art. 113(c), Art. 111(3)"),
]


# Key application milestones with machine-readable (ISO) dates, for a UI
# countdown. Same facts as TIMELINE; kept as data so the frontend never
# hard-codes a date. (date_iso, short label, legal basis)
MILESTONES = [
    ("2025-02-02", "Prohibited practices (Art. 5) & AI literacy (Art. 4)", "Art. 113(a)"),
    ("2025-08-02", "GPAI obligations, governance & penalties", "Art. 113(b)"),
    ("2026-08-02", "High-risk (Annex III) & Art. 50 transparency obligations", "Art. 113"),
    ("2027-08-02", "High-risk under Art. 6(1)/Annex I (regulated products)", "Art. 113(c)"),
]


def applies_from(tier, answers):
    """When the core obligations for THIS system start to apply.

    GPAI-aware: a general-purpose AI model carries Chapter V obligations from
    2 Aug 2025 independently of its risk tier, so a minimal-tier GPAI model has
    a real deadline rather than "no mandatory deadline". This keeps the risk
    report's headline consistent with the obligations & conformity tracker.
    """
    answers = answers or {}
    gpai = truthy(answers.get("gpai_model"))
    gpai_note = (" GPAI model obligations (Chapter V) additionally apply from "
                 "2 Aug 2025 (Art. 113(b)).")

    if tier == TIER_PROHIBITED:
        base = {"date": "2 Feb 2025",
                "what": "Prohibition under Art. 5 already applies.",
                "basis": "Art. 113(a)"}
    elif tier == TIER_HIGH:
        if truthy(answers.get("hr_safety_component")):
            base = {"date": "2 Aug 2027",
                    "what": "High-risk obligations for Art. 6(1)/Annex I "
                            "(regulated products).",
                    "basis": "Art. 113(c)"}
        else:
            base = {"date": "2 Aug 2026",
                    "what": "High-risk obligations for Annex III systems.",
                    "basis": "Art. 113"}
    elif tier == TIER_LIMITED:
        base = {"date": "2 Aug 2026",
                "what": "Transparency obligations (Art. 50) apply.",
                "basis": "Art. 113"}
    else:
        base = {"date": "-",
                "what": "No mandatory deadline (minimal risk).",
                "basis": "Art. 95 (voluntary)"}

    if not gpai:
        return base
    # A minimal-tier system that is a GPAI model: the GPAI date is the only
    # mandatory deadline, so surface it as the headline.
    if tier == TIER_MINIMAL:
        return {"date": "2 Aug 2025",
                "what": "GPAI model obligations (Chapter V) apply.",
                "basis": "Art. 113(b)"}
    # Otherwise keep the tier headline but flag the parallel GPAI deadline.
    if tier in (TIER_LIMITED, TIER_HIGH):
        base = dict(base)
        base["what"] = base["what"] + gpai_note
    return base
