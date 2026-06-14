"""ISO/IEC 42001:2023 (AI management system) structure + EU AI Act crosswalk.

Only the publicly-published structural skeleton is modelled here - the
management clauses (4-10) and the Annex A control CATEGORIES (A.2-A.10). No
proprietary control text is reproduced, and individual Annex A sub-control
numbers are deliberately NOT hard-coded (third-party summaries disagree at that
depth).

The crosswalk below is an analytical alignment, NOT an official mapping:
ISO/IEC 42001 is an organisational management-system standard, whereas the EU AI
Act imposes product/high-risk-system obligations. Treat each row as the
"most-relevant anchor", not an equivalence.
"""

# Auditable management-system clauses (Annex SL high-level structure).
CLAUSES = {
    "4": "Context of the organization",
    "5": "Leadership",
    "6": "Planning",
    "7": "Support",
    "8": "Operation",
    "9": "Performance evaluation",
    "10": "Improvement",
}

# Annex A reference-control categories (38 controls across these 9 groups).
ANNEX_A = {
    "A.2": "Policies related to AI",
    "A.3": "Internal organization",
    "A.4": "Resources for AI systems",
    "A.5": "Assessing impacts of AI systems",
    "A.6": "AI system life cycle",
    "A.7": "Data for AI systems",
    "A.8": "Information for interested parties of AI systems",
    "A.9": "Use of AI systems",
    "A.10": "Third-party and customer relationships",
}

# (EU AI Act article, ISO/IEC 42001 anchor, note)
CROSSWALK = [
    ("Art. 9 (risk management)", "Clause 6.1.2 / 6.1.3", "AI risk assessment & treatment."),
    ("Art. 10 (data governance)", "Annex A.7", "Data for AI systems."),
    ("Art. 11 + Annex IV (technical documentation)", "Clause 7.5 + Annex A.6",
     "Documented information; life-cycle documentation."),
    ("Art. 12 (logging)", "Clause 9.1 + Annex A.6",
     "Partial - Art. 12 mandates automatic event logging."),
    ("Art. 13 (transparency to deployers)", "Annex A.8", "Information for interested parties."),
    ("Art. 14 (human oversight)", "Annex A.9", "Use of AI systems."),
    ("Art. 15 (accuracy/robustness/cybersecurity)", "Annex A.6 (+ ISO/IEC 27001)",
     "Verification/validation/monitoring; cyber often paired with 27001."),
    ("Art. 17 (quality management system)", "Clauses 4-10 (the AIMS)",
     "Closest structural analogue; still partial."),
    ("Art. 27 (FRIA)", "Clause 6.1.4 + Annex A.5",
     "Impact assessment - broader than the fundamental-rights-scoped FRIA."),
    ("Art. 72 (post-market monitoring)", "Clause 9 + Clause 10",
     "Moderate; 42001 has no AI Act-style post-market monitoring plan."),
]

PROVENANCE = (
    "Analytical alignment, not an official ISO <-> EU AI Act crosswalk. ISO/IEC "
    "42001 is an organisational AI management-system standard; the AI Act imposes "
    "product/high-risk obligations. Category headers (A.2-A.10) and clauses (4-10) "
    "are publicly published; individual sub-control numbers are not asserted."
)
