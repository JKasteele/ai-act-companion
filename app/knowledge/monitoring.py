"""Post-market monitoring knowledge base.

The six monitoring categories are taken from NIST AI 800-4, *Challenges to the
Monitoring of Deployed AI Systems* (March 2026, DOI 10.6028/NIST.AI.800-4),
Section 2; the five cross-cutting challenges from Section 3.1. The category and
challenge titles are reproduced verbatim from that publication.

How these are organised into an EU AI Act post-market monitoring plan (Art. 72)
is a Companion-derived structure, not an official AI Act template — see
PROVENANCE. Identifiers were verified against the primary NIST PDF.
"""

# (id, title, what it monitors). Titles verbatim from NIST AI 800-4 §2.
CATEGORIES = [
    ("functionality", "Functionality Monitoring",
     "Does the system still work as intended? Accuracy, performance drift and "
     "degradation over time."),
    ("operational", "Operational Monitoring",
     "Infrastructure consistency, uptime, latency, resource use and cost."),
    ("human_factors", "Human Factors Monitoring",
     "Quality of human–AI interaction, transparency, user feedback and "
     "over-/under-reliance."),
    ("security", "Security Monitoring",
     "Adversarial attacks, misuse, and prompt-injection / jailbreak / "
     "exfiltration detection."),
    ("compliance", "Compliance Monitoring",
     "Regulatory adherence (EU AI Act, GDPR), policy compliance and "
     "transparency disclosure (Art. 50)."),
    ("large_scale_impacts", "Large-Scale Impacts Monitoring",
     "Downstream and societal effects as the system scales or becomes "
     "safety-relevant."),
]

COLUMNS = ["Metric / signal", "Baseline", "Threshold / trigger",
           "Data source", "Review cadence", "Owner"]

# Cross-cutting challenges, verbatim from NIST AI 800-4 §3.1 (Table 2).
CROSS_CUTTING = [
    "Trusted Methods and Tools",
    "Visibility and Transparency",
    "Pace of Change",
    "Incentives and Organizational Culture",
    "Resource Requirements",
]

PROVENANCE = (
    "The six monitoring categories and five cross-cutting challenges are taken "
    "from NIST AI 800-4, 'Challenges to the Monitoring of Deployed AI Systems' "
    "(March 2026, DOI 10.6028/NIST.AI.800-4). Organising them into an EU AI Act "
    "Art. 72 post-market monitoring plan is a Companion-derived structure, not an "
    "official AI Act template."
)

# Annex III areas where outcome drift across groups is a primary functionality
# signal (decisions about people).
_DRIFT_USECASES = {"employment", "essential_services", "education",
                   "law_enforcement", "migration_border", "justice_democracy"}


def _truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "ja", "on", "1"}
    return bool(value)


def seeded_rows(answers):
    """Return {category_id: [row, ...]} seeded deterministically from structured
    answers only (never free-text). A row is a dict keyed like COLUMNS."""
    answers = answers or {}
    rows = {cid: [] for cid, _t, _w in CATEGORIES}

    def row(metric, **kw):
        r = {c: "" for c in COLUMNS}
        r["Metric / signal"] = metric
        for k, v in kw.items():
            r[k] = v
        return r

    if _truthy(answers.get("sec_is_llm")):
        rows["security"].append(row(
            "Prompt-injection / jailbreak attempts",
            **{"Threshold / trigger": "any successful bypass",
               "Data source": "guardrail / input-filter logs"}))

    usecases = answers.get("hr_usecases") or []
    if isinstance(usecases, str):
        usecases = [usecases]
    if any(u in _DRIFT_USECASES for u in usecases):
        rows["functionality"].append(row(
            "Outcome drift across protected groups",
            **{"Threshold / trigger": "disparity beyond agreed fairness bound",
               "Review cadence": "quarterly"}))

    # Always seed a compliance row pointing at the obligations tracker.
    rows["compliance"].append(row(
        "Obligations status (see compliance tracker)",
        **{"Data source": "conformity tracker", "Review cadence": "quarterly"}))
    return rows
