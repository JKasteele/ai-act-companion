"""Mainstream security frameworks: NIST CSF 2.0 + ISO/IEC 27001:2022, and a
Framework Integration Matrix that bridges the AI-governance lenses (NIST AI RMF,
EU AI Act, OWASP LLM Top 10, MITRE ATLAS) to the frameworks that security
reviewers and ISMS auditors actually use.

Provenance / honesty:
  * NIST CSF 2.0 function and category identifiers are public.
  * ISO/IEC 27001:2022 entries reproduce only the public Annex A control
    *titles* — never the paid standard body text.
  * The integration matrix is a Companion-derived analytical alignment, NOT an
    official published crosswalk. See PROVENANCE; ship it in any rendered output.
"""

# (code, name, intent, example categories) — NIST CSF 2.0.
CSF_FUNCTIONS = [
    ("GV", "Govern",
     "Establish and monitor the cybersecurity risk-management strategy, "
     "expectations and policy.",
     "GV.RM, GV.PO, GV.OV, GV.RR"),
    ("ID", "Identify",
     "Understand assets, suppliers and the related cybersecurity risks.",
     "ID.AM, ID.RA"),
    ("PR", "Protect",
     "Use safeguards to manage cybersecurity risks to assets.",
     "PR.AA, PR.DS"),
    ("DE", "Detect",
     "Find and analyse possible cybersecurity attacks and compromises.",
     "DE.CM, DE.AE"),
    ("RS", "Respond",
     "Take action regarding a detected cybersecurity incident.",
     "RS.MA, RS.AN"),
    ("RC", "Recover",
     "Restore assets and operations affected by a cybersecurity incident.",
     "RC.RP"),
]

# (control id, title) — ISO/IEC 27001:2022 Annex A, public titles only.
ISO_27001_2022 = [
    ("A.5.1", "Policies for information security"),
    ("A.5.7", "Threat intelligence"),
    ("A.5.9", "Inventory of information and other associated assets"),
    ("A.5.10", "Acceptable use of information and other associated assets"),
    ("A.5.12", "Classification of information"),
    ("A.5.24", "Information security incident management planning and preparation"),
    ("A.5.26", "Response to information security incidents"),
    ("A.5.29", "Information security during disruption"),
    ("A.5.30", "ICT readiness for business continuity"),
    ("A.5.31", "Legal, statutory, regulatory and contractual requirements"),
    ("A.8.15", "Logging"),
    ("A.8.16", "Monitoring activities"),
    ("A.8.25", "Secure development life cycle"),
    ("A.8.26", "Application security requirements"),
    ("A.8.28", "Secure coding"),
]

ISO_27001_TITLES = dict(ISO_27001_2022)

# One row per CSF function. `ai_act_refs` are tokens linkified via ref_url().
INTEGRATION_MATRIX = [
    {"csf": "Govern (GV)", "iso": ["A.5.1", "A.5.10", "A.5.31"],
     "nist_ai_rmf": "Govern", "owasp": "—", "atlas": "—",
     "ai_act_refs": ["Art. 9", "Art. 13", "Art. 14", "Art. 26"]},
    {"csf": "Identify (ID)", "iso": ["A.5.7", "A.5.9", "A.5.12"],
     "nist_ai_rmf": "Map", "owasp": "—", "atlas": "Reconnaissance",
     "ai_act_refs": ["Art. 9"]},
    {"csf": "Protect (PR)", "iso": ["A.8.25", "A.8.26", "A.8.28"],
     "nist_ai_rmf": "Manage", "owasp": "LLM01–LLM08",
     "atlas": "AI Attack Staging (formerly ML Attack Staging)",
     "ai_act_refs": ["Art. 10", "Art. 15"]},
    {"csf": "Detect (DE)", "iso": ["A.8.15", "A.8.16"],
     "nist_ai_rmf": "Measure", "owasp": "—", "atlas": "Defense Evasion",
     "ai_act_refs": ["Art. 72"]},
    {"csf": "Respond (RS)", "iso": ["A.5.24", "A.5.26"],
     "nist_ai_rmf": "Manage", "owasp": "—", "atlas": "Impact",
     "ai_act_refs": ["Art. 73", "Art. 26"]},
    {"csf": "Recover (RC)", "iso": ["A.5.29", "A.5.30"],
     "nist_ai_rmf": "Manage", "owasp": "—", "atlas": "—", "ai_act_refs": []},
]

PROVENANCE = (
    "This Framework Integration Matrix is a Companion-derived analytical "
    "alignment across NIST CSF 2.0, ISO/IEC 27001:2022, NIST AI RMF, the OWASP "
    "Top 10 for LLM Applications, MITRE ATLAS and the EU AI Act — not an official "
    "published crosswalk. ISO/IEC 27001 entries reproduce only the public Annex A "
    "control titles, not the paid standard text."
)
