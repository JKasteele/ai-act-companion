"""EU AI Act (Regulation (EU) 2024/1689) as a structured knowledge base.

The classifier references the identifiers in this file so that every conclusion
is traceable to a concrete article or annex. Citations are summarised
paraphrases; always consult the consolidated regulation for the exact text.

Disclaimer: this is a self-assessment aid, not legal advice.
"""

import re

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
HIGH_RISK_OBLIGATIONS = [
    ("Art. 9", "Risk management system throughout the entire lifecycle."),
    ("Art. 10", "Data governance and quality criteria for training, "
                "validation and test data (incl. bias examination)."),
    ("Art. 11 + Annex IV", "Draw up and keep technical documentation up to date."),
    ("Art. 12", "Automatic recording of events (logging)."),
    ("Art. 13", "Transparency and provision of information to deployers."),
    ("Art. 14", "Effective human oversight."),
    ("Art. 15", "Accuracy, robustness and cybersecurity."),
    ("Art. 17", "Quality management system (for providers)."),
    ("Art. 43", "Conformity assessment before putting into service."),
    ("Art. 47 + 48", "EU declaration of conformity and CE marking."),
    ("Art. 49", "Registration in the EU database for high-risk systems."),
    ("Art. 72", "Post-market monitoring."),
    ("Art. 26", "Obligations for deployers."),
    ("Art. 27", "Fundamental rights impact assessment (FRIA), where applicable."),
]

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
}

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


def applies_from(tier, answers):
    """When the core obligations for THIS system start to apply."""
    answers = answers or {}
    if tier == TIER_PROHIBITED:
        return {"date": "2 Feb 2025",
                "what": "Prohibition under Art. 5 already applies.",
                "basis": "Art. 113(a)"}
    if tier == TIER_HIGH:
        if answers.get("hr_safety_component"):
            return {"date": "2 Aug 2027",
                    "what": "High-risk obligations for Art. 6(1)/Annex I "
                            "(regulated products).",
                    "basis": "Art. 113(c)"}
        return {"date": "2 Aug 2026",
                "what": "High-risk obligations for Annex III systems.",
                "basis": "Art. 113"}
    if tier == TIER_LIMITED:
        return {"date": "2 Aug 2026",
                "what": "Transparency obligations (Art. 50) apply.",
                "basis": "Art. 113"}
    return {"date": "-",
            "what": "No mandatory deadline (minimal risk).",
            "basis": "Art. 95 (voluntary)"}
