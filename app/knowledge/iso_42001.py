"""ISO/IEC 42001:2023 (AI management system) structure + EU AI Act crosswalk.

Only the publicly-published structure is modelled here - the management clauses
(4-10), the Annex A control CATEGORIES (A.2-A.10) and the individual Annex A
control *titles* (38 controls). No proprietary control text is reproduced (titles
only, exactly as for the ISO/IEC 27001 titles in security_frameworks.py).

The crosswalks below are an analytical alignment, NOT an official mapping:
ISO/IEC 42001 is an organisational management-system standard, whereas the EU AI
Act imposes product/high-risk-system obligations. Treat each row as the
"most-relevant anchor", not an equivalence.

The Annex A control list was cross-verified against multiple public summaries
(the depth at which third-party summaries diverge); the 38-control list and the
A.6.1.x / A.6.2.x life-cycle sub-structure here match the standard's own count.
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

# The 38 Annex A reference controls: (id, public title, most-relevant EU AI Act
# article token(s)). Titles only; the AI Act anchor is a Companion-derived
# analytical alignment ("most-relevant anchor", not an equivalence).
ANNEX_A_CONTROLS = [
    ("A.2.2", "AI policy", ["Art. 17"]),
    ("A.2.3", "Alignment with other organizational policies", ["Art. 17"]),
    ("A.2.4", "Review of the AI policy", ["Art. 17", "Art. 72"]),
    ("A.3.2", "AI roles and responsibilities", ["Art. 17", "Art. 26"]),
    ("A.3.3", "Reporting of concerns", ["Art. 26", "Art. 73"]),
    ("A.4.2", "Resource documentation", ["Art. 11"]),
    ("A.4.3", "Data resources", ["Art. 10"]),
    ("A.4.4", "Tooling resources", ["Art. 15"]),
    ("A.4.5", "System and computing resources", ["Art. 15"]),
    ("A.4.6", "Human resources", ["Art. 14"]),
    ("A.5.2", "AI system impact assessment process", ["Art. 9", "Art. 27"]),
    ("A.5.3", "Documentation of AI system impact assessments", ["Art. 11", "Art. 27"]),
    ("A.5.4", "Assessing AI system impact on individuals or groups of individuals",
     ["Art. 27"]),
    ("A.5.5", "Assessing societal impacts of AI systems", ["Art. 9", "Art. 27"]),
    ("A.6.1.2", "Objectives for responsible development of AI system", ["Art. 9"]),
    ("A.6.1.3", "Processes for responsible design and development of AI systems",
     ["Art. 9", "Art. 15"]),
    ("A.6.2.2", "AI system requirements and specification", ["Art. 11"]),
    ("A.6.2.3", "Documentation of AI system design and development",
     ["Art. 11"]),
    ("A.6.2.4", "AI system verification and validation", ["Art. 15"]),
    ("A.6.2.5", "AI system deployment", ["Art. 26"]),
    ("A.6.2.6", "AI system operation and monitoring", ["Art. 72", "Art. 26"]),
    ("A.6.2.7", "AI system technical documentation", ["Art. 11"]),
    ("A.6.2.8", "AI system recording of event logs", ["Art. 12"]),
    ("A.7.2", "Data for development and enhancement of AI system", ["Art. 10"]),
    ("A.7.3", "Acquisition of data", ["Art. 10"]),
    ("A.7.4", "Quality of data for AI systems", ["Art. 10"]),
    ("A.7.5", "Data provenance", ["Art. 10"]),
    ("A.7.6", "Data preparation", ["Art. 10"]),
    ("A.8.2", "System documentation and information for users", ["Art. 13"]),
    ("A.8.3", "External reporting", ["Art. 73"]),
    ("A.8.4", "Communication of incidents", ["Art. 73"]),
    ("A.8.5", "Information for interested parties", ["Art. 13", "Art. 50"]),
    ("A.9.2", "Processes for responsible use of AI systems", ["Art. 26"]),
    ("A.9.3", "Objectives for responsible use of AI system", ["Art. 26"]),
    ("A.9.4", "Intended use of the AI system", ["Art. 13", "Art. 26"]),
    ("A.10.2", "Allocating responsibilities", ["Art. 25", "Art. 26"]),
    ("A.10.3", "Suppliers", ["Art. 25"]),
    ("A.10.4", "Customers", ["Art. 13", "Art. 26"]),
]


def annex_a_category(control_id):
    """Map a control id (e.g. 'A.6.2.8') to its Annex A category ('A.6')."""
    parts = control_id.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else control_id

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
    "product/high-risk obligations. Clauses (4-10), category headers (A.2-A.10) and "
    "the 38 Annex A control titles are publicly published (titles only, no paid "
    "standard text); each control's EU AI Act anchor is the Companion's "
    "most-relevant alignment, not an equivalence."
)
