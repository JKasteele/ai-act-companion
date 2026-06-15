"""Report generators: risk assessment, DPIA skeleton, bias audit checklist.

All output is Markdown (the canonical export). The frontend renders it to HTML
for preview/print. No external templating dependency: we build the Markdown with
Python strings, fed by the classifier output.
"""

from .controls import generate_control_catalog
from .data_security import assess_data_security
from .knowledge import ai_security as sec
from .knowledge import data_security as ds
from .knowledge import eu_ai_act as eu
from .knowledge import iso_42001 as iso
from .knowledge import monitoring as mon
from .knowledge import security_frameworks as sfw
from .redteam import generate_test_plan
from .security import SEVERITY_ORDER, assess_security

REPORT_TYPES = ("risk", "dpia", "bias", "security", "fria", "techdoc",
                "compliance", "monitoring", "framework-matrix", "redteam",
                "controls", "datasec")


# --- helpers ---------------------------------------------------------------
def _a(answers, key, default="-"):
    val = answers.get(key)
    if val is None or val == "":
        return default
    if isinstance(val, bool):
        return "Yes" if val else "No"
    if isinstance(val, list):
        return ", ".join(str(v) for v in val) if val else default
    return str(val)


def _bool(answers, key):
    return bool(answers.get(key)) and answers.get(key) not in ("false", "no")


def _header(assessment):
    return (
        f"_Assessment id: `{assessment.get('id', '-')}` · "
        f"Generated: {assessment.get('created_at', '-')} · "
        f"AI Act Companion v0.3_\n\n"
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
    return "\n".join(rows) + "\n"


def _iso_table():
    rows = ["| EU AI Act | ISO/IEC 42001 anchor | Note |", "|---|---|---|"]
    for art, anchor, note in iso.CROSSWALK:
        rows.append(f"| {_ref_link(art)} | {anchor} | {note} |")
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
    md.append("- Recipients / processors: _to be completed_\n")
    md.append("- Retention periods: _to be completed_\n")
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


# --- dispatcher ------------------------------------------------------------
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
    raise ValueError(f"Unknown report type: {report_type}")
