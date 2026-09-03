"""Post-market monitoring knowledge base.

The six monitoring categories are taken from NIST AI 800-4, *Challenges to the
Monitoring of Deployed AI Systems* (March 2026, DOI 10.6028/NIST.AI.800-4),
Section 2; the five cross-cutting challenges from Section 3.1. The category and
challenge titles are reproduced verbatim from that publication.

How these are organised into an EU AI Act post-market monitoring plan (Art. 72)
is a Companion-derived structure, not an official AI Act template — see
PROVENANCE. Identifiers were verified against the primary NIST PDF.
"""

from .._normalize import truthy as _truthy

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


# Review cadence per risk tier (Companion-derived good practice; the AI Act sets
# no fixed interval, but Art. 9(2) and Art. 72 imply a periodic review).
CADENCE_BY_TIER = {"prohibited": "immediately — stop use", "high": "monthly KPIs, "
                   "6-monthly review", "limited": "quarterly KPIs, annual review",
                   "minimal": "annual"}


def cadence_for(tier):
    return CADENCE_BY_TIER.get(tier or "", "annual")


def seeded_rows(answers, tier=None):
    """Return {category_id: [row, ...]} seeded deterministically from structured
    answers only (never free-text). A row is a dict keyed like COLUMNS. `tier`
    (from the classifier) sets the review cadence and adds the KPI rows that
    supervisors expect for decisions about people."""
    answers = answers or {}
    rows = {cid: [] for cid, _t, _w in CATEGORIES}
    cadence = cadence_for(tier)

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

    # KPI rows: performance vs. baseline, oversight, incidents and complaints.
    rows["functionality"].append(row(
        "Primary performance metric vs. release baseline",
        **{"Baseline": "value at release", "Threshold / trigger": "agreed tolerance "
           "band; breach -> re-validation", "Data source": "evaluation pipeline",
           "Review cadence": cadence}))
    rows["functionality"].append(row(
        "Input / output drift (distribution shift)",
        **{"Threshold / trigger": "drift statistic above alert level",
           "Data source": "monitoring platform", "Review cadence": cadence}))
    autonomy = str(answers.get("autonomy_level") or "").strip().lower()
    if autonomy in ("advisory", "human_in_the_loop", "human_on_the_loop"):
        rows["human_factors"].append(row(
            "Override rate (human deviates from model advice)",
            **{"Baseline": "rate at release", "Threshold / trigger": "near 0% = "
               "automation bias; sharp rise = model or data problem",
               "Data source": "workflow / case system (override log)",
               "Review cadence": cadence}))
    rows["compliance"].append(row(
        "Complaints, objections and requests for human intervention",
        **{"Threshold / trigger": "any complaint alleging discrimination",
           "Data source": "complaints register", "Review cadence": cadence}))
    rows["compliance"].append(row(
        "Incidents and near-misses (Art. 73 screening)",
        **{"Threshold / trigger": "any Art. 3(49) limb -> incident report",
           "Data source": "incident register", "Review cadence": cadence}))
    # Always seed a compliance row pointing at the obligations tracker.
    rows["compliance"].append(row(
        "Obligations status (see compliance tracker)",
        **{"Data source": "conformity tracker", "Review cadence": cadence}))
    return rows
