"""NIST AI Risk Management Framework (AI RMF 1.0) as a knowledge base + crosswalk.

The AI RMF has four core functions - GOVERN, MAP, MEASURE, MANAGE - with
categories and subcategories. We model a relevant subset and provide a crosswalk
to EU AI Act obligations, so the report links both frameworks.
"""

FUNCTIONS = {
    "GOVERN": "Culture, policy, roles and processes for AI risk management.",
    "MAP": "Establish context and map risks.",
    "MEASURE": "Analyse, assess and monitor risks (quantitative/qualitative).",
    "MANAGE": "Prioritise, treat and continuously follow up on risks.",
}

# Curated subcategories that directly relate to AI Act obligations.
# (id, function, description, linked AI Act reference)
SUBCATEGORIES = [
    ("GOVERN 1.1", "GOVERN",
     "Legal and regulatory requirements involving AI are understood, managed and documented.",
     "EU AI Act Art. 9, Art. 16"),
    ("GOVERN 1.2", "GOVERN",
     "A trustworthy AI risk management process is established and maintained.",
     "EU AI Act Art. 9, Art. 17"),
    ("GOVERN 2.1", "GOVERN",
     "Roles, responsibilities and lines of authority for AI risk are assigned.",
     "EU AI Act Art. 14, Art. 26"),
    ("GOVERN 4.1", "GOVERN",
     "An organisation-wide culture of risk awareness and critical thinking is in place.",
     "EU AI Act Art. 4 (AI literacy)"),
    ("MAP 1.1", "MAP",
     "Intended purpose, context of use and relevant parties are documented.",
     "EU AI Act Art. 11 + Annex IV"),
    ("MAP 2.3", "MAP",
     "Scientific integrity and potential negative impacts are mapped.",
     "EU AI Act Art. 9(2)"),
    ("MAP 5.1", "MAP",
     "Potential positive and negative impacts on individuals/groups/society are identified.",
     "EU AI Act Art. 27 (FRIA)"),
    ("MEASURE 2.5", "MEASURE",
     "The system is validated for reliability, robustness and accuracy.",
     "EU AI Act Art. 15"),
    ("MEASURE 2.7", "MEASURE",
     "Safety and security (resilience) are evaluated.",
     "EU AI Act Art. 15"),
    ("MEASURE 2.11", "MEASURE",
     "Fairness and bias - including harmful bias - are evaluated.",
     "EU AI Act Art. 10(2)(f-g)"),
    ("MEASURE 2.8", "MEASURE",
     "Transparency and explainability are assessed.",
     "EU AI Act Art. 13, Art. 50"),
    ("MANAGE 1.3", "MANAGE",
     "Risks are prioritised and assigned a treatment strategy.",
     "EU AI Act Art. 9(5)"),
    ("MANAGE 2.3", "MANAGE",
     "Mechanisms for human oversight and intervention are operational.",
     "EU AI Act Art. 14"),
    ("MANAGE 4.1", "MANAGE",
     "Post-deployment monitoring and incident response are in place.",
     "EU AI Act Art. 72, Art. 73"),
]


def crosswalk_for_tier(tier):
    """Return the relevant NIST subcategories per risk tier.

    GOVERN/MAP always apply; MEASURE/MANAGE depth scales with the risk tier.
    """
    from .eu_ai_act import TIER_HIGH, TIER_LIMITED, TIER_PROHIBITED

    base = {"GOVERN 1.1", "GOVERN 4.1", "MAP 1.1", "MAP 5.1"}
    if tier in (TIER_LIMITED,):
        base |= {"MEASURE 2.8"}
    if tier in (TIER_HIGH, TIER_PROHIBITED):
        base |= {
            "GOVERN 1.2", "GOVERN 2.1", "MAP 2.3",
            "MEASURE 2.5", "MEASURE 2.7", "MEASURE 2.11", "MEASURE 2.8",
            "MANAGE 1.3", "MANAGE 2.3", "MANAGE 4.1",
        }
    return [s for s in SUBCATEGORIES if s[0] in base]
