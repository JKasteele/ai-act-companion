"""Data governance for AI systems — the layer EU AI Act Art. 10 sits on.

AI governance is built on data governance: you cannot evidence "appropriate
data governance and management practices" (Art. 10(2)) without knowing, per
dataset, where the data came from, who owns it, who stewards it, how it is
classified and how good it is. This module models that vocabulary as data so
the `datagov` report, the DPIA and the gap list all draw on one definition.

Vocabulary follows the DAMA-DMBOK (Data Management Body of Knowledge) knowledge
areas and data-quality dimensions as they are commonly summarised in public
material; no DAMA text is reproduced. The crosswalk rows are Companion-derived
analytical alignments ("most-relevant anchor"), not official mappings.

Sources: Regulation (EU) 2024/1689 Art. 4a, Art. 10 and Art. 26(4); ISO/IEC 42001 Annex
A.7 (titles only); NIST AI RMF 1.0; EIOPA "Artificial Intelligence Governance
Principles" (2021, data governance & record-keeping principle).
"""

from .._normalize import as_list, select_field, truthy

# --- Vocabulary ------------------------------------------------------------
# Origin of a dataset (provenance). (value, label, note)
ORIGINS = [
    ("internal", "Internal (own systems)", "Own operational or master data."),
    ("external_vendor", "External — vendor / licensed",
     "Third-party supplied; contract and DORA/ICT-third-party rules may apply."),
    ("external_public", "External — public / open data", "Public or open datasets."),
    ("partner", "Partner / shared", "Received from a partner under an agreement."),
    ("user_generated", "User-generated / inference-time input",
     "Collected from users at runtime (prompts, uploads, forms)."),
    ("synthetic", "Synthetic / generated", "Generated data; document the generator."),
]

# Confidentiality classification of a dataset. (value, label, note)
CLASSIFICATIONS = [
    ("public", "Public", "No restriction."),
    ("internal", "Internal", "Business data, no personal data."),
    ("confidential", "Confidential", "Commercially sensitive, no personal data."),
    ("personal", "Personal data", "GDPR applies (Art. 6 lawful basis needed)."),
    ("special_category", "Special-category personal data",
     "GDPR Art. 9 (health, biometrics, ethnicity, …); Art. 9(2) condition needed."),
]

# GDPR Art. 6 lawful bases (plus 'n/a' for non-personal data).
LEGAL_BASES = [
    ("na", "Not applicable (no personal data)"),
    ("consent", "Consent (Art. 6(1)(a))"),
    ("contract", "Contract (Art. 6(1)(b))"),
    ("legal_obligation", "Legal obligation (Art. 6(1)(c))"),
    ("vital_interest", "Vital interests (Art. 6(1)(d))"),
    ("public_task", "Public task (Art. 6(1)(e))"),
    ("legitimate_interest", "Legitimate interest (Art. 6(1)(f))"),
    ("unknown", "Unknown / to be determined"),
]

# Status of a data-quality dimension: has it been looked at, and how hard?
QUALITY_STATUS = [
    ("unknown", "Unknown — not assessed"),
    ("assessed", "Assessed qualitatively (reviewed, no metric)"),
    ("measured", "Measured (metric, threshold and evidence exist)"),
    ("na", "Not applicable"),
]

# Data-quality dimensions. (id, name, definition, EU AI Act hook, example metric)
# The six classic DAMA dimensions plus the AI-specific one the AI Act adds.
QUALITY_DIMENSIONS = [
    ("accuracy", "Accuracy",
     "Values correctly describe the real-world object or event.",
     "Art. 10(3): datasets 'free of errors' to the best extent possible.",
     "Error rate against a verified reference sample."),
    ("completeness", "Completeness",
     "Required values are present; missingness is known and handled.",
     "Art. 10(3): datasets 'complete'; Art. 10(2)(e) data availability.",
     "Share of records with all mandatory fields populated."),
    ("consistency", "Consistency",
     "The same fact is represented the same way across datasets and time.",
     "Art. 10(2)(c) data-preparation operations; Art. 10(4) context of use.",
     "Cross-source reconciliation failures per 1,000 records."),
    ("timeliness", "Timeliness",
     "Data is current enough for the decision it feeds.",
     "Art. 10(4): data reflects the specific setting in which the system is used.",
     "Age of the newest record vs. the refresh SLA."),
    ("validity", "Validity",
     "Values conform to the defined format, type and range.",
     "Art. 10(2)(c) cleaning/labelling; Art. 10(3) 'appropriate statistical properties'.",
     "Share of values failing schema or range rules."),
    ("uniqueness", "Uniqueness",
     "No unintended duplicates; one entity is represented once.",
     "Art. 10(2)(f–g): duplicates skew group statistics and bias checks.",
     "Duplicate rate after entity resolution."),
    ("representativeness", "Representativeness & bias screening",
     "The data covers the persons, groups and settings the system will meet.",
     "Art. 10(3) 'sufficiently representative'; Art. 10(2)(f–g) bias examination; "
     "Art. 26(4) deployer duty on input data.",
     "Coverage per (proxy for) protected group vs. the target population."),
]

# Roles in a data-governance operating model. (role, accountability, anchor)
ROLES = [
    ("Data owner", "Accountable for a data domain: access decisions, quality "
                   "targets, retention, lawful use. A business role, not IT.",
     "DAMA-DMBOK data governance; ISO 42001 A.3.2 roles and responsibilities"),
    ("Data steward", "Responsible day to day: definitions, metadata, quality "
                     "monitoring, issue resolution for that domain.",
     "DAMA-DMBOK data stewardship; ISO 42001 A.7.4 quality of data"),
    ("Data custodian", "Operates the platform that stores and moves the data; "
                       "implements the owner's decisions (security, backups, lineage).",
     "DAMA-DMBOK data operations / security"),
    ("AI system owner", "Accountable for the AI system as a product: intended "
                        "purpose, risk classification, conformity, monitoring.",
     "EU AI Act Art. 3 provider/deployer; ISO 42001 A.6"),
    ("Data protection officer", "Advises on and monitors GDPR compliance; consulted "
                                "in the DPIA (Art. 35(2), Art. 39).",
     "GDPR Art. 37–39"),
]

# Crosswalk: (topic, EU AI Act, ISO/IEC 42001, NIST AI RMF, EIOPA principle, DAMA area)
CROSSWALK = [
    ("Roles & accountability", "Art. 10(2), Art. 17(1)(f)", "A.3.2, A.7.2",
     "GOVERN 2.1", "Data governance & record-keeping", "Data governance"),
    ("Dataset inventory & provenance", "Art. 10(2)(b), Art. 11 + Annex IV(2)(d)",
     "A.7.3, A.7.5", "MAP 1.1", "Data governance & record-keeping",
     "Metadata management"),
    ("Classification & lawful basis", "Art. 4a (special categories for bias "
     "detection and correction); GDPR Art. 6/9", "A.7.3", "MEASURE 2.10",
     "Data governance & record-keeping", "Data security / privacy"),
    ("Lineage", "Art. 10(2)(c), Annex IV(2)(d)", "A.7.5, A.7.6", "MAP 2.3",
     "Transparency & explainability", "Data integration & interoperability"),
    ("Quality dimensions", "Art. 10(3), Art. 26(4)", "A.7.4", "MEASURE 2.5",
     "Robustness & performance", "Data quality"),
    ("Representativeness & bias", "Art. 10(2)(f–g), Art. 10(3)", "A.7.4, A.5.4",
     "MEASURE 2.11", "Fairness & non-discrimination", "Data quality"),
    ("Retention & purpose limitation", "Art. 4a(1)(e), Art. 12; GDPR Art. 5(1)(b),(e)",
     "A.7.2", "GOVERN 1.1", "Data governance & record-keeping",
     "Data governance / lifecycle"),
]

PROVENANCE = (
    "Crosswalk rows are a Companion-derived analytical alignment, not an official "
    "mapping. DAMA-DMBOK terms are used as commonly summarised in public material; "
    "EIOPA principles per 'Artificial Intelligence Governance Principles' (2021)."
)

# Intake ids for the quality dimensions (section 11 of the questionnaire).
QUALITY_FIELDS = [(f"dg_q_{dim_id}", dim_id) for dim_id, *_rest in QUALITY_DIMENSIONS]

DATASET_COLUMNS = ["name", "origin", "owner", "steward", "classification",
                   "purpose", "retention", "legal_basis"]

_LABELS = {
    "origin": dict((v, lab) for v, lab, _n in ORIGINS),
    "classification": dict((v, lab) for v, lab, _n in CLASSIFICATIONS),
    "legal_basis": dict(LEGAL_BASES),
    "status": dict(QUALITY_STATUS),
}


def label(kind, value):
    """Human label for a vocabulary value (falls back to the raw value)."""
    return _LABELS.get(kind, {}).get(value, value or "-")


# --- Normalised views over the intake --------------------------------------
def dataset_rows(answers):
    """The `dg_datasets` table as a list of dicts with every column present.

    Accepts a list of dicts (the form/API shape) and tolerates a single dict.
    Rows with no name AND no origin are dropped as empty."""
    rows = []
    for raw in as_list((answers or {}).get("dg_datasets")):
        if not isinstance(raw, dict):
            continue
        row = {c: str(raw.get(c) or "").strip() for c in DATASET_COLUMNS}
        for c in ("origin", "classification", "legal_basis"):
            row[c] = row[c].lower()
        if row["name"] or row["origin"]:
            rows.append(row)
    return rows


def quality_rows(answers):
    """One row per quality dimension with the intake status attached."""
    answers = answers or {}
    out = []
    for field, dim_id in QUALITY_FIELDS:
        status = select_field(answers, field) or "unknown"
        dim = next(d for d in QUALITY_DIMENSIONS if d[0] == dim_id)
        out.append({"id": dim_id, "name": dim[1], "definition": dim[2],
                    "hook": dim[3], "metric": dim[4], "status": status})
    return out


def gaps(answers, tier="minimal"):
    """Deterministic gap list: (severity, gap, action, ref). Severity is
    'high' | 'medium' | 'low'. High-risk systems are held to Art. 10; others to
    GDPR Art. 5 accuracy and good practice, so severities are one notch lower."""
    answers = answers or {}
    high = tier == "high"
    role = select_field(answers, "provider_role")
    hi, med = ("high", "medium") if high else ("medium", "low")
    out = []
    rows = dataset_rows(answers)
    personal = truthy(answers.get("data_personal"))
    special = truthy(answers.get("data_special_category"))

    if not rows:
        if role == "deployer":
            out.append((hi, "No input-data inventory.",
                        "List the input datasets under the deployer's control and obtain "
                        "the provider's Art. 13 data description; do not claim ownership "
                        "of the provider's training, validation or test data.",
                        "Art. 26(4), Art. 13(3)(b)"))
        else:
            out.append((hi, "No dataset inventory.",
                        "List every training, validation, test and inference-time "
                        "dataset with origin, owner, steward and classification.",
                        "Art. 10(2)(b), Annex IV(2)(d)"))
    for r in rows:
        nm = r["name"] or "(unnamed dataset)"
        if not r["owner"]:
            out.append((med, f"'{nm}': no data owner.",
                        "Assign an accountable business owner for the data domain.",
                        "Art. 10(2); ISO 42001 A.3.2"))
        if not r["steward"]:
            out.append(("low", f"'{nm}': no data steward.",
                        "Name the steward who maintains definitions, metadata and "
                        "quality for this dataset.", "DAMA-DMBOK stewardship"))
        if not r["origin"]:
            out.append((med, f"'{nm}': origin not recorded.",
                        "Record provenance (internal / vendor / public / user / "
                        "synthetic) and the collection process.",
                        "Art. 10(2)(b); ISO 42001 A.7.5"))
        if r["classification"] in ("personal", "special_category") and \
                r["legal_basis"] in ("", "unknown", "na"):
            out.append(("high", f"'{nm}': personal data without a recorded lawful basis.",
                        "Determine and record the GDPR Art. 6 basis (and the Art. 9(2) "
                        "condition for special categories).", "GDPR Art. 6, Art. 9"))
        if r["classification"] == "special_category" and not special:
            out.append((med, f"'{nm}': classified special-category, but the intake says "
                        "no special categories are processed.",
                        "Reconcile the dataset classification with section 6 of the "
                        "intake; the DPIA and bias plan depend on it.",
                        "GDPR Art. 9; Art. 4a"))
        if not r["retention"]:
            out.append(("low", f"'{nm}': no retention period.",
                        "Set a retention period and deletion rule; Art. 12 logs "
                        "have their own minimum (6 months, Art. 19/26(6)).",
                        "GDPR Art. 5(1)(e); Art. 19"))
    if personal and rows and not any(r["classification"] in ("personal", "special_category")
                                     for r in rows):
        out.append((med, "Intake says personal data is processed, but no dataset is "
                    "classified as personal.",
                    "Classify the datasets that carry personal data.",
                    "GDPR Art. 30 record of processing"))

    owner = str(answers.get("dg_data_owner") or "").strip()
    sys_owner = str(answers.get("sys_owner") or "").strip()
    if not owner:
        out.append((med, "No system-level data owner named.",
                    "Name the data owner distinct from the AI system owner; the two "
                    "roles carry different accountabilities.", "Art. 10(2); Art. 17(1)(f)"))
    elif sys_owner and owner.lower() == sys_owner.lower():
        out.append(("low", "Data owner equals the system owner.",
                    "Confirm this is a deliberate choice; in most operating models the "
                    "data domain is owned by the business function that produces the "
                    "data, not by the system team.", "DAMA-DMBOK data governance"))
    if not truthy(answers.get("dg_catalog_registered")):
        out.append(("low", "Datasets not registered in a data catalogue / metadata store.",
                    "Register them so lineage, definitions and owners are discoverable.",
                    "Annex IV(2)(d); DAMA metadata management"))
    if not str(answers.get("dg_lineage") or "").strip():
        out.append((med, "No lineage recorded (source → preparation → training/input "
                    "set → model → output).",
                    "Document the lineage chain; it is the backbone of the Annex IV "
                    "data description and of any drift investigation.",
                    "Art. 10(2)(c); Annex IV(2)(d)"))
    for q in quality_rows(answers):
        if q["status"] == "unknown":
            sev = hi if q["id"] == "representativeness" else med
            out.append((sev, f"Quality dimension '{q['name']}' not assessed.",
                        f"Assess it; suggested metric: {q['metric']}", q["hook"]))
        elif q["status"] == "assessed" and high:
            out.append(("low", f"'{q['name']}' assessed but not measured.",
                        "For a high-risk system, back the judgement with a metric, a "
                        "threshold and dated evidence.", "Art. 10(3), Art. 11"))
    order = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda g: order[g[0]])
    return out


def summary(answers, tier="minimal"):
    """Structured view for the API / MCP: inventory, quality and gaps."""
    rows = dataset_rows(answers)
    g = gaps(answers, tier)
    return {
        "datasets": rows,
        "dataset_count": len(rows),
        "quality": quality_rows(answers),
        "gaps": [{"severity": s, "gap": gap, "action": act, "ref": ref}
                 for s, gap, act, ref in g],
        "gap_counts": {lvl: sum(1 for s, *_r in g if s == lvl)
                       for lvl in ("high", "medium", "low")},
    }
