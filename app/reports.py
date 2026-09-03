"""Report generators: risk assessment, DPIA skeleton, bias audit checklist.

All output is Markdown (the canonical export). The frontend renders it to HTML
for preview/print. No external templating dependency: we build the Markdown with
Python strings, fed by the classifier output.
"""

from . import __version__
from ._normalize import select_field as _select
from ._normalize import truthy as _truthy
from .controls import generate_control_catalog
from .data_security import assess_data_security
from .incident import assess_incident
from .knowledge import ai_security as sec
from .knowledge import data_governance as dg
from .knowledge import data_security as ds
from .knowledge import eu_ai_act as eu
from .knowledge import iso_42001 as iso
from .knowledge import monitoring as mon
from .knowledge import security_frameworks as sfw
from .modelcard import generate_model_card
from .redteam import generate_test_plan
from .security import SEVERITY_ORDER, assess_security
from .stride import generate_stride_model

# Single source of truth for the report catalogue: (type, human label). The API
# (/api/config), the frontend tabs and the MCP tool all derive from this, so a
# new report type is added in one place. A guard test (tests/test_mcp.py) asserts
# the MCP Literal stays in sync with REPORT_TYPES.
REPORT_CATALOG = (
    ("risk", "Risk assessment"),
    ("dpia", "DPIA skeleton"),
    ("bias", "Bias checklist"),
    ("security", "AI security"),
    ("fria", "FRIA"),
    ("techdoc", "Technical documentation"),
    ("compliance", "Compliance tracker"),
    ("monitoring", "Post-market monitoring"),
    ("framework-matrix", "Framework matrix"),
    ("redteam", "Red-team plan"),
    ("controls", "Control catalogue"),
    ("datasec", "Data security"),
    ("stride", "STRIDE threat model"),
    ("incident", "Serious incident"),
    ("modelcard", "Model card"),
    ("doc", "Declaration of conformity"),
    ("registration", "EU-database registration"),
    ("gpai", "GPAI obligations"),
    ("datagov", "Data governance"),
)
REPORT_TYPES = tuple(rtype for rtype, _label in REPORT_CATALOG)


# --- helpers ---------------------------------------------------------------
def _safe(text):
    """Neutralise a free-text answer before interpolating it into Markdown.

    Classification is unaffected — the tier is a pure function of structured
    fields — but the generated *documents* interpolate free-text (description,
    intended purpose, oversight notes, data sources). Collapse line breaks so a
    multi-line answer cannot inject Markdown structure (new headings, list items
    or table rows), and escape pipes so it cannot break out of a table cell. The
    frontend additionally HTML-escapes on render, covering the preview path.
    """
    s = str(text).replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return s.replace("|", "\\|")


def _a(answers, key, default="-"):
    val = answers.get(key)
    if val is None or val == "":
        return default
    if isinstance(val, bool):
        return "Yes" if val else "No"
    if isinstance(val, list):
        return _safe(", ".join(str(v) for v in val)) if val else default
    return _safe(val)


def _bool(answers, key):
    # Same coercion as the classifier, so a report never disagrees with the tier
    # about whether a field like data_personal was answered "yes".
    return _truthy(answers.get(key))


def _header(assessment):
    return (
        f"_Assessment id: `{assessment.get('id', '-')}` · "
        f"Generated: {assessment.get('created_at', '-')} · "
        f"AI Act Companion v{__version__} · "
        f"Knowledge base {eu.KNOWLEDGE_VERSION} (reviewed {eu.LAST_REVIEWED}, "
        f"incl. Reg. (EU) 2026/1744)_\n\n"
        f"> {eu.DISCLAIMER}\n"
    )


def _ref_link(ref):
    """Render a citation as a Markdown link to the AI Act Explorer when resolvable."""
    url = eu.ref_url(ref)
    return f"[{ref}]({url})" if url else ref


def _refs(refs):
    return ", ".join(_ref_link(r) for r in refs)


def _findings_block(findings):
    if not findings:
        return "_None._\n"
    lines = []
    for f in findings:
        lines.append(f"- **{f.get('title','')}** ({_refs(f.get('refs', []))}) — {f.get('rationale','')}")
    return "\n".join(lines) + "\n"


def _timeline_table():
    rows = ["| Date | What applies | Basis |", "|---|---|---|"]
    for date, what, basis in eu.TIMELINE:
        rows.append(f"| {date} | {what} | {_ref_link(basis)} |")
    notes = [f"_As amended by [{name}]({url}): {what}_"
             for name, what, url in eu.AMENDMENTS]
    return "\n".join(rows) + "\n\n" + "\n".join(notes) + "\n"


def _iso_table():
    rows = ["| EU AI Act | ISO/IEC 42001 anchor | Note |", "|---|---|---|"]
    for art, anchor, note in iso.CROSSWALK:
        rows.append(f"| {_ref_link(art)} | {anchor} | {note} |")
    return "\n".join(rows) + "\n"


def _iso_annex_a_table():
    """Map the 38 ISO/IEC 42001 Annex A controls to their most-relevant EU AI
    Act article(s). Titles only; the AI Act anchor is an analytical alignment."""
    rows = ["| Annex A | Control (title) | Most-relevant EU AI Act |",
            "|---|---|---|"]
    for cid, title, refs in iso.ANNEX_A_CONTROLS:
        cat = iso.ANNEX_A.get(iso.annex_a_category(cid), "")
        rows.append(f"| {cid} | {title} _({cat})_ | {_refs(refs)} |")
    return "\n".join(rows) + "\n"


def _nist_table(crosswalk):
    rows = ["| NIST subcategory | Function | Description | EU AI Act |",
            "|---|---|---|---|"]
    for sub in crosswalk:
        # sub = [id, function, description, ai_act_ref]
        rows.append(f"| {sub[0]} | {sub[1]} | {sub[2]} | {sub[3]} |")
    return "\n".join(rows) + "\n"


def _framework_matrix_table():
    rows = ["| CSF 2.0 | ISO 27001:2022 | NIST AI RMF | OWASP LLM | MITRE ATLAS | EU AI Act |",
            "|---|---|---|---|---|---|"]
    for m in sfw.INTEGRATION_MATRIX:
        iso_cell = ", ".join(m["iso"]) or "—"
        ai_act = _refs(m["ai_act_refs"]) if m["ai_act_refs"] else "—"
        rows.append(f"| {m['csf']} | {iso_cell} | {m['nist_ai_rmf']} | "
                    f"{m['owasp']} | {m['atlas']} | {ai_act} |")
    return "\n".join(rows) + "\n"


# --- 1. AI risk assessment -------------------------------------------------
def render_risk_assessment(assessment):
    answers = assessment.get("answers", {})
    cls = assessment.get("classification", {})
    sys_name = _a(answers, "sys_name", "AI system")

    md = []
    md.append(f"# AI Risk Assessment - {sys_name}\n")
    md.append(_header(assessment))

    md.append("## 1. System overview\n")
    md.append(
        f"| Field | Value |\n|---|---|\n"
        f"| Name | {_a(answers,'sys_name')} |\n"
        f"| Version | {_a(answers,'sys_version')} |\n"
        f"| Owner | {_a(answers,'sys_owner')} |\n"
        f"| Role (Art. 3) | {_a(answers,'provider_role')} |\n"
        f"| Lifecycle stage | {_a(answers,'lifecycle_stage')} |\n"
        f"| Placed on the market/used in EU | {_a(answers,'eu_market')} |\n"
    )
    md.append(f"\n**Description.** {_a(answers,'sys_description')}\n")
    md.append(f"\n**Intended purpose.** {_a(answers,'intended_purpose')}\n")

    md.append("\n## 2. EU AI Act classification\n")
    md.append(f"**Risk tier: {cls.get('tier_label','-')}**\n\n")
    md.append(f"{cls.get('tier_description','')}\n\n")
    md.append(f"{cls.get('summary','')}\n")
    app = cls.get("applicability") or {}
    if app:
        md.append(f"\n**Applies from:** {app.get('date','-')} — {app.get('what','')} "
                  f"({_ref_link(app.get('basis',''))})\n")
    md.append(f"\n_Legal source: [EUR-Lex CELEX {eu.CELEX}]({eu.EURLEX_URL}) · "
              "article links via the AI Act Explorer._\n")

    md.append("\n### 2.1 Determining findings\n")
    md.append(_findings_block(cls.get("findings", [])))

    md.append("\n### 2.2 Transparency obligations (Art. 50)\n")
    md.append(_findings_block(cls.get("transparency_obligations", [])))

    if cls.get("gpai_obligations"):
        md.append("\n### 2.3 GPAI obligations (Chapter V)\n")
        md.append(_findings_block(cls.get("gpai_obligations", [])))

    md.append("\n### 2.4 Phased applicability timeline (Art. 113)\n")
    md.append(_timeline_table())

    if cls.get("high_risk_obligations"):
        md.append("\n## 3. High-risk system obligations\n")
        md.append("The following core obligations apply:\n\n")
        for ref, desc in cls["high_risk_obligations"]:
            md.append(f"- **{_ref_link(ref)}** - {desc}\n")

    md.append("\n## 4. Autonomy & human oversight\n")
    md.append(
        f"- Autonomy level: {_a(answers,'autonomy_level')}\n"
        f"- Human can override/stop: {_a(answers,'can_override')}\n"
        f"- Oversight measures: {_a(answers,'human_oversight')}\n"
    )

    md.append("\n## 5. Framework crosswalks\n")
    md.append("\n### 5.1 NIST AI RMF\n")
    md.append(
        "Mapping of the situation to relevant NIST AI RMF subcategories "
        "(GOVERN/MAP always apply; MEASURE/MANAGE scale with the risk):\n\n"
    )
    md.append(_nist_table(cls.get("nist_crosswalk", [])))
    md.append("\n### 5.2 ISO/IEC 42001\n")
    md.append(_iso_table())
    md.append(
        "\n#### 5.2.1 Annex A control mapping\n"
        "The 38 ISO/IEC 42001 Annex A reference controls, each tagged with its "
        "most-relevant EU AI Act article (analytical alignment — use it to plan "
        "an AIMS Statement of Applicability alongside this assessment):\n\n"
    )
    md.append(_iso_annex_a_table())
    md.append(f"\n_{iso.PROVENANCE}_\n")

    md.append("\n## 6. Risk register (to be completed)\n")
    md.append(
        "| # | Risk | Source | Likelihood | Impact | Mitigation | Owner | Status |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| 1 | _e.g. discriminatory outcomes_ | Training data | | | | | Open |\n"
        "| 2 | _e.g. lack of explainability_ | Model design | | | | | Open |\n"
        "| 3 | | | | | | | |\n"
    )

    md.append("\n## 7. Recommended documentation\n")
    for art in cls.get("recommended_artifacts", []):
        md.append(f"- {art}\n")

    md.append("\n## 8. Review & sign-off\n")
    md.append(
        "| Role | Name | Date | Signature |\n|---|---|---|---|\n"
        "| Author | | | |\n"
        "| Reviewer (AI governance) | | | |\n"
        "| Accountable owner | | | |\n"
    )
    return "".join(md)


# --- 2. DPIA skeleton ------------------------------------------------------
def render_dpia(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI system")

    md = []
    md.append(f"# DPIA Skeleton - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        "Data protection impact assessment (GDPR Art. 35), linked to the EU AI "
        "Act. A DPIA is typically required for high risk to data subjects, "
        "large-scale processing of special categories, or automated "
        "decision-making with legal effects (GDPR Art. 22).\n"
    )

    md.append("\n## 0. Need for a DPIA\n")
    md.append(
        f"- Personal data processed: {_a(answers,'data_personal')}\n"
        f"- Special categories (Art. 9): {_a(answers,'data_special_category')}\n"
        f"- Biometric data: {_a(answers,'data_biometric')}\n"
        f"- Automated decision-making (Art. 22): {_a(answers,'automated_decision')}\n"
        f"- Affects vulnerable groups: {_a(answers,'affects_vulnerable')}\n"
        f"- Scale: {_a(answers,'data_scale')}\n"
    )
    if not _bool(answers, "data_personal"):
        md.append(
            "\n> No personal data was indicated. A DPIA may then not be "
            "required; this skeleton serves to substantiate that conclusion.\n"
        )

    md.append("\n## 1. Systematic description of the processing\n")
    md.append(f"- Purpose: {_a(answers,'intended_purpose')}\n")
    md.append(f"- Description: {_a(answers,'sys_description')}\n")
    md.append(f"- Data origin: {_a(answers,'data_sources')}\n")
    md.append("- Categories of data subjects: _to be completed_\n")
    dg_rows = [r for r in dg.dataset_rows(answers)
               if r["classification"] in ("personal", "special_category")]
    if dg_rows:
        md.append("- Datasets with personal data (from the data-governance inventory):\n")
        for r in dg_rows:
            md.append(
                f"  - {_safe(r['name']) or '(unnamed)'} — {dg.label('classification', r['classification'])}; "
                f"origin {dg.label('origin', r['origin'])}; owner {_safe(r['owner']) or '-'}; "
                f"retention {_safe(r['retention']) or '_to be completed_'}; "
                f"legal basis {dg.label('legal_basis', r['legal_basis'])}\n"
            )
        md.append("- Recipients / processors: _to be completed_ (vendor-origin datasets "
                  "imply a processor or joint controller — check the DPA)\n")
    else:
        md.append("- Recipients / processors: _to be completed_\n")
        md.append("- Retention periods: _to be completed_ (or fill section 11 of the "
                  "intake; the data-governance report carries them per dataset)\n")
        md.append("- Legal basis (Art. 6 GDPR): _to be completed_\n")

    md.append("\n## 2. Assessment of necessity and proportionality\n")
    md.append(
        "- Is the processing necessary for the purpose? _to be completed_\n"
        "- Data minimisation and purpose limitation: _to be completed_\n"
        "- Data subject rights (access, objection, human intervention): _to be completed_\n"
    )

    md.append("\n## 3. Risks to rights and freedoms\n")
    md.append(
        "| # | Risk | Likelihood | Severity | Measure | Residual risk |\n"
        "|---|---|---|---|---|---|\n"
        "| 1 | _unlawful processing_ | | | | |\n"
        "| 2 | _discrimination / bias_ | | | | |\n"
        "| 3 | _data breach_ | | | | |\n"
    )

    md.append("\n## 4. Measures to mitigate risks\n")
    md.append("- Technical (encryption, access control, logging): _to be completed_\n")
    md.append("- Organisational (policy, training, DPAs): _to be completed_\n")
    md.append(f"- Human oversight (AI Act Art. 14): {_a(answers,'human_oversight')}\n")

    md.append("\n## 5. Link to the EU AI Act\n")
    md.append(
        "- Data governance & bias (Art. 10) - see bias audit checklist.\n"
        "- Transparency towards data subjects (Art. 13, Art. 50).\n"
        "- Fundamental rights impact assessment (Art. 27, FRIA) where applicable.\n"
    )

    md.append("\n## 6. DPO advice & decision\n")
    md.append(
        "| Item | Content |\n|---|---|\n"
        "| Advice of the data protection officer | |\n"
        "| Prior consultation with the DPA required? (Art. 36) | |\n"
        "| Decision of the controller | |\n"
        "| Date / signature | |\n"
    )
    return "".join(md)


# --- 3. Bias audit checklist -----------------------------------------------
BIAS_CHECKLIST = [
    ("Problem definition", [
        "Has 'fair' been defined for this application (which fairness notion)?",
        "Have the protected attributes/groups been identified (GDPR Art. 9, non-discrimination law)?",
        "Has it been recorded which harm bias would cause and to whom?",
    ]),
    ("Data (AI Act Art. 10)", [
        "Are training, validation and test data representative of the target population?",
        "Has the source data been checked for historical/societal bias?",
        "Have missing values and imbalanced classes been analysed?",
        "Is the origin and collection process of the data documented?",
    ]),
    ("Measurement (NIST MEASURE 2.11)", [
        "Has performance been broken down per (proxy for) protected group?",
        "Have multiple fairness metrics been computed (e.g. demographic parity, equalized odds)?",
        "Has the trade-off between fairness metrics been made explicit?",
        "Have intersectional groups (combinations of attributes) been examined?",
    ]),
    ("Mitigation", [
        "Have pre-/in-/post-processing mitigations been considered and tested?",
        "Has the effect of mitigation on both fairness and accuracy been measured?",
        "Has a threshold/decision policy been set that limits bias?",
    ]),
    ("Governance & oversight", [
        "Is there human oversight of high-impact outcomes (AI Act Art. 14)?",
        "Is there a complaint/objection route for data subjects?",
        "Is periodic re-assessment (drift, post-market monitoring Art. 72) scheduled?",
        "Are roles and responsibilities for fairness assigned (NIST GOVERN 2.1)?",
    ]),
]


def render_bias_checklist(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI system")

    md = []
    md.append(f"# Bias Audit Checklist - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        "Checklist for auditing bias and fairness, mapped to EU AI Act Art. 10 "
        "(data governance) and NIST AI RMF MEASURE 2.11. Check off and note "
        "evidence/findings per item.\n"
    )
    for section, items in BIAS_CHECKLIST:
        md.append(f"\n## {section}\n")
        md.append("| ✓ | Control point | Finding / evidence |\n|---|---|---|\n")
        for item in items:
            md.append(f"| ☐ | {item} | |\n")

    md.append("\n## Conclusion\n")
    md.append(
        "| Item | Content |\n|---|---|\n"
        "| Summary of key findings | |\n"
        "| Residual risks | |\n"
        "| Follow-up actions + deadlines | |\n"
        "| Auditor / date | |\n"
    )
    return "".join(md)


# --- 4. AI security assessment (OWASP LLM Top 10 + MITRE ATLAS) -------------
def render_security_assessment(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI system")
    profile = assessment.get("security") or assess_security(answers)

    md = []
    md.append(f"# AI Security Assessment - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        "Maps the system to the **OWASP Top 10 for LLM Applications (2025)** and "
        "**MITRE ATLAS**, linked to EU AI Act Art. 15 (accuracy, robustness and "
        "cybersecurity) and the NIST AI RMF.\n"
    )
    md.append(f"\n{profile.get('summary','')}\n")
    md.append(f"\n> {profile.get('disclaimer','')}\n")
    if profile.get("provenance"):
        md.append(f">\n> _{profile['provenance']}_\n")

    risks = profile.get("risks", [])
    if not risks:
        md.append("\n_No AI-security items were triggered by the current answers._\n")
    else:
        md.append("\n## Severity overview\n")
        md.append(
            "Severity is computed deterministically from the security-architecture "
            f"fields (section 9). Highest: **{profile.get('max_severity','-')}**.\n\n"
        )
        md.append("| Severity | Risk | Driven by |\n|---|---|---|\n")
        for r in risks:
            md.append(f"| **{r.get('severity','-')}** | {r['id']} {r['name']} | "
                      f"{r.get('severity_rationale','')} |\n")

        md.append("\n## Applicable risks\n")
        for r in risks:
            atlas = ", ".join(f"{t['id']} ({t['name']})" for t in r.get("atlas", [])) or "-"
            if r.get("atlas_note"):
                atlas += f" — {r['atlas_note']}"
            md.append(f"\n### {r['id']} - {r['name']}\n")
            md.append(f"{r['summary']}\n\n")
            md.append(
                f"| Aspect | Detail |\n|---|---|\n"
                f"| Severity | **{r.get('severity','-')}** — {r.get('severity_rationale','')} |\n"
                f"| Why it applies | {r['why']} |\n"
                f"| MITRE ATLAS | {atlas} |\n"
                f"| EU AI Act | {_refs(r['ai_act_refs'])} |\n"
                f"| NIST AI RMF | {', '.join(r['nist_refs'])} |\n"
                f"| Mitigation | {r['mitigation']} |\n"
            )

    md.append("\n## Framework integration matrix\n")
    md.append(
        "Bridges this AI-security view to the frameworks security reviewers and "
        "ISMS auditors use (NIST CSF 2.0, ISO/IEC 27001:2022):\n\n"
    )
    md.append(_framework_matrix_table())
    md.append(f"\n> _{sfw.PROVENANCE}_\n")

    md.append("\n## Security control checklist (to be completed)\n")
    md.append(
        "| ✓ | Control | Owner | Evidence |\n|---|---|---|---|\n"
        "| ☐ | Inputs from untrusted sources validated/sandboxed | | |\n"
        "| ☐ | Model output treated as untrusted before downstream use | | |\n"
        "| ☐ | Least-privilege tool/permission scopes | | |\n"
        "| ☐ | Secrets kept out of prompts; controls enforced server-side | | |\n"
        "| ☐ | Supply chain (models/data/deps) vetted and pinned | | |\n"
        "| ☐ | Rate limiting / quotas / abuse monitoring | | |\n"
        "| ☐ | Adversarial / red-team testing performed | | |\n"
    )
    return "".join(md)


# --- 5. FRIA - fundamental rights impact assessment (Art. 27) ---------------
def render_fria(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI system")

    md = []
    md.append(f"# Fundamental Rights Impact Assessment (FRIA) - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        "FRIA skeleton under **EU AI Act Art. 27**. Required, before first use, "
        "for deployers that are bodies governed by public law or private "
        "entities providing public services, and for deployers of the high-risk "
        "systems in **Annex III point 5(b) and (c)** (creditworthiness/credit "
        "scoring and risk assessment/pricing in life & health insurance). "
        "Complements any GDPR DPIA (Art. 27(4)); the result must be notified to "
        "the market surveillance authority (Art. 27(3)).\n"
    )

    sub = eu.ANNEX_III_5_SUBAREAS.get(_select(answers, "hr_essential_subarea"))
    if sub and sub.get("fria_all_deployers"):
        md.append(
            f"\n> **{sub['ref']} — {sub['title']}.** The FRIA duty applies to *every* "
            "deployer of this system, private entities included (Art. 27(1)).\n"
        )
    scope_note = eu.INSURANCE_SCOPE_NOTES.get(_select(answers, "hr_insurance_scope")) \
        if sub and sub["ref"] == "Annex III(5)(c)" else None
    if scope_note:
        md.append(f"\n> **Sector context.** {scope_note}\n")

    md.append("\n## (a) Deployer's processes using the system\n")
    md.append(f"Intended purpose: {_a(answers,'intended_purpose')}\n\n")
    md.append(f"Description: {_a(answers,'sys_description')}\n")

    md.append("\n## (b) Period and frequency of intended use\n")
    md.append("_To be completed (how long, how often, in which context)._\n")

    md.append("\n## (c) Categories of natural persons and groups affected\n")
    md.append(
        f"- Affects vulnerable groups: {_a(answers,'affects_vulnerable')}\n"
        "- Categories of affected persons/groups: _to be completed_\n"
    )

    md.append("\n## (d) Specific risks of harm to those persons/groups\n")
    md.append(
        "Consider the provider information (Art. 13). See also the bias-audit "
        "and AI security reports.\n\n"
        "| # | Right/freedom at risk | Specific harm | Affected group | Likelihood | Severity |\n"
        "|---|---|---|---|---|---|\n"
        "| 1 | _non-discrimination_ | | | | |\n"
        "| 2 | _privacy / data protection_ | | | | |\n"
        "| 3 | _human dignity / effective remedy_ | | | | |\n"
    )

    md.append("\n## (e) Human oversight measures\n")
    md.append(f"{_a(answers,'human_oversight')}\n")
    md.append(f"\n- A human can override/stop the system: {_a(answers,'can_override')}\n")

    md.append("\n## (f) Measures if risks materialise\n")
    md.append(
        "- Internal governance arrangements: _to be completed_\n"
        "- Complaint / redress mechanism for affected persons: _to be completed_\n"
        "- Escalation and incident handling: _to be completed_\n"
    )

    md.append("\n## Notification & sign-off\n")
    md.append(
        "| Item | Content |\n|---|---|\n"
        "| Market surveillance authority notified (Art. 27(3)) | |\n"
        "| Related GDPR DPIA reference (Art. 27(4)) | |\n"
        "| Responsible deployer | |\n"
        "| Date / signature | |\n"
    )
    return "".join(md)


# --- 6. Annex IV technical documentation (Art. 11) -------------------------
# The nine sections required by Annex IV of Regulation (EU) 2024/1689. Kept as a
# single source of truth so the renderer and its test agree on the headings.
ANNEX_IV_SECTIONS = [
    "1. General description of the AI system",
    "2. Detailed description of the elements and the development process",
    "3. Monitoring, functioning and control",
    "4. Appropriateness of the performance metrics",
    "5. Risk management system (Art. 9)",
    "6. Relevant changes through the system's lifecycle",
    "7. List of harmonised standards applied",
    "8. Copy of the EU declaration of conformity (Art. 47)",
    "9. Detailed description of the post-market monitoring plan (Art. 72)",
]

_TBC = "_[to be completed]_"


def render_technical_documentation(assessment):
    answers = assessment.get("answers", {})
    cls = assessment.get("classification", {})
    sys_name = _a(answers, "sys_name", "AI system")
    is_high = cls.get("tier") == eu.TIER_HIGH

    md = []
    md.append(f"# Technical Documentation (Annex IV) - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        f"Technical documentation skeleton under {_ref_link('Art. 11 + Annex IV')}. "
        "**Required for high-risk systems** before placing on the market; for "
        "other systems it is voluntary good practice. Pre-filled from the intake "
        f"answers; everything else is marked {_TBC} for the provider to complete.\n"
    )
    if not is_high:
        md.append(
            "\n> This system was **not** classified as high-risk. Annex IV "
            "documentation is then not mandatory, but this skeleton can serve as "
            "voluntary good practice and to substantiate that conclusion.\n"
        )

    # 1. General description
    md.append(f"\n## {ANNEX_IV_SECTIONS[0]}\n")
    md.append(
        f"| Field | Value |\n|---|---|\n"
        f"| Name | {_a(answers,'sys_name')} |\n"
        f"| Version | {_a(answers,'sys_version')} |\n"
        f"| Provider / owner | {_a(answers,'sys_owner')} |\n"
        f"| Role (Art. 3) | {_a(answers,'provider_role')} |\n"
        f"| Intended purpose | {_a(answers,'intended_purpose')} |\n"
    )
    md.append(f"\n**Description.** {_a(answers,'sys_description')}\n")
    md.append(
        "\n- How it interacts with / can be used together with hardware or other "
        f"software (incl. other AI systems): {_TBC}\n"
        f"- Forms in which it is placed on the market / put into service "
        f"(embedded, download, API, …): {_TBC}\n"
        f"- Hardware on which it is intended to run: {_TBC}\n"
        f"- Basic description of the user interface: {_TBC}\n"
        f"- Instructions for use for the deployer (Art. 13): {_TBC}\n"
    )

    # 2. Elements & development process
    md.append(f"\n## {ANNEX_IV_SECTIONS[1]}\n")
    md.append(
        f"- Methods and steps for development (incl. any third-party pre-trained "
        f"systems/tools): {_TBC}\n"
        f"- Design specifications, general logic and key design choices "
        f"(rationale, assumptions); what it is optimised for: {_TBC}\n"
        f"- System architecture: {_TBC}\n"
        f"- Data requirements / datasheets (training methodologies, datasets, "
        f"provenance, scope, labelling, cleaning) — stated data origin: "
        f"{_a(answers,'data_sources')}\n"
        f"- Assessment of the human-oversight measures ({_ref_link('Art. 14')}): "
        f"{_a(answers,'human_oversight')}\n"
        f"- Predetermined changes and continuous-compliance measures: {_TBC}\n"
        f"- Validation and testing procedures (accuracy, robustness, compliance): "
        f"{_TBC}\n"
        f"- Cybersecurity measures ({_ref_link('Art. 15')}): {_TBC}\n"
    )

    # 3. Monitoring, functioning and control
    md.append(f"\n## {ANNEX_IV_SECTIONS[2]}\n")
    md.append(
        f"- Capabilities and limitations, incl. expected accuracy (overall and for "
        f"specific persons/groups): {_TBC}\n"
        f"- Foreseeable unintended outcomes and risks to health, safety, "
        f"fundamental rights and of discrimination: {_TBC}\n"
        f"- Human-oversight measures ({_ref_link('Art. 14')}): autonomy level "
        f"{_a(answers,'autonomy_level')}; human can override/stop: "
        f"{_a(answers,'can_override')}\n"
        f"- Input-data specifications: {_TBC}\n"
    )

    # 4-8: largely human judgement
    md.append(f"\n## {ANNEX_IV_SECTIONS[3]}\n")
    md.append(f"{_TBC}\n")
    md.append(f"\n## {ANNEX_IV_SECTIONS[4]}\n")
    md.append(
        f"See the dedicated AI risk assessment / risk register ({_ref_link('Art. 9')}). "
        f"{_TBC}\n"
    )
    md.append(f"\n## {ANNEX_IV_SECTIONS[5]}\n")
    md.append(
        "| Date | Change | Reason | Impact on conformity |\n|---|---|---|---|\n"
        "| | | | |\n"
    )
    md.append(f"\n## {ANNEX_IV_SECTIONS[6]}\n")
    md.append(
        f"List the harmonised standards applied, or describe the other solutions "
        f"used to meet the requirements. {_TBC}\n"
    )
    md.append(f"\n## {ANNEX_IV_SECTIONS[7]}\n")
    md.append(f"Attach the EU declaration of conformity ({_ref_link('Art. 47')}). {_TBC}\n")

    # 9. Post-market monitoring plan
    md.append(f"\n## {ANNEX_IV_SECTIONS[8]}\n")
    md.append(
        f"Summarise (or attach) the post-market monitoring plan ({_ref_link('Art. 72')}); "
        "see the dedicated post-market monitoring report. "
        f"{_TBC}\n"
    )
    return "".join(md)


# --- 7. Obligations & conformity tracker (+ Art. 99 penalties) -------------
def _applies_from_for(family, applicability):
    """Per-row 'applies from' date. High-risk uses the system-level date; the
    other families have fixed dates from the timeline."""
    if family == "high":
        date = applicability.get("date", "-")
        basis = applicability.get("basis", "")
        return f"{date} ({basis})" if basis else date
    if family == "transparency":
        return "2 Aug 2026 (Art. 50)"
    if family == "gpai":
        return "2 Aug 2025 (Ch. V)"
    if family == "gdpr":
        return "In force (GDPR)"
    return "-"


def _compliance_rows(cls):
    """Build (obligation_ref, requirement, applies_from) rows deterministically
    from the classifier output. Status/owner/dates are left for the human."""
    applic = cls.get("applicability") or {}
    rows = []
    for ref, desc in cls.get("high_risk_obligations", []):
        rows.append((_ref_link(ref), desc, _applies_from_for("high", applic)))
    for f in cls.get("transparency_obligations", []):
        ref = f.get("refs", ["Art. 50"])[0]
        rows.append((_ref_link(ref), f.get("title", ""),
                     _applies_from_for("transparency", applic)))
    for f in cls.get("gpai_obligations", []):
        ref = f.get("refs", ["Art. 53"])[0]
        rows.append((_ref_link(ref), f.get("title", ""),
                     _applies_from_for("gpai", applic)))
    # GDPR artifacts that the engine recommends (e.g. a DPIA) — plain refs, as
    # GDPR is not on the AI Act Explorer.
    for art in cls.get("recommended_artifacts", []):
        if "DPIA" in art or "GDPR" in art:
            rows.append(("GDPR Art. 35", "Data protection impact assessment",
                         _applies_from_for("gdpr", applic)))
            break
    return rows


def _penalty_keys(cls):
    tier = cls.get("tier")
    keys = []
    if tier == eu.TIER_PROHIBITED:
        keys.append("prohibited")
    if (tier == eu.TIER_HIGH or cls.get("high_risk_obligations")
            or cls.get("transparency_obligations")):
        keys.append("high_other")
    keys.append("incorrect_info")
    if cls.get("gpai_obligations"):
        keys.append("gpai")
    return keys


def render_compliance_tracker(assessment):
    answers = assessment.get("answers", {})
    cls = assessment.get("classification", {})
    sys_name = _a(answers, "sys_name", "AI system")

    md = []
    md.append(f"# EU AI Act Obligations & Conformity Tracker - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        f"**Risk tier: {cls.get('tier_label','-')}**. The applicable obligations "
        "below follow deterministically from the classification; the status, "
        "evidence, owner and target dates are for the responsible team to fill "
        "in. Status is not inferred — every row starts as `Not started`.\n"
    )

    rows = _compliance_rows(cls)
    md.append("\n## Obligations\n")
    if not rows:
        md.append("_No specific obligations were triggered by the classification._\n")
    else:
        md.append(
            "| Obligation (Art.) | Requirement | Applies from | Status | "
            "Evidence / reference | Owner | Target date |\n"
            "|---|---|---|---|---|---|---|\n"
        )
        for ref, requirement, applies in rows:
            md.append(f"| {ref} | {requirement} | {applies} | Not started | | | |\n")

    keys = _penalty_keys(cls)
    if keys:
        md.append("\n## Penalties (Art. 99)\n")
        md.append(
            "Administrative fines that may apply to the obligations above "
            "(ceilings under the Regulation):\n\n"
            "| Violation | Basis | Maximum fine |\n|---|---|---|\n"
        )
        for k in keys:
            p = eu.PENALTIES[k]
            md.append(f"| {p['what']} | {_ref_link(p['ref'])} | {p['max']} |\n")
        md.append(f"\n> {eu.PENALTIES_SME_NOTE}\n")

    md.append("\n## Sign-off\n")
    md.append(
        "| Role | Name | Date | Signature |\n|---|---|---|---|\n"
        "| Compliance owner | | | |\n"
        "| AI governance reviewer | | | |\n"
    )
    return "".join(md)


# --- 8. Post-market monitoring plan (Art. 72) ------------------------------
def render_post_market_monitoring(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI system")

    md = []
    md.append(f"# Post-Market Monitoring Plan - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        f"Post-market monitoring plan under {_ref_link('Art. 72')} (providers) and "
        f"{_ref_link('Art. 26')} (deployer monitoring). Organised around six "
        "monitoring categories; fill in a baseline, threshold, data source, review "
        "cadence and owner per signal. Seeded rows are derived from the intake; "
        "extend as needed.\n"
    )

    seeded = mon.seeded_rows(answers)
    header = "| " + " | ".join(mon.COLUMNS) + " |\n"
    divider = "|" + "|".join(["---"] * len(mon.COLUMNS)) + "|\n"
    for cid, title, what in mon.CATEGORIES:
        md.append(f"\n## {title}\n")
        md.append(f"_{what}_\n\n")
        md.append(header)
        md.append(divider)
        for r in seeded.get(cid, []):
            md.append("| " + " | ".join(r.get(c, "") for c in mon.COLUMNS) + " |\n")
        md.append("| " + " | ".join([""] * len(mon.COLUMNS)) + " |\n")

    md.append("\n## Cross-cutting monitoring challenges\n")
    md.append("Recognised challenges to monitoring deployed AI systems:\n\n")
    for c in mon.CROSS_CUTTING:
        md.append(f"- {c}\n")

    md.append(f"\n> _{mon.PROVENANCE}_\n")
    return "".join(md)


# --- 9. Framework integration matrix (CSF 2.0 + ISO 27001:2022) ------------
def render_framework_matrix(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI system")

    md = []
    md.append(f"# Framework Integration Matrix - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        "Maps the AI-governance and AI-security findings onto the mainstream "
        "security frameworks: **NIST CSF 2.0** and **ISO/IEC 27001:2022**.\n"
    )

    md.append("\n## NIST CSF 2.0 functions\n")
    md.append("| Function | Code | Intent | Example categories |\n|---|---|---|---|\n")
    for code, name, intent, cats in sfw.CSF_FUNCTIONS:
        md.append(f"| {name} | {code} | {intent} | {cats} |\n")

    md.append("\n## ISO/IEC 27001:2022 Annex A controls (relevant subset)\n")
    md.append("_Public control titles only._\n\n")
    md.append("| Control | Title |\n|---|---|\n")
    for cid, title in sfw.ISO_27001_2022:
        md.append(f"| {cid} | {title} |\n")

    md.append("\n## Integration matrix\n")
    md.append(_framework_matrix_table())
    md.append(f"\n> _{sfw.PROVENANCE}_\n")
    return "".join(md)


# --- 10. Red-team test plan (OWASP LLM Top 10 + MITRE ATLAS) ---------------
def render_red_team_plan(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI system")
    plan = assessment.get("red_team") or generate_test_plan(answers)

    md = []
    md.append(f"# AI Red-Team Test Plan - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        "A prioritised, **architecture-aware** adversarial test plan derived from "
        "the AI security lens (OWASP Top 10 for LLM Applications 2025 + MITRE "
        "ATLAS). Each test case's priority is the deterministic, "
        "architecture-aware **severity** of its parent OWASP risk, so this plan "
        "is specific to the system's architecture rather than a generic "
        "checklist.\n"
    )
    md.append(f"\n> {plan.get('disclaimer','')}\n")

    cases = plan.get("cases", [])
    if not cases:
        md.append(
            "\n_No AI-security risks were triggered by the current answers, so no "
            "test cases were generated. Complete section 8 (AI security context) "
            "to scope a test plan._\n"
        )
        return "".join(md)

    # --- scope & rules of engagement ---
    md.append("\n## 1. Scope & rules of engagement\n")
    md.append(
        "- **Authorization.** Run only with explicit, written authorization from "
        "the system owner. This is a test plan, not permission to test.\n"
        "- **Environment.** Prefer a controlled non-production environment; use "
        "synthetic data only — never real personal data.\n"
        "- **Purple-team.** Coordinate with the defending team; for each test, "
        "confirm what they should detect (the *Detection & logging* column).\n"
        f"- **Tester access.** {plan.get('access_note','')}\n"
        "- **Methodology only.** Test cases describe technique families and "
        "objectives; design concrete payloads for the target — none are shipped "
        "here.\n"
    )
    if not plan.get("arch_provided"):
        md.append(
            "\n> Security-architecture context (section 9) was not fully provided, "
            "so priorities use conservative defaults. Complete it to refine the "
            "plan.\n"
        )

    # --- summary ---
    bp = plan.get("by_priority", {})
    md.append("\n## 2. Summary\n")
    md.append(
        f"{plan.get('count', 0)} test case(s); highest priority "
        f"**{plan.get('max_priority','-')}**. "
        f"Covers {len(plan.get('owasp_covered', []))}/10 OWASP LLM items and "
        f"{len(plan.get('atlas_covered', []))} MITRE ATLAS technique(s).\n\n"
    )
    md.append("| Priority | Test cases |\n|---|---|\n")
    for level in ("Critical", "High", "Medium", "Low"):
        if bp.get(level):
            md.append(f"| **{level}** | {bp[level]} |\n")

    # --- prioritised test cases ---
    md.append("\n## 3. Prioritised test cases\n")
    for c in cases:
        atlas = ", ".join(f"{t['id']} ({t['name']})" for t in c.get("atlas", [])) or "-"
        if c.get("atlas_note"):
            atlas += f" — {c['atlas_note']}"
        controls = (
            f"EU AI Act: {_refs(c['ai_act_refs'])}; "
            f"NIST AI RMF: {', '.join(c['nist_refs'])}. "
            f"Mitigation validated: {c['mitigation']}"
        )
        md.append(f"\n### {c['ref']} — {c['title']}  · **{c['priority']}**\n")
        objective = c["objective"]
        if c.get("gate_reason"):
            objective += f" _(included because {c['gate_reason']}.)_"
        md.append(
            f"| Aspect | Detail |\n|---|---|\n"
            f"| Priority | **{c['priority']}** (severity of {c['owasp']['id']}) |\n"
            f"| Targets | {c['owasp']['id']} {c['owasp']['name']} · {atlas} |\n"
            f"| Objective | {objective} |\n"
            f"| Preconditions | {c['preconditions']} |\n"
            f"| Method (methodology only) | {c['method']} |\n"
            f"| Success criteria | {c['success_criteria']} |\n"
            f"| Detection & logging | {c['detection']} |\n"
            f"| Controls validated | {controls} |\n"
        )

    # --- coverage matrix ---
    md.append("\n## 4. Coverage matrix\n")
    md.append("| OWASP LLM item | Tested | Test IDs | Highest priority |\n|---|---|---|---|\n")
    for info in sec.OWASP_LLM_TOP10.values():
        full_id = info["id"]
        matched = [c for c in cases if c["owasp"]["id"] == full_id]
        if matched:
            ids = ", ".join(c["ref"] for c in matched)
            top = max((c["priority"] for c in matched),
                      key=lambda s: SEVERITY_ORDER.get(s, 0))
            md.append(f"| {full_id} {info['name']} | Yes | {ids} | {top} |\n")
        else:
            md.append(f"| {full_id} {info['name']} | No | | |\n")

    # --- findings / reporting template ---
    md.append("\n## 5. Findings & reporting (to be completed)\n")
    md.append(
        "| Test ID | Result | Evidence | Severity (observed) | Residual risk | "
        "Remediation owner | Target date |\n"
        "|---|---|---|---|---|---|---|\n"
    )
    for c in cases:
        md.append(f"| {c['ref']} | Not run | | | | | |\n")

    md.append("\n## 6. Sign-off\n")
    md.append(
        "| Role | Name | Date | Signature |\n|---|---|---|---|\n"
        "| Lead tester | | | |\n"
        "| System owner (authorising) | | | |\n"
        "| AI governance reviewer | | | |\n"
    )
    md.append(f"\n> _{plan.get('provenance','')}_\n")
    return "".join(md)


# --- 11. Defensive control catalogue (OWASP LLM Top 10 + CSF/ISO) ----------
def render_control_catalog(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI system")
    cat = assessment.get("controls") or generate_control_catalog(answers)

    md = []
    md.append(f"# AI Defensive Control Catalogue - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        "A prioritised, **architecture-aware** catalogue of the controls to "
        "implement, derived from the AI security lens (OWASP Top 10 for LLM "
        "Applications 2025). It is the defensive counterpart of the red-team test "
        "plan: each control's priority is the architecture-aware **severity** of "
        "the OWASP risk it mitigates, and each names the red-team test case(s) "
        "that verify it — *implement, then test*.\n"
    )
    md.append(f"\n> {cat.get('disclaimer','')}\n")

    controls = cat.get("controls", [])
    if not controls:
        md.append(
            "\n_No AI-security risks were triggered by the current answers, so no "
            "controls were selected. Complete section 8 (AI security context) to "
            "build a catalogue._\n"
        )
        return "".join(md)

    md.append("\n## 1. How to read this catalogue\n")
    md.append(
        "- **Priority = severity.** A control's priority is the deterministic, "
        "architecture-aware severity of the OWASP risk it mitigates — so this is "
        "specific to the architecture, not a generic checklist.\n"
        "- **Conditional controls** appear only when the architecture warrants "
        "them; each carries a one-line reason.\n"
        "- **Validated by** names the red-team test case(s) (see the red-team "
        "test plan) that confirm the control is effective.\n"
        "- **Frameworks** anchor each control to a NIST CSF 2.0 function and "
        "ISO/IEC 27001:2022 control, plus the EU AI Act / NIST AI RMF references "
        "of the parent risk.\n"
    )
    if not cat.get("arch_provided"):
        md.append(
            "\n> Security-architecture context (section 9) was not fully provided, "
            "so priorities use conservative defaults. Complete it to refine the "
            "catalogue.\n"
        )

    bp = cat.get("by_priority", {})
    md.append("\n## 2. Summary\n")
    md.append(
        f"{cat.get('count', 0)} control(s); highest priority "
        f"**{cat.get('max_priority','-')}**. "
        f"Covers {len(cat.get('owasp_covered', []))}/10 OWASP LLM items and is "
        f"verified by {len(cat.get('validated_refs', []))} red-team test case(s).\n\n"
    )
    md.append("| Priority | Controls |\n|---|---|\n")
    for level in ("Critical", "High", "Medium", "Low"):
        if bp.get(level):
            md.append(f"| **{level}** | {bp[level]} |\n")

    md.append("\n## 3. Prioritised controls\n")
    for c in controls:
        control_text = c["control"]
        if c.get("gate_reason"):
            control_text += f" _(applies because {c['gate_reason']}.)_"
        validated = ", ".join(c["validated_by"]) or "-"
        md.append(f"\n### {c['ref']} — {c['title']}  · **{c['priority']}**\n")
        md.append(
            f"| Aspect | Detail |\n|---|---|\n"
            f"| Priority | **{c['priority']}** (severity of {c['owasp']['id']}) |\n"
            f"| Mitigates | {c['owasp']['id']} {c['owasp']['name']} |\n"
            f"| Control | {control_text} |\n"
            f"| Prevents | {c['intent']} |\n"
            f"| How to verify | {c['verify']} |\n"
            f"| Validated by (red-team) | {validated} |\n"
            f"| NIST CSF 2.0 | {', '.join(c['csf'])} |\n"
            f"| ISO/IEC 27001:2022 | {', '.join(c['iso'])} |\n"
            f"| EU AI Act | {_refs(c['ai_act_refs'])} |\n"
            f"| NIST AI RMF | {', '.join(c['nist_refs'])} |\n"
        )

    md.append("\n## 4. Coverage matrix\n")
    md.append("| OWASP LLM item | Controls | Control IDs | Highest priority |\n|---|---|---|---|\n")
    for info in sec.OWASP_LLM_TOP10.values():
        full_id = info["id"]
        matched = [c for c in controls if c["owasp"]["id"] == full_id]
        if matched:
            ids = ", ".join(c["ref"] for c in matched)
            top = max((c["priority"] for c in matched),
                      key=lambda s: SEVERITY_ORDER.get(s, 0))
            md.append(f"| {full_id} {info['name']} | {len(matched)} | {ids} | {top} |\n")
        else:
            md.append(f"| {full_id} {info['name']} | 0 | | |\n")

    md.append("\n## 5. Control register (to be completed)\n")
    md.append(
        "| Control ID | Implemented? | Owner | Evidence / reference | Target date |\n"
        "|---|---|---|---|---|\n"
    )
    for c in controls:
        md.append(f"| {c['ref']} | Not started | | | |\n")

    md.append("\n## 6. Sign-off\n")
    md.append(
        "| Role | Name | Date | Signature |\n|---|---|---|---|\n"
        "| Security owner | | | |\n"
        "| AI governance reviewer | | | |\n"
    )
    md.append(f"\n> _{cat.get('provenance','')}_\n")
    return "".join(md)


# --- 12. AI data security assessment (OWASP GenAI Data Security) ------------
def render_data_security(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI system")
    profile = assessment.get("data_security") or assess_data_security(answers)

    md = []
    md.append(f"# AI Data Security Assessment - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        "Maps the system to the **OWASP GenAI Data Security** risks "
        "(DSGAI01-DSGAI21) — the data-layer complement to the OWASP LLM Top 10 "
        "lens, covering training/fine-tuning data, prompts, retrieved context, "
        "embeddings, telemetry and outputs. Its natural EU AI Act anchor is "
        "**Art. 10 (data and data governance)**, with the GDPR where personal "
        "data is processed.\n"
    )
    md.append(f"\n{profile.get('summary','')}\n")
    md.append(f"\n> {profile.get('disclaimer','')}\n")
    if profile.get("provenance"):
        md.append(f">\n> _{profile['provenance']}_\n")

    risks = profile.get("risks", [])
    if not risks:
        md.append("\n_No OWASP GenAI Data Security risks were triggered by the "
                  "current answers._\n")
        return "".join(md)

    md.append("\n## 1. Applicable data-security risks\n")
    for r in risks:
        owasp = ", ".join(r.get("owasp_refs", [])) or "—"
        gdpr = ", ".join(r.get("gdpr_refs", [])) or "—"
        md.append(f"\n### {r['id']} - {r['name']}\n")
        md.append(f"{r['summary']}\n\n")
        md.append(
            f"| Aspect | Detail |\n|---|---|\n"
            f"| Why it applies | {r['why']} |\n"
            f"| Related OWASP LLM | {owasp} |\n"
            f"| EU AI Act | {_refs(r['ai_act_refs'])} |\n"
            f"| GDPR | {gdpr} |\n"
            f"| NIST AI RMF | {', '.join(r['nist_refs'])} |\n"
            f"| Mitigation | {r['mitigation']} |\n"
        )

    md.append("\n## 2. Coverage (all 21 DSGAI risks)\n")
    applicable = {r["id"] for r in risks}
    md.append("| DSGAI | Risk | Applicable | Related OWASP LLM |\n|---|---|---|---|\n")
    for oid in ds.ORDER:
        info = ds.DSGAI[oid]
        owasp = ", ".join(info["owasp_refs"]) or "—"
        mark = "Yes" if oid in applicable else "No"
        md.append(f"| {oid} | {info['name']} | {mark} | {owasp} |\n")

    md.append("\n## 3. Data-security control checklist (to be completed)\n")
    md.append(
        "| ✓ | Control | Owner | Evidence |\n|---|---|---|---|\n"
        "| ☐ | Data classified; retention & disposal set per class (incl. prompts/logs) | | |\n"
        "| ☐ | PII minimised and redacted in context, telemetry and outputs | | |\n"
        "| ☐ | Retrieval / vector store access-controlled and tenant-isolated | | |\n"
        "| ☐ | Ingestion validated; provenance tracked; poisoning monitored | | |\n"
        "| ☐ | Per-user/tenant context isolation (no cross-conversation bleed) | | |\n"
        "| ☐ | Lawful basis mapped; DPIA/FRIA completed where required | | |\n"
        "| ☐ | Sanctioned-AI inventory + egress controls (shadow AI) | | |\n"
    )

    md.append("\n## 4. Sign-off\n")
    md.append(
        "| Role | Name | Date | Signature |\n|---|---|---|---|\n"
        "| Data protection / security owner | | | |\n"
        "| AI governance reviewer | | | |\n"
    )
    return "".join(md)


# --- 13. STRIDE threat model (architecture-driven) -------------------------
def render_stride_threat_model(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI system")
    model = assessment.get("stride") or generate_stride_model(answers)

    md = []
    md.append(f"# STRIDE Threat Model - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        "Models the system across the six **STRIDE** categories (Spoofing, "
        "Tampering, Repudiation, Information disclosure, Denial of service, "
        "Elevation of privilege). Each category is driven by the "
        "security-architecture answers (section 9); the severity is the same "
        "architecture-aware rating the AI security lens computes, linked to "
        f"{_ref_link('Art. 15')}.\n"
    )
    md.append(f"\n{model.get('summary','')}\n")
    md.append(f"\n> {model.get('disclaimer','')}\n")
    if model.get("provenance"):
        md.append(f">\n> _{model['provenance']}_\n")

    categories = model.get("categories", [])
    md.append("\n## Severity overview\n")
    md.append(
        "Severity is computed deterministically from the security-architecture "
        f"fields. Highest: **{model.get('max_severity','-')}**.\n\n"
    )
    md.append("| STRIDE category | Severity | Driven by |\n|---|---|---|\n")
    for c in categories:
        md.append(f"| **{c['code']} — {c['name']}** | {c['severity']} | "
                  f"{c['severity_rationale']} |\n")

    md.append("\n## Per-category analysis\n")
    for c in categories:
        owasp = c.get("owasp") or "—"
        md.append(f"\n### {c['code']} — {c['name']}\n")
        md.append(f"{c['summary']}\n\n")
        md.append("**Questions that determine the risk:**\n")
        for q in c.get("questions", []):
            md.append(f"- {q}\n")
        md.append("\n| Architecture factor | Answer (from intake) |\n|---|---|\n")
        for f in c.get("fields", []):
            md.append(f"| {f['question']} | {f['answer']} |\n")
        md.append(
            f"\n| Aspect | Detail |\n|---|---|\n"
            f"| Severity | **{c['severity']}** — {c['severity_rationale']} |\n"
            f"| OWASP LLM Top 10 | {owasp} |\n"
            f"| EU AI Act | {_refs(c['ai_act_refs'])} |\n"
        )
    return "".join(md)


# --- 14. Serious-incident decision helper + report (Art. 3(49), Art. 73) ----
def render_incident(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI system")
    inc = assessment.get("incident") or assess_incident(answers)

    md = []
    md.append(f"# Serious-Incident Assessment & Report - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        f"A decision helper and report template for **serious incidents** under "
        f"{_ref_link('Art. 73')}, using the {_ref_link('Art. 3(49)')} definition. "
        "Maps to NIST CSF **Respond (RS)** and ISO/IEC 27001:2022 **A.5.24 / "
        "A.5.26** (incident management and response).\n"
    )
    md.append(f"\n> _{inc.get('definition','')}_\n")

    md.append("\n## 1. Is this a serious incident? (Art. 3(49))\n")
    md.append(
        "A serious incident is one whose effect meets **any** of the four limbs "
        "below. Mark each limb in the intake (section 10).\n\n"
    )
    md.append("| Met? | Limb | Effect |\n|---|---|---|\n")
    for limb in inc.get("limbs", []):
        mark = "Yes" if limb["met"] else "—"
        md.append(f"| {mark} | {_ref_link(limb['ref'])} | {limb['desc']} |\n")
    md.append(f"\n{inc.get('verdict','')}\n")

    md.append("\n## 2. Reporting deadlines (Art. 73)\n")
    md.append("| Case | Deadline (no later than) | Basis |\n|---|---|---|\n")
    for case, deadline, basis in inc.get("timeline", []):
        md.append(f"| {case} | {deadline} | {_ref_link(basis)} |\n")
    md.append(f"\n{inc.get('note','')}\n")

    md.append("\n## 3. Serious-incident report (to be completed)\n")
    md.append(
        f"| Field | Content |\n|---|---|\n"
        f"| System / version | {_a(answers,'sys_name')} {_a(answers,'sys_version','')} |\n"
        f"| Provider / deployer | {_a(answers,'sys_owner')} |\n"
        f"| Date/time the incident occurred | {_TBC} |\n"
        f"| Date the causal link was established | {_TBC} |\n"
        f"| Reportable / deadline | {('Yes — ' + inc['deadline']) if inc.get('reportable') else 'To be determined'} |\n"
        f"| Description of the incident | {_TBC} |\n"
        f"| Timeline of events | {_TBC} |\n"
        f"| Affected persons / groups | {_TBC} |\n"
        f"| Suspected root cause | {_TBC} |\n"
        f"| Immediate corrective / mitigating action | {_TBC} |\n"
        f"| Market surveillance authority notified (when / ref) | {_TBC} |\n"
        f"| Initial report filed / complete report due | {_TBC} |\n"
    )

    md.append("\n## 4. Sign-off\n")
    md.append(
        "| Role | Name | Date | Signature |\n|---|---|---|---|\n"
        "| Incident owner | | | |\n"
        "| AI governance / compliance reviewer | | | |\n"
    )
    return "".join(md)


# --- 15. Model card (Mitchell et al., 2019) --------------------------------
def render_model_card(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI system")
    card = assessment.get("model_card") or generate_model_card(answers)
    g = card.get("prefilled", {})

    def val(key):
        v = g.get(key)
        return _safe(v) if v else _TBC

    md = []
    md.append(f"# Model Card - {sys_name}\n")
    md.append(_header(assessment))
    md.append(
        f"A Model Card (Mitchell et al., 2019) — a light transparency artifact "
        f"whose natural EU AI Act anchor is {_ref_link('Art. 13')} (transparency "
        "and provision of information to deployers). Pre-filled from the intake "
        f"answers; everything requiring measurement or judgement is marked {_TBC}.\n"
    )

    md.append("\n## Model details\n")
    md.append(
        f"| Field | Value |\n|---|---|\n"
        f"| Name | {val('sys_name')} |\n"
        f"| Version | {val('sys_version')} |\n"
        f"| Owner / provider | {val('sys_owner')} |\n"
        f"| Role (Art. 3) | {val('provider_role')} |\n"
        f"| Lifecycle stage | {val('lifecycle_stage')} |\n"
        f"| Date | {_TBC} |\n"
        f"| License | {_TBC} |\n"
    )

    md.append("\n## Intended use\n")
    md.append(f"- **Intended purpose:** {val('intended_purpose')}\n")
    md.append(f"- **Description:** {val('sys_description')}\n")
    md.append(f"- **Primary intended users:** {_TBC}\n")
    md.append(f"- **Out-of-scope / prohibited uses:** {_TBC}\n")

    md.append("\n## Factors\n")
    md.append(
        f"Relevant groups, environments and instrumentation that may affect "
        f"performance.\n\n"
        f"- Affects vulnerable groups: {val('affects_vulnerable')}\n"
        f"- Relevant demographic / subgroup factors: {_TBC}\n"
        f"- Environmental / instrumentation factors: {_TBC}\n"
    )

    md.append("\n## Metrics\n")
    md.append(
        f"Performance measures, decision thresholds and how they were chosen. "
        f"{_TBC}\n"
    )

    md.append("\n## Evaluation data\n")
    md.append(f"Datasets used for evaluation, with provenance and preprocessing. {_TBC}\n")

    md.append("\n## Training data\n")
    md.append(f"Stated data origin: {val('data_sources')}\n\n")
    md.append(f"Distribution, provenance and preprocessing details: {_TBC}\n")

    md.append("\n## Quantitative analyses\n")
    md.append(
        f"Disaggregated results across the factors above (see the bias-audit "
        f"checklist for the structure). {_TBC}\n"
    )

    md.append("\n## Ethical considerations\n")
    md.append(
        f"- Processes personal data: {val('data_personal')}\n"
        f"- Special-category data (GDPR Art. 9): {val('data_special_category')}\n"
        f"- Biometric data: {val('data_biometric')}\n"
        f"- Automated decisions with significant effects (GDPR Art. 22): "
        f"{val('automated_decision')}\n"
        f"- Risks, harms and mitigations considered: {_TBC}\n"
    )

    md.append("\n## Caveats and recommendations\n")
    md.append(
        f"- Human oversight: {val('human_oversight')}\n"
        f"- Autonomy level: {val('autonomy_level')}; a human can override/stop: "
        f"{val('can_override')}\n"
        f"- Known limitations and recommendations for use: {_TBC}\n"
    )
    md.append(f"\n> _{card.get('provenance','')}_\n")
    return "".join(md)


def _role(answers):
    return str(answers.get("provider_role") or "").strip().lower()


# --- 16. EU Declaration of Conformity (Art. 47 + Annex V) ------------------
def render_declaration_of_conformity(assessment):
    answers = assessment.get("answers", {})
    cls = assessment.get("classification", {})
    sys_name = _a(answers, "sys_name", "AI system")
    is_high = cls.get("tier") == eu.TIER_HIGH

    md = [f"# EU Declaration of Conformity — {sys_name}\n", _header(assessment)]
    md.append(
        f"A skeleton **EU declaration of conformity** required by "
        f"{_ref_link('Art. 47')}, with the content items of {_ref_link('Annex V')}. "
        "The provider draws up one written DoC per high-risk system and keeps it "
        f"for 10 years after it is placed on the market or put into service. "
        f"Complete every {_TBC} before relying on it.\n"
    )
    if not is_high:
        md.append(
            f"\n> **Scope note.** On the current answers the system is "
            f"**{cls.get('tier_label', '-')}**, not high-risk. A DoC under "
            "Art. 47 is only required for high-risk systems — treat this as a "
            "template until/unless the classification is high-risk.\n"
        )
    if _role(answers) == "deployer":
        md.append(
            f"\n> **Role note.** Drawing up the DoC is a **provider** obligation "
            f"({_ref_link('Art. 16')}); a deployer relies on the provider's DoC "
            "rather than issuing its own.\n"
        )

    md.append("\n## 1. AI system (Annex V(1))\n")
    md.append(
        "| Field | Value |\n|---|---|\n"
        f"| AI system name / type | {_a(answers, 'sys_name')} |\n"
        f"| Version | {_a(answers, 'sys_version')} |\n"
        f"| Unique identifier / traceability to the system | {_TBC} |\n"
        f"| Intended purpose | {_a(answers, 'intended_purpose')} |\n"
    )
    md.append("\n## 2. Provider (Annex V(2))\n")
    md.append(
        "| Field | Value |\n|---|---|\n"
        f"| Provider name | {_a(answers, 'sys_owner')} |\n"
        f"| Registered trade name / address / contact | {_TBC} |\n"
        f"| Authorised representative (non-EU provider, {_ref_link('Art. 22')}) | {_TBC} |\n"
    )
    md.append("\n## 3. Statement of responsibility (Annex V(3))\n")
    md.append("> This declaration of conformity is issued under the sole "
              "responsibility of the provider.\n")
    md.append("\n## 4. Conformity (Annex V(4)–(6))\n")
    md.append(
        f"- The AI system above is in conformity with the {eu.REGULATION} and, "
        "where applicable, with other Union harmonisation legislation.\n"
        f"- Harmonised standards / common specifications applied: {_TBC}\n"
        f"- Where a notified body was involved ({_ref_link('Art. 43')}): its name, "
        f"identification number, the conformity-assessment procedure performed and "
        f"the certificate issued: {_TBC}\n"
    )
    md.append("\n## 5. Signature (Annex V(7))\n")
    md.append(
        "| Field | Value |\n|---|---|\n"
        f"| Place of issue | {_TBC} |\n"
        f"| Date of issue | {_TBC} |\n"
        f"| Name & function of signatory | {_TBC} |\n"
        "| Signature | |\n"
    )
    md.append(
        f"\n_Legal source: {_ref_link('Art. 47')} + {_ref_link('Annex V')}; "
        f"CE marking affixed per {_ref_link('Art. 48')}._\n"
    )
    return "".join(md)


# --- 17. EU database registration data sheet (Art. 49 + Annex VIII) --------
def render_registration(assessment):
    answers = assessment.get("answers", {})
    cls = assessment.get("classification", {})
    sys_name = _a(answers, "sys_name", "AI system")
    is_high = cls.get("tier") == eu.TIER_HIGH
    categories = [f"{eu.HIGH_RISK_USECASES[u]['ref']} — {eu.HIGH_RISK_USECASES[u]['title']}"
                  for u in (answers.get("hr_usecases") or [])
                  if u in eu.HIGH_RISK_USECASES]
    cat_str = "; ".join(categories) if categories else _TBC

    md = [f"# EU Database Registration Data Sheet — {sys_name}\n", _header(assessment)]
    md.append(
        f"A data sheet for registering a high-risk AI system in the EU database "
        f"({_ref_link('Art. 49')} + {_ref_link('Art. 71')}), collecting the "
        f"information items of {_ref_link('Annex VIII')} Section A. Registration "
        "happens before the system is placed on the market or put into service.\n"
    )
    if not is_high:
        md.append(
            f"\n> **Scope note.** On the current answers the system is "
            f"**{cls.get('tier_label', '-')}**. Registration under Art. 49 applies "
            "to high-risk systems (and, per Art. 49(3), to certain public-authority "
            "deployers) — treat this as a template until the classification is high-risk.\n"
        )

    md.append("\n## Annex VIII Section A — registration information\n")
    md.append(
        "| # | Item | Value |\n|---|---|---|\n"
        f"| 1 | Provider name, address, contact | {_a(answers, 'sys_owner')} / {_TBC} |\n"
        f"| 2 | Person submitting on the provider's behalf (if any) | {_TBC} |\n"
        f"| 3 | Authorised representative (if applicable) | {_TBC} |\n"
        f"| 4 | Trade name + unambiguous reference/identifier | {_a(answers, 'sys_name')} "
        f"{_a(answers, 'sys_version', '')} / {_TBC} |\n"
        f"| 5 | Intended purpose + components/functions supported by AI | "
        f"{_a(answers, 'intended_purpose')} |\n"
        f"| 6 | Concise description of the information (data, inputs) and operating logic | "
        f"{_a(answers, 'sys_description')} |\n"
        f"| 7 | Status of the system (on market / in service / withdrawn / recalled) | "
        f"{_a(answers, 'lifecycle_stage')} |\n"
        f"| 8 | Annex III high-risk category(ies) | {cat_str} |\n"
        f"| 9 | Notified-body certificate (type, number, expiry), if any | {_TBC} |\n"
        f"| 10 | Member States where on the market / in service / available | "
        f"{('EU' if _bool(answers, 'eu_market') else _TBC)} |\n"
        f"| 11 | Copy of the EU declaration of conformity | see the DoC report |\n"
        f"| 12 | Electronic instructions for use | {_TBC} |\n"
        f"| 13 | URL for additional information (optional) | {_TBC} |\n"
    )
    md.append(
        "\n> Registration for high-risk systems in **law enforcement, migration, "
        "asylum and border control** (Annex III(6)–(8)) is made in a **secure "
        "non-public** section of the database (Art. 49(4)).\n"
    )
    md.append(f"\n_Legal source: {_ref_link('Art. 49')} + {_ref_link('Annex VIII')}._\n")
    return "".join(md)


# --- 18. GPAI provider obligations (Chapter V, Art. 53–55) -----------------
def render_gpai_obligations(assessment):
    answers = assessment.get("answers", {})
    sys_name = _a(answers, "sys_name", "AI model")
    is_gpai = _truthy(answers.get("gpai_model"))
    is_systemic = _truthy(answers.get("gpai_systemic"))
    is_oss = _truthy(answers.get("gpai_open_source")) and not is_systemic

    md = [f"# GPAI Provider Obligations — {sys_name}\n", _header(assessment)]
    md.append(
        f"General-purpose AI **model** obligations under Chapter V "
        f"({_ref_link('Art. 53')}–{_ref_link('Art. 55')}), applicable from "
        "**2 Aug 2025** independently of the system's risk tier. Models already "
        f"on the market before that date must comply by 2 Aug 2027 ({_ref_link('Art. 111')}).\n"
    )
    if not is_gpai:
        md.append(
            "\n> **Scope note.** The current answers do not mark this as a GPAI "
            "model (`gpai_model`). This is shown as a template; the obligations "
            "below apply to providers of general-purpose AI models.\n"
        )

    md.append(f"\n## 1. Obligations for all GPAI providers ({_ref_link('Art. 53')}(1))\n")
    md.append(
        f"| Ref | Obligation | Status |\n|---|---|---|\n"
        f"| {_ref_link('Art. 53')}(1)(a) + Annex XI | Technical documentation of the "
        f"model (training/testing, evaluation). | {'Exempt (Art. 53(2))' if is_oss else 'Not started'} |\n"
        f"| {_ref_link('Art. 53')}(1)(b) + Annex XII | Information & documentation for "
        f"downstream providers integrating the model. | {'Exempt (Art. 53(2))' if is_oss else 'Not started'} |\n"
        f"| {_ref_link('Art. 53')}(1)(c) | Policy to comply with Union copyright law "
        f"(incl. Art. 4(3) DSM reservations). | Not started |\n"
        f"| {_ref_link('Art. 53')}(1)(d) | Publicly available **summary of the training "
        f"content** (AI Office template). | Not started |\n"
    )
    if is_oss:
        md.append(
            f"\n> **Open-source carve-out ({_ref_link('Art. 53')}(2)).** This model is "
            "marked as released under a free and open-source licence with no systemic "
            "risk, so the technical-documentation (a) and downstream-information (b) "
            "duties do not apply. The copyright policy (c) and training-content "
            "summary (d) still apply.\n"
        )

    md.append("\n## 2. Copyright policy — template\n")
    md.append(
        f"- [ ] Identify the copyright-relevant data used for training.\n"
        f"- [ ] Honour rights reservations expressed under Art. 4(3) of Directive "
        f"(EU) 2019/790 (the TDM opt-out).\n"
        f"- [ ] Document the measures taken to comply with Union copyright law.\n"
        f"- Notes: {_a(answers, 'data_sources')}\n"
    )
    md.append("\n## 3. Training-content summary — template\n")
    md.append(
        f"A sufficiently detailed summary of the content used for training, per the "
        f"AI Office template ({_ref_link('Art. 53')}(1)(d)):\n\n"
        f"- Main data collections / sources: {_a(answers, 'data_sources')}\n"
        f"- Large private/public datasets and their nature: {_TBC}\n"
        f"- Data obtained from web crawling / scraping (and domains): {_TBC}\n"
        f"- Other sources (user data, synthetic data, licensing): {_TBC}\n"
    )

    md.append(f"\n## 4. Systemic-risk obligations ({_ref_link('Art. 55')})\n")
    if is_systemic:
        md.append(
            "This model is marked as having **systemic risk** (≥ 10^25 FLOP training "
            f"compute or designated). In addition to §1, the provider must "
            f"({_ref_link('Art. 55')}):\n\n"
            "| Obligation | Status |\n|---|---|\n"
            "| Model evaluation incl. adversarial testing (red-teaming) | Not started |\n"
            "| Assess and mitigate systemic risks at Union level | Not started |\n"
            "| Track, document and report serious incidents to the AI Office | Not started |\n"
            "| Ensure an adequate level of cybersecurity for the model and its physical infrastructure | Not started |\n"
        )
        md.append(
            f"\n> Provider must notify the Commission without delay when the model "
            f"meets the systemic-risk threshold ({_ref_link('Art. 52')}).\n"
        )
    else:
        md.append(
            "The model is **not** marked as having systemic risk, so the additional "
            f"{_ref_link('Art. 55')} obligations (evaluation, adversarial testing, "
            "systemic-risk mitigation, incident reporting, cybersecurity) do not "
            "currently apply. Re-assess if training compute or designation changes.\n"
        )

    md.append(
        f"\n_Adherence to a code of practice ({_ref_link('Art. 56')}) is a means of "
        f"demonstrating compliance until harmonised standards exist. Legal source: "
        f"{_ref_link('Art. 53')}, {_ref_link('Art. 55')}, {eu.EURLEX_URL}._\n"
    )
    return "".join(md)


# --- dispatcher ------------------------------------------------------------

# --- 19. Data governance & quality (Art. 10) --------------------------------
def _dg_table(rows):
    head = ("| Dataset | Origin | Data owner | Steward | Classification | Purpose | "
            "Retention | Lawful basis |\n|---|---|---|---|---|---|---|---|\n")
    body = ""
    for r in rows:
        body += ("| " + " | ".join([
            _safe(r["name"]) or "-", dg.label("origin", r["origin"]),
            _safe(r["owner"]) or "-", _safe(r["steward"]) or "-",
            dg.label("classification", r["classification"]),
            _safe(r["purpose"]) or "-", _safe(r["retention"]) or "-",
            dg.label("legal_basis", r["legal_basis"]),
        ]) + " |\n")
    if not rows:
        body = "| _no datasets recorded_ | | | | | | | |\n"
    return head + body


def render_data_governance(assessment):
    answers = assessment.get("answers", {})
    cls = assessment.get("classification") or {}
    tier = cls.get("tier", "minimal")
    sys_name = _a(answers, "sys_name", "AI system")
    role = (answers.get("provider_role") or "").strip().lower()
    rows = dg.dataset_rows(answers)
    quality = dg.quality_rows(answers)
    gaps = dg.gaps(answers, tier)

    md = [f"# Data Governance & Quality — {sys_name}\n", _header(assessment)]
    if tier == "high":
        md.append(
            f"Data-governance record for a **high-risk** system. {_ref_link('Art. 10')} "
            "requires providers to evidence data governance and quality for training, "
            f"validation and test data; {_ref_link('Art. 26')}(4) requires deployers to "
            "keep input data relevant and sufficiently representative. This report is "
            "the evidence layer under the bias checklist, the DPIA and the Annex IV data "
            "description.\n"
        )
    else:
        md.append(
            f"Data-governance record. {_ref_link('Art. 10')} binds providers of high-risk "
            "systems; for this system it is good practice, and where personal data is "
            "processed the GDPR accuracy principle (Art. 5(1)(d)) and the record of "
            "processing (Art. 30) still apply. Gap severities are one notch lower than "
            "for a high-risk system.\n"
        )
    if role == "deployer":
        md.append(
            f"\n> **Role note.** As a deployer you do not own the training data, but "
            f"you do own the input data ({_ref_link('Art. 26')}(4)) and you need the "
            f"provider's data description ({_ref_link('Art. 13')}(3)(b)) to complete "
            "sections 2 and 5.\n"
        )

    md.append("\n## 1. Roles and accountability\n")
    md.append(
        "| Role | Named | Notes |\n|---|---|---|\n"
        f"| AI system owner | {_a(answers, 'sys_owner')} | Accountable for the system "
        "as a product (purpose, classification, conformity, monitoring). |\n"
        f"| Data owner | {_a(answers, 'dg_data_owner')} | Accountable for the data "
        "domain(s): access, quality targets, retention, lawful use. |\n"
        f"| Data steward | {_a(answers, 'dg_data_steward')} | Definitions, metadata, "
        "quality monitoring, issue resolution. |\n"
        f"| Registered in data catalogue | {_a(answers, 'dg_catalog_registered')} | "
        "Lineage, definitions and owners discoverable. |\n"
    )
    md.append("\nOperating-model reference (who does what):\n\n")
    md.append("| Role | Accountability | Anchor |\n|---|---|---|\n")
    for r, acc, anchor in dg.ROLES:
        md.append(f"| {r} | {acc} | {anchor} |\n")

    md.append("\n## 2. Dataset inventory (provenance, ownership, classification)\n")
    md.append(_dg_table(rows))
    md.append(
        f"\n_{len(rows)} dataset(s) recorded. Origin and collection process per dataset "
        f"map to {_ref_link('Art. 10')}(2)(b) and Annex IV(2)(d)._\n"
    )

    md.append("\n## 3. Classification, purpose limitation and lawful basis\n")
    personal_rows = [r for r in rows if r["classification"] in ("personal", "special_category")]
    special_rows = [r for r in rows if r["classification"] == "special_category"]
    md.append(
        f"- Datasets with personal data: {len(personal_rows)} "
        f"(special-category: {len(special_rows)})\n"
        f"- Intake: personal data = {_a(answers, 'data_personal')}, special categories = "
        f"{_a(answers, 'data_special_category')}, automated decision-making = "
        f"{_a(answers, 'automated_decision')}\n"
        f"- Special categories may be processed for bias detection/correction only under "
        f"{_ref_link('Art. 10')}(5) safeguards; that allowance does not create a lawful "
        "basis for using them as model features.\n"
    )
    for r in personal_rows:
        md.append(
            f"- **{_safe(r['name']) or '(unnamed)'}**: purpose _{_safe(r['purpose']) or 'not recorded'}_, "
            f"lawful basis {dg.label('legal_basis', r['legal_basis'])}, retention "
            f"{_safe(r['retention']) or 'not recorded'}.\n"
        )

    md.append("\n## 4. Lineage\n")
    lineage = str(answers.get("dg_lineage") or "").strip()
    if lineage:
        md.append("```text\n" + lineage.replace("```", "` ` `") + "\n```\n")
    else:
        md.append(
            "```text\nsource system(s) → preparation (cleaning / labelling / enrichment) "
            "→ training / validation / test sets → model version → output → "
            "downstream decision\n```\n_Template — replace with the real chain "
            f"({_ref_link('Art. 10')}(2)(c), Annex IV(2)(d))._\n"
        )
    md.append(f"\nPrepared-data sources noted in the intake: {_a(answers, 'data_sources')}\n")

    md.append("\n## 5. Data quality — dimensions and status\n")
    md.append("| Dimension | Definition | AI Act hook | Status | Suggested metric |\n"
              "|---|---|---|---|---|\n")
    for q in quality:
        md.append(f"| {q['name']} | {q['definition']} | {q['hook']} | "
                  f"**{dg.label('status', q['status'])}** | {q['metric']} |\n")
    md.append(f"\nEvidence recorded: {_a(answers, 'dg_q_evidence')}\n")

    md.append(f"\n## 6. {_ref_link('Art. 10')} requirement checklist\n")
    md.append("| ✓ | Ref | Requirement | Evidence / where |\n|---|---|---|---|\n")
    for ref, req in eu.ART_10_REQUIREMENTS:
        if ref.startswith("Art. 26") and role == "provider":
            continue
        md.append(f"| ☐ | {_ref_link(ref)} | {req} | |\n")

    md.append("\n## 7. Gaps and actions (derived from the intake)\n")
    if gaps:
        md.append("| Severity | Gap | Action | Ref |\n|---|---|---|---|\n")
        for sev, gap, action, ref in gaps:
            md.append(f"| {sev.capitalize()} | {_safe(gap)} | {_safe(action)} | {ref} |\n")
    else:
        md.append("_No gaps derived from the intake. Verify the evidence behind each "
                  "'measured' status._\n")

    md.append("\n## 8. Crosswalk\n")
    md.append("| Topic | EU AI Act | ISO/IEC 42001 | NIST AI RMF | EIOPA principle | "
              "DAMA-DMBOK area |\n|---|---|---|---|---|---|\n")
    for topic, act, iso_ref, nist_ref, eiopa, dama in dg.CROSSWALK:
        md.append(f"| {topic} | {act} | {iso_ref} | {nist_ref} | {eiopa} | {dama} |\n")
    md.append(f"\n> _{dg.PROVENANCE}_\n")

    md.append("\n## Sign-off\n")
    md.append(
        "| Item | Content |\n|---|---|\n"
        "| Data owner | |\n| Data steward | |\n| AI system owner | |\n"
        "| Next review date | |\n| Date / signature | |\n"
    )
    return "".join(md)


def render(report_type, assessment):
    sys_name = assessment.get("answers", {}).get("sys_name", "ai-system")
    slug = "".join(c if c.isalnum() else "-" for c in sys_name.lower()).strip("-") or "ai-system"
    if report_type == "risk":
        return "risk", f"risk-assessment-{slug}.md", render_risk_assessment(assessment)
    if report_type == "dpia":
        return "dpia", f"dpia-{slug}.md", render_dpia(assessment)
    if report_type == "bias":
        return "bias", f"bias-checklist-{slug}.md", render_bias_checklist(assessment)
    if report_type == "security":
        return "security", f"ai-security-{slug}.md", render_security_assessment(assessment)
    if report_type == "fria":
        return "fria", f"fria-{slug}.md", render_fria(assessment)
    if report_type == "techdoc":
        return "techdoc", f"annex-iv-techdoc-{slug}.md", render_technical_documentation(assessment)
    if report_type == "compliance":
        return "compliance", f"compliance-tracker-{slug}.md", render_compliance_tracker(assessment)
    if report_type == "monitoring":
        return "monitoring", f"post-market-monitoring-{slug}.md", render_post_market_monitoring(assessment)
    if report_type == "framework-matrix":
        return "framework-matrix", f"framework-matrix-{slug}.md", render_framework_matrix(assessment)
    if report_type == "redteam":
        return "redteam", f"red-team-test-plan-{slug}.md", render_red_team_plan(assessment)
    if report_type == "controls":
        return "controls", f"control-catalogue-{slug}.md", render_control_catalog(assessment)
    if report_type == "datasec":
        return "datasec", f"data-security-{slug}.md", render_data_security(assessment)
    if report_type == "stride":
        return "stride", f"stride-threat-model-{slug}.md", render_stride_threat_model(assessment)
    if report_type == "incident":
        return "incident", f"serious-incident-{slug}.md", render_incident(assessment)
    if report_type == "modelcard":
        return "modelcard", f"model-card-{slug}.md", render_model_card(assessment)
    if report_type == "doc":
        return "doc", f"declaration-of-conformity-{slug}.md", render_declaration_of_conformity(assessment)
    if report_type == "registration":
        return "registration", f"eu-database-registration-{slug}.md", render_registration(assessment)
    if report_type == "gpai":
        return "gpai", f"gpai-obligations-{slug}.md", render_gpai_obligations(assessment)
    if report_type == "datagov":
        return "datagov", f"data-governance-{slug}.md", render_data_governance(assessment)
    raise ValueError(f"Unknown report type: {report_type}")
