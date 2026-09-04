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
EURLEX_URL = "https://eur-lex.europa.eu/eli/reg/2024/1689"
AMENDMENT_2026_URL = "https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng"

# --- Knowledge-base metadata -------------------------------------------
# The law moves; a report must say WHICH state of the law it reflects.
# Bump LAST_REVIEWED whenever the rules or dates in this module are checked
# against new guidance, and record every amending act in AMENDMENTS.
KNOWLEDGE_VERSION = "2026-09"
LAST_REVIEWED = "2026-09-04"
# (short name, what it changed, source URL)
AMENDMENTS = [
    ("Regulation (EU) 2026/1744 (Digital Omnibus on AI)",
     "In force 27 Jul 2026. Postpones the Annex III high-risk obligations "
     "(Ch. III s. 2, incl. FRIA Art. 27 and registration Art. 49) from "
     "2 Aug 2026 to 2 Dec 2027, and the Annex I (regulated products) "
     "obligations from 2 Aug 2027 to 2 Aug 2028. Art. 50 transparency, the "
     "penalty and enforcement provisions and supervision of Art. 4 AI literacy "
     "apply from 2 Aug 2026 as originally planned; generative systems already "
     "on the market get until 2 Dec 2026 for machine-readable marking. It also "
     "inserted Art. 4a, Art. 5(1)(ba)/(bb) and Art. 6(1a)-(1c); the two new "
     "prohibitions apply from 2 Dec 2026. Amended Art. 2(2) limits the regime "
     "for Annex I Section B, while Art. 2(13) creates a delegated-act framework "
     "for equivalent product-law protections in Section A.",
     "https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng"),
]
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
    if "2026/1744" in ref:
        return AMENDMENT_2026_URL
    # The third-party explorer may not yet reproduce newly inserted paragraphs.
    # Send amendment-specific tokens to the official amending act instead of
    # accidentally resolving e.g. "Art. 4a" to the old Article 4 page.
    if re.search(r"Art\.?\s*4a\b", ref, re.IGNORECASE) or re.search(
            r"Art\.?\s*5\(1\)\((?:ba|bb)\)|Art\.?\s*5\(1[ab]\)|Art\.?\s*6\(1[abc]\)",
            ref, re.IGNORECASE):
        return AMENDMENT_2026_URL
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
        "The system is high-risk. Extensive actor- and route-specific obligations "
        "apply: providers carry the conformity and product-governance duties, while "
        "deployers carry the use, oversight, monitoring and applicable FRIA duties."
    ),
    TIER_LIMITED: (
        "The system is subject to transparency obligations (Article 50): "
        "users/affected persons must be informed about the interaction with AI "
        "or about generated/manipulated content."
    ),
    TIER_MINIMAL: (
        "The minimal-risk tier adds no system-specific mandatory duty. Cross-cutting "
        "duties such as AI-literacy support measures (Article 4), any separate GPAI "
        "duties and other applicable law still need to be assessed; voluntary codes "
        "of conduct are encouraged (Article 95)."
    ),
}

# --- Article 5: prohibited practices ---------------------------------------
# Key = question id in the intake; read 1-to-1 by the classifier.
PROHIBITED_PRACTICES = {
    "p_manipulation": {
        "ref": "Art. 5(1)(a)",
        "title": "Subliminal, manipulative or deceptive techniques",
        "summary": (
            "Subliminal techniques beyond a person's consciousness, or purposefully "
            "manipulative/deceptive techniques, that appreciably impair informed "
            "decision-making, materially distort behaviour and cause or are reasonably "
            "likely to cause significant harm."
        ),
    },
    "p_vulnerability": {
        "ref": "Art. 5(1)(b)",
        "title": "Exploitation of vulnerabilities",
        "summary": (
            "Exploiting vulnerabilities due to age, disability or a specific "
            "socio-economic situation to materially distort behaviour with "
            "significant harm or a reasonable likelihood of significant harm."
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
            "based solely on profiling or personality traits, outside AI supporting "
            "a human assessment already based on objective and verifiable facts "
            "directly linked to criminal activity."
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
            "orientation, excluding the Regulation's narrow dataset-labelling/"
            "filtering and law-enforcement categorisation carve-outs."
        ),
    },
    "p_realtime_rbi_le": {
        "ref": "Art. 5(1)(h)",
        "title": "Real-time remote biometric identification (RBI) for law enforcement",
        "summary": (
            "Real-time remote biometric identification in publicly accessible "
            "spaces for law enforcement outside the exhaustively listed, necessary "
            "and proportionate exceptions and their prior-authorisation safeguards."
        ),
    },
}

# The two prohibitions inserted by Reg. (EU) 2026/1744 are not unconditional
# content flags.  Article 5(1a) contains different gateways for providers and
# deployers; the classifier evaluates those gateways separately instead of
# treating a general-purpose generator as prohibited merely because misuse is
# technically possible.  These provisions apply from 2 December 2026.
CONDITIONAL_PROHIBITED_PRACTICES = {
    "p_nonconsensual_intimate": {
        "ref": "Art. 5(1)(ba)",
        "title": "Non-consensual intimate or sexually explicit material",
        "summary": (
            "Realistic image, video, audio or similar material depicts an "
            "identifiable person's intimate parts or sexually explicit activity "
            "without that person's freely given, specific, informed, unambiguous "
            "and explicit consent. Under Art. 5(1b), an edit that neither increases "
            "exposure of intimate parts nor changes the nature of depicted sexual "
            "activity is not manipulation for this prohibition."
        ),
    },
    "p_child_sexual_material": {
        "ref": "Art. 5(1)(bb)",
        "title": "Child sexual abuse material or performance",
        "summary": (
            "Material or a performance within Article 2(c) or (e) of Directive "
            "2011/93/EU is generated or manipulated, unless a 'without right' "
            "defence applies under national law."
        ),
    },
}

NEW_ART_5_APPLICATION_DATE = "2 Dec 2026"

# --- Article 6 + Annex III: high-risk use cases ----------------------------
ART_6_1 = {
    "ref": "Art. 6(1)–(1c) jo. Annex I",
    "title": "Safety component under Union harmonisation legislation",
    "summary": (
        "The AI system is a product, or the safety component of a product, "
        "covered by the harmonisation legislation listed in Annex I and "
        "required to undergo a third-party conformity assessment for health or "
        "safety risks. A component's safety function and the consequences of its "
        "failure include the health and safety of persons or property (Art. 3(14)). "
        "Solely non-safety assistance, optimisation, efficiency, automation, "
        "convenience or quality-control functions are excluded, unless failure or "
        "malfunction would endanger health or safety (Art. 6(1a)–(1c))."
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

# Annex III point 5 has four distinct sub-points with different deployers and
# a different FRIA rule: Art. 27(1) makes the FRIA mandatory for EVERY deployer
# of a 5(b) or 5(c) system, private insurers and lenders included, not only for
# public bodies. Key = value of the `hr_essential_subarea` intake field.
ANNEX_III_5_SUBAREAS = {
    "public_benefits": {
        "ref": "Annex III(5)(a)",
        "title": "Eligibility for essential public benefits and services",
        "summary": (
            "Used by or on behalf of public authorities to evaluate eligibility "
            "for essential public assistance benefits and services (incl. "
            "healthcare services), or to grant, reduce, revoke or reclaim them."
        ),
        "fria_all_deployers": False,
    },
    "creditworthiness": {
        "ref": "Annex III(5)(b)",
        "title": "Creditworthiness / credit scoring of natural persons",
        "summary": (
            "Evaluates the creditworthiness of natural persons or establishes "
            "their credit score. Systems used solely to detect financial fraud "
            "are excluded from this point."
        ),
        "fria_all_deployers": True,
    },
    "insurance_life_health": {
        "ref": "Annex III(5)(c)",
        "title": "Risk assessment and pricing in life and health insurance",
        "summary": (
            "Risk assessment and pricing in relation to natural persons in the "
            "case of life and health insurance (underwriting, acceptance, "
            "premium setting, risk selection)."
        ),
        "fria_all_deployers": True,
    },
    "emergency_triage": {
        "ref": "Annex III(5)(d)",
        "title": "Emergency-call evaluation and emergency healthcare triage",
        "summary": (
            "Evaluates and classifies emergency calls, dispatches or prioritises "
            "emergency first-response services, or triages patients in "
            "emergency healthcare."
        ),
        "fria_all_deployers": False,
    },
}

# Context notes for Annex III(5)(c), keyed by the `hr_insurance_scope` field.
# Sector rules shape WHERE the risk actually sits; the classification itself
# does not change. NL notes reference the Zorgverzekeringswet (Zvw) and the
# Zorgverzekeraars Nederland code of conduct for processing personal data.
INSURANCE_SCOPE_NOTES = {
    "health_basic_nl": (
        "Dutch basic health insurance (Zvw): statutory acceptance duty and ban "
        "on premium differentiation. Risk assessment therefore cannot lawfully "
        "drive acceptance or premium for the basic package; the residual risk is "
        "indirect selection via proxies (marketing, steering towards or away "
        "from supplementary packages) and the ZN code-of-conduct rule that "
        "medical data from the basic package may not be used for accepting "
        "supplementary insurance. Document those boundaries in the FRIA."
    ),
    "health_supplementary": (
        "Supplementary health insurance: acceptance and pricing may be risk-based, "
        "so this is the Annex III(5)(c) core case. Special-category (health) data "
        "needs a GDPR Art. 9(2) condition; the Art. 4a allowance to process "
        "special categories for bias detection is narrow and comes with strict "
        "safeguards."
    ),
    "life": (
        "Life insurance: risk-based underwriting is the Annex III(5)(c) core case. "
        "Watch for proxies for health, age and ethnicity in the feature set and "
        "for the medical-examination boundaries in national insurance law."
    ),
    "other": (
        "Outside NL or a different product line: check the national insurance "
        "and anti-discrimination rules that constrain risk-based pricing."
    ),
}

# Art. 10 broken into the elements a provider must evidence (and the deployer
# input-data duty in Art. 26(4)). (ref, requirement) — for the datagov report.
ART_10_REQUIREMENTS = [
    ("Art. 10(2)(a)", "Relevant design choices are documented."),
    ("Art. 10(2)(b)", "Data collection processes and the origin of data are documented; "
                      "for personal data, the original purpose of collection."),
    ("Art. 10(2)(c)", "Data-preparation operations (annotation, labelling, cleaning, "
                      "updating, enrichment, aggregation) are documented."),
    ("Art. 10(2)(d)", "Assumptions about what the data measures and represents are "
                      "formulated."),
    ("Art. 10(2)(e)", "Availability, quantity and suitability of the datasets are "
                      "assessed."),
    ("Art. 10(2)(f)", "Datasets are examined for possible biases that could affect "
                      "health, safety or fundamental rights or lead to discrimination."),
    ("Art. 10(2)(g)", "Measures to detect, prevent and mitigate those biases are in place."),
    ("Art. 10(2)(h)", "Data gaps or shortcomings that prevent compliance are identified "
                      "and addressed."),
    ("Art. 10(3)", "Datasets are relevant, sufficiently representative and, to the best "
                   "extent possible, free of errors and complete; statistical properties "
                   "fit the persons and groups the system is used on."),
    ("Art. 10(4)", "Datasets reflect the geographical, contextual, behavioural or "
                   "functional setting in which the system will be used."),
    ("Art. 4a(1)", "Provider of a high-risk system: special categories of personal "
                   "data may exceptionally be processed for Art. 10(2)(f)–(g) bias "
                   "detection/correction only where strictly necessary and subject "
                   "to every listed safeguard (including alternatives assessment, "
                   "reuse limits, pseudonymisation/security, access controls, no "
                   "third-party access, timely deletion and processing records)."),
    ("Art. 4a(2)", "Providers and deployers of other AI systems or models, and "
                   "deployers of high-risk systems, may use the same exceptional "
                   "basis only where strictly necessary for biases likely to affect "
                   "health or safety, fundamental rights or Union-law discrimination, "
                   "and all Art. 4a(1) safeguards apply; this creates no duty to carry "
                   "out such processing."),
    ("Art. 26(4)", "Deployer: input data under its control is relevant and sufficiently "
                   "representative in view of the intended purpose."),
]

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
    ("Art. 49", "Registration in the EU database for Annex III high-risk systems.",
     "provider"),
    ("Art. 72", "Post-market monitoring.", "provider"),
    ("Art. 26", "Obligations for deployers (use per instructions, human "
                "oversight, monitoring, keep logs).", "deployer"),
    ("Art. 27", "Fundamental rights impact assessment (FRIA), where applicable.",
     "deployer"),
]


def high_risk_obligations_for_role(role, answers=None):
    """Return the (ref, description) high-risk obligations for a given Art. 3
    role. Provider-only and deployer-only duties are filtered so the guidance
    is not wrong for the actor or classification route. Unknown/"both"/"other"
    shows both actor sets. Art. 27 and Art. 49 are Annex-III-only here."""
    role = (role or "").strip().lower()
    raw_usecases = (answers or {}).get("hr_usecases") or []
    if isinstance(raw_usecases, str):
        raw_usecases = [raw_usecases]
    has_annex_iii = any(u and u != "none" for u in raw_usecases)
    if role == "provider":
        keep = {"provider", "both"}
    elif role == "deployer":
        keep = {"deployer", "both"}
    else:
        keep = {"provider", "deployer", "both"}
    return [
        (ref, desc)
        for ref, desc, r in HIGH_RISK_OBLIGATIONS
        if r in keep and (has_annex_iii or ref not in ("Art. 27", "Art. 49"))
    ]


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
# As amended by the Digital Omnibus on AI (Reg. (EU) 2026/1744, in force
# 27 Jul 2026), which postponed the stand-alone high-risk dates. See AMENDMENTS.
# (date, what applies, legal basis)
TIMELINE = [
    ("1 Aug 2024", "Entry into force.", "Art. 113"),
    ("2 Feb 2025", "Prohibited practices (Art. 5) and AI literacy (Art. 4) apply.",
     "Art. 113(a)"),
    ("2 May 2025", "GPAI codes of practice due (in practice published Jul 2025).",
     "Art. 56(9)"),
    ("2 Aug 2025", "GPAI obligations (Ch. V), governance, notifying authorities "
     "and penalties apply (except the Art. 101 GPAI fines).", "Art. 113(b)"),
    ("2 Feb 2026", "Commission guidance on high-risk classification due "
     "(draft guidelines published 19 May 2026).", "Art. 6(5)"),
    ("27 Jul 2026", "Digital Omnibus on AI (Reg. (EU) 2026/1744) enters into "
     "force, including Art. 4a and the revised Annex I scope framework; Annex III "
     "high-risk obligations move to 2 Dec 2027 and Annex I to 2 Aug 2028.",
     "Reg. (EU) 2026/1744"),
    ("2 Aug 2026", "Art. 50 transparency obligations, the penalty and enforcement "
     "provisions and supervision of Art. 4 AI literacy apply.", "Art. 113"),
    ("2 Dec 2026", "New prohibited practices for non-consensual intimate material "
     "and child sexual abuse material (Art. 5(1)(ba)/(bb), subject to Art. "
     "5(1a)/(1b)) apply; also the end of the Art. 50(2) machine-readable-marking "
     "grace period for generators already on the market before 2 Aug 2026.",
     "Art. 113(a); Art. 111(4)"),
    ("2 Aug 2027", "GPAI models already on the market before 2 Aug 2025 must "
     "comply.", "Art. 111(3)"),
    ("2 Dec 2027", "High-risk obligations for Annex III systems (Ch. III s. 2, "
     "incl. FRIA Art. 27 and registration Art. 49) apply.",
     "Art. 113"),
    ("2 Aug 2028", "High-risk obligations for Art. 6(1)/Annex I systems "
     "(regulated products) apply.", "Art. 113(c)"),
]


# Key application milestones with machine-readable (ISO) dates, for a UI
# countdown. Same facts as TIMELINE; kept as data so the frontend never
# hard-codes a date. (date_iso, short label, legal basis)
MILESTONES = [
    ("2025-02-02", "Prohibited practices (Art. 5) & AI literacy (Art. 4)", "Art. 113(a)"),
    ("2025-08-02", "GPAI obligations, governance & penalties", "Art. 113(b)"),
    ("2026-07-27", "Digital Omnibus in force, incl. Art. 4a and Annex I scope changes",
     "Reg. (EU) 2026/1744"),
    ("2026-08-02", "Art. 50 transparency obligations, penalties & Art. 4 supervision",
     "Art. 113"),
    ("2026-12-02", "Art. 5(1)(ba)/(bb) new prohibited practices apply",
     "Art. 113(a)"),
    ("2027-12-02", "High-risk (Annex III) obligations apply (Digital Omnibus date)",
     "Art. 113"),
    ("2028-08-02", "High-risk under Art. 6(1)/Annex I (regulated products)", "Art. 113(c)"),
]


def annex_i_high_risk_trigger(answers):
    """Evaluate the amended Art. 6(1)/(1a)-(1c) Annex I route.

    Saved pre-2026 assessments only have ``hr_safety_component``; retain their
    result.  Once any granular field is present, the legacy screening answer is
    insufficient on its own.
    """
    answers = answers or {}
    detail_fields = {
        "hr_annex_i_relation", "hr_safety_function",
        "hr_failure_endangers_health_safety", "hr_third_party_health_safety",
    }
    if not any(key in answers for key in detail_fields):
        return truthy(answers.get("hr_safety_component"))
    relation = (answers.get("hr_annex_i_relation") or "").strip().lower()
    if not truthy(answers.get("hr_third_party_health_safety")):
        return False
    if relation == "ai_product":
        return True
    return relation == "embedded_component" and (
        truthy(answers.get("hr_safety_function"))
        or truthy(answers.get("hr_failure_endangers_health_safety"))
    )


def annex_i_section_b_only(answers):
    """Whether amended Art. 2(2)'s limited Section-B regime is the only route.

    These systems remain classified through Art. 6(1), but only Art. 6(1),
    Art. 60a and Arts. 102–112 apply (with Arts. 57–59 only insofar as the
    product legislation integrates the high-risk requirements). They must not
    receive the ordinary Chapter III provider/deployer compliance pack.
    """
    answers = answers or {}
    raw_usecases = answers.get("hr_usecases") or []
    if isinstance(raw_usecases, str):
        raw_usecases = [raw_usecases]
    has_annex_iii = any(u and u != "none" for u in raw_usecases)
    return (
        annex_i_high_risk_trigger(answers)
        and str(answers.get("hr_annex_i_section") or "").strip().upper() == "B"
        and not has_annex_iii
    )


def art4_applies(answers, in_scope=True):
    """Whether the recorded actor carries the Art. 4 support-measures duty."""
    answers = answers or {}
    role = str(answers.get("provider_role") or "").strip().lower()
    return (
        in_scope
        and role in ("provider", "deployer", "both")
        and not annex_i_section_b_only(answers)
    )


def applies_from(tier, answers):
    """When the core obligations for THIS system start to apply.

    GPAI-aware: a general-purpose AI model carries Chapter V obligations from
    2 Aug 2025 independently of its risk tier, so a minimal-tier GPAI model has
    a real deadline rather than "no mandatory deadline". This keeps the risk
    report's headline consistent with the obligations & conformity tracker.
    """
    answers = answers or {}
    # The questionnaire now defines gpai_model narrowly: the assessed actor is
    # the GPAI model provider, not merely an integrator of an upstream model.
    gpai = truthy(answers.get("gpai_model"))
    gpai_note = (" GPAI model obligations (Chapter V) additionally apply from "
                 "2 Aug 2025 (Art. 113(b)).")

    if tier == TIER_PROHIBITED:
        old_trigger = any(truthy(answers.get(qid)) for qid in PROHIBITED_PRACTICES)
        new_trigger = any(
            truthy(answers.get(qid)) for qid in CONDITIONAL_PROHIBITED_PRACTICES
        )
        if new_trigger and not old_trigger:
            base = {"date": NEW_ART_5_APPLICATION_DATE,
                    "what": "The Art. 5(1)(ba)/(bb) prohibitions apply from "
                            "2 Dec 2026, subject to Art. 5(1a)/(1b).",
                    "basis": "Art. 113(a)"}
        else:
            base = {"date": "2 Feb 2025",
                    "what": "Prohibition under Art. 5 already applies.",
                    "basis": "Art. 113(a)"}
    elif tier == TIER_HIGH:
        raw_usecases = answers.get("hr_usecases") or []
        if isinstance(raw_usecases, str):
            raw_usecases = [raw_usecases]
        annex_iii = any(u and u != "none" for u in raw_usecases)
        annex_i = annex_i_high_risk_trigger(answers)
        if annex_i_section_b_only(answers):
            base = {"date": "2 Aug 2028",
                    "what": "The Art. 6(1) classification and limited Annex I "
                            "Section B regime in Art. 2(2) apply from 2 Aug 2028; "
                            "the ordinary Chapter III high-risk pack does not apply "
                            "through this route.",
                    "basis": "Art. 113(c)"}
        elif annex_i and annex_iii:
            base = {"date": "2 Dec 2027",
                    "what": "Annex III high-risk obligations apply from 2 Dec 2027; "
                            "the parallel Art. 6(1)/Annex I route applies from "
                            "2 Aug 2028 (Reg. (EU) 2026/1744).",
                    "basis": "Art. 113(c)"}
        elif annex_i:
            base = {"date": "2 Aug 2028",
                    "what": "High-risk obligations for Art. 6(1)/Annex I "
                            "(regulated products); postponed from 2 Aug 2027 "
                            "by Reg. (EU) 2026/1744.",
                    "basis": "Art. 113(c)"}
        else:
            base = {"date": "2 Dec 2027",
                    "what": "High-risk obligations for Annex III systems; "
                            "postponed from 2 Aug 2026 by Reg. (EU) 2026/1744.",
                    "basis": "Art. 113"}
    elif tier == TIER_LIMITED:
        base = {"date": "2 Aug 2026",
                "what": "Transparency obligations (Art. 50) apply (in force).",
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
