"""MCP server for AI Act Companion.

Exposes the deterministic toolkit as Model Context Protocol tools so that
Claude Code (or any MCP client) becomes the natural-language interface to the
engine. Design intent:

  * The rule engine is the GROUND TRUTH. Claude must call `classify_ai_system`
    to determine the EU AI Act risk tier; it must not infer or override the
    tier itself.
  * Claude is the interface + narrative author (intake conversation, drafting
    descriptions), with a mandatory human-in-the-loop review before anything
    is finalised or stored.

Run directly (`python mcp_server.py`) over stdio. Requires `pip install mcp`.
"""

import sys
from importlib import import_module
from pathlib import Path
from typing import Literal

# Make the bundled `app` package importable regardless of launch directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# mcp 2.x renamed FastMCP to MCPServer (same decorator/run API for stdio);
# support both so `pip install ai-act-companion[mcp]` works on either major.
try:  # pragma: no branch - depends on the installed SDK
    _Server = import_module("mcp.server.mcpserver").MCPServer  # mcp >= 2
except (ImportError, AttributeError):  # pragma: no cover - SDK-version dependent
    _Server = import_module("mcp.server.fastmcp").FastMCP  # mcp 1.x

from app import reports, storage  # noqa: E402
from app.classifier import classify as _classify  # noqa: E402
from app.controls import generate_control_catalog as _generate_control_catalog  # noqa: E402
from app.data_security import assess_data_security as _assess_data_security  # noqa: E402
from app.forensics import assess_forensic_readiness as _assess_forensic_readiness  # noqa: E402
from app.governance import governance_status as _governance_status  # noqa: E402
from app.incident import assess_incident as _assess_incident  # noqa: E402
from app.knowledge import data_governance as _dg  # noqa: E402
from app.modelcard import generate_model_card as _generate_model_card  # noqa: E402
from app.questionnaire import QUESTIONNAIRE  # noqa: E402
from app.redteam import generate_test_plan as _generate_test_plan  # noqa: E402
from app.scan import scan_repo as _scan_repo  # noqa: E402
from app.security import assess_security as _assess_security  # noqa: E402
from app.stride import generate_stride_model as _generate_stride_model  # noqa: E402

mcp = _Server("ai-act-companion")


@mcp.tool()
def get_questionnaire() -> dict:
    """Return the EU AI Act intake questionnaire (sections, questions, field
    ids, types and options). Use this first to know which fields exist and what
    values are valid before collecting answers from the user."""
    return QUESTIONNAIRE


@mcp.tool()
def classify_ai_system(answers: dict) -> dict:
    """Deterministically classify an AI system under the EU AI Act.

    `answers` maps questionnaire field ids to values (see get_questionnaire).
    Returns the risk tier (prohibited/high/limited/minimal), the cited articles
    and annexes, the reasoning, transparency and GPAI obligations, and the NIST
    AI RMF crosswalk.

    This is the authoritative classification. Do NOT decide the risk tier
    yourself - always rely on this result.
    """
    return _classify(answers)


@mcp.tool()
def classify_ai_security(answers: dict) -> dict:
    """Map the AI system to the applicable OWASP Top 10 for LLM Applications
    (2025) risks, each with the relevant MITRE ATLAS techniques and EU AI Act /
    NIST AI RMF controls. Deterministic security lens that complements
    `classify_ai_system`. Relevance is driven by the `sec_*` intake fields."""
    return _assess_security(answers)


@mcp.tool()
def generate_red_team_plan(answers: dict) -> dict:
    """Generate a prioritised, architecture-aware AI red-team **test plan** from
    the AI security lens. Returns structured test cases (objective, MITRE ATLAS
    targets, preconditions, methodology, success criteria, detection and the EU
    AI Act / NIST controls each validates), each prioritised by the
    architecture-aware severity of its parent OWASP risk, plus a coverage
    summary. Driven by the `sec_*`/`arch_*` intake fields.

    This is a planning aid to scope an AUTHORIZED purple-team exercise — it
    contains no working exploit payloads and executes nothing. Treat it as a
    draft for human review."""
    return _generate_test_plan(answers)


@mcp.tool()
def generate_control_catalog(answers: dict) -> dict:
    """Generate a prioritised, architecture-aware **defensive control catalogue**
    — the blue-team counterpart of the red-team test plan. Returns the controls
    to implement for each in-scope OWASP LLM risk (what to implement, what it
    prevents, how to verify it, the NIST CSF 2.0 / ISO 27001 anchors and the EU
    AI Act / NIST AI RMF references), each prioritised by the architecture-aware
    severity of the risk it mitigates and cross-linked to the red-team test
    case(s) that verify it. Driven by the `sec_*`/`arch_*` intake fields.
    Self-assessment aid; present as a draft for human review."""
    return _generate_control_catalog(answers)


@mcp.tool()
def assess_data_security(answers: dict) -> dict:
    """Map the AI system to the applicable **OWASP GenAI Data Security** risks
    (DSGAI01-DSGAI21) — the data-layer complement to `classify_ai_security`,
    covering training data, prompts, retrieved context, embeddings, telemetry and
    outputs. Each applicable risk carries its related OWASP LLM Top 10 item(s) and
    EU AI Act (Art. 10 anchor) / GDPR / NIST AI RMF controls. Deterministic;
    relevance is driven by the `sec_*`/`arch_*`/`data_*` intake fields."""
    return _assess_data_security(answers)


@mcp.tool()
def assess_data_governance(answers: dict) -> dict:
    """Structured **data-governance** view (EU AI Act Art. 10 / Art. 26(4)): the
    dataset inventory from `dg_datasets` (origin, owner, steward, classification,
    purpose, retention, lawful basis), the seven data-quality dimensions with their
    status, and a deterministic gap list with severities. Severities are one notch
    lower outside the high-risk tier. Documentation only — never affects the tier."""
    tier = _classify(answers).get("tier", "minimal")
    return _dg.summary(answers, tier)


@mcp.tool()
def assess_forensic_readiness(answers: dict) -> dict:
    """**Forensic readiness** (Art. 12 / 19 / 26(6) / 73): the evidence register
    (16 artefacts, each in place / gap / n-a for this architecture and role), an
    8-dimension readiness score (0-16) with band, retention-vs-minimisation
    conflicts, the parallel reporting clocks (AI Act / GDPR / DORA / NIS2) and
    gaps with actions. Pure function of the `fr_*` and structural fields."""
    return _assess_forensic_readiness(answers, _classify(answers))


@mcp.tool()
def governance_status(answers: dict) -> dict:
    """**Governance register** status: policy owner, approval body, status, review
    cadence for the tier, next review (recorded or derived) and the overdue flag,
    exceptions (expired / open-ended), evidence of Art. 4 support measures, intake
    completeness per section and a gap list. Reads the `gov_*` fields."""
    return _governance_status(answers, _classify(answers))


@mcp.tool()
def generate_report(
    answers: dict | None = None,
    report_type: Literal[
        "risk", "dpia", "bias", "security", "fria",
        "techdoc", "compliance", "monitoring", "framework-matrix", "redteam",
        "controls", "datasec", "stride", "incident", "modelcard",
        "doc", "registration", "gpai", "datagov", "forensics", "governance",
    ] = "risk",
    assessment_id: str = "",
    lang: Literal["en", "nl"] = "en",
) -> str:
    """Generate a documentation artifact as Markdown from the given answers.

    report_type:
      'risk' - AI risk assessment;
      'dpia' - DPIA skeleton (GDPR Art. 35);
      'bias' - bias-audit checklist;
      'security' - AI security assessment (OWASP LLM Top 10 + MITRE ATLAS, with
        architecture-aware severity and a NIST CSF 2.0 / ISO 27001 matrix);
      'fria' - fundamental rights impact assessment (Art. 27);
      'techdoc' - Annex IV technical documentation skeleton (Art. 11);
      'compliance' - obligations & conformity tracker with Art. 99 penalties;
      'monitoring' - post-market monitoring plan (Art. 72);
      'framework-matrix' - NIST CSF 2.0 / ISO 27001:2022 framework integration
        matrix;
      'redteam' - architecture-aware AI red-team test plan (authorized
        purple-team scoping; see generate_red_team_plan for the structured form);
      'controls' - prioritised defensive control catalogue (the blue-team
        counterpart of the red-team plan; see generate_control_catalog);
      'datasec' - OWASP GenAI Data Security assessment (DSGAI01-21; see
        assess_data_security for the structured form);
      'stride' - STRIDE threat model across the six categories, driven by the
        architecture fields and reusing the architecture-aware severity;
      'incident' - serious-incident decision helper (Art. 3(49)) + Art. 73
        reporting-deadline template;
      'modelcard' - Model Card skeleton (Mitchell et al., 2019; Art. 13),
        pre-filled from the intake;
      'doc' - EU Declaration of Conformity skeleton (Art. 47 + Annex V);
      'registration' - EU-database registration data sheet (Art. 49 + Annex VIII);
      'gpai' - GPAI provider obligations (Art. 53-55) with copyright-policy and
        training-content-summary templates;
      'datagov' - data governance & quality record (Art. 10 / Art. 26(4)):
        roles (data owner/steward), dataset inventory with provenance and
        classification, lineage, DAMA-style quality dimensions, derived gap
        list and an ISO 42001 A.7 / NIST / EIOPA crosswalk;
      'forensics' - forensic readiness & evidence plan (Art. 12/19/26(6)/73):
        evidence register (artefact -> obligation -> location -> retention ->
        owner -> integrity), readiness score over eight dimensions, parallel
        reporting clocks (AI Act / GDPR / DORA / NIS2) and a crosswalk to ISO
        27001, ISO 42001, CIS Control 8, ATLAS AML.M0024;
      'governance' - governance register: policy owner / approval body /
        status / review cadence and overdue flag, exceptions with end dates,
        evidence of Art. 4 AI-literacy support measures, intake completeness and
        the AI-register entry.
    `lang='nl'` prepends a Dutch summary block (risk tier, applicability, findings,
    recommended documentation, governance headlines); the citable body stays
    English. Provide either `answers` (classified on the fly) or `assessment_id`
    (render from a previously saved assessment). The system is classified
    deterministically first, then the report is rendered. Present the draft to
    the user for review before treating it as final.
    """
    if assessment_id:
        saved = storage.load(assessment_id)
        if not saved:
            raise ValueError(f"Assessment not found: {assessment_id}")
        answers = saved.get("answers", {})
    answers = answers or {}
    assessment = {
        "id": assessment_id or "(unsaved)",
        "created_at": storage.now_iso(),
        "answers": answers,
        "classification": _classify(answers),
        "security": _assess_security(answers),
        "red_team": _generate_test_plan(answers),
        "controls": _generate_control_catalog(answers),
        "data_security": _assess_data_security(answers),
        "stride": _generate_stride_model(answers),
        "incident": _assess_incident(answers),
        "model_card": _generate_model_card(answers),
    }
    _rtype, _filename, markdown = reports.render(report_type, assessment, lang=lang)
    return markdown


@mcp.tool()
def save_assessment(answers: dict, confirmed: bool = False) -> dict:
    """Classify and PERSIST an assessment to disk, returning its id and the
    classification.

    Human-in-the-loop is enforced as a contract, not just a convention: you must
    pass `confirmed=True`, and may only do so after the user has explicitly
    reviewed the answers and asked you to save. If `confirmed` is not True this
    tool stores nothing and returns a notice telling you to obtain confirmation
    first."""
    if not confirmed:
        return {
            "saved": False,
            "reason": "Not saved: human-in-the-loop confirmation required. Show "
                      "the classification to the user and call again with "
                      "confirmed=True only after they approve.",
        }
    assessment = {
        "id": storage.new_id(answers.get("sys_name")),
        "created_at": storage.now_iso(),
        "answers": answers,
        "classification": _classify(answers),
        "security": _assess_security(answers),
    }
    storage.save(assessment)
    return {"saved": True, "id": assessment["id"],
            "classification": assessment["classification"]}


@mcp.tool()
def list_assessments() -> list:
    """List previously saved assessments (id, system name, risk tier, date)."""
    return storage.list_all()


@mcp.tool()
def get_assessment(assessment_id: str) -> dict:
    """Load a previously saved assessment (answers + classification) by id.
    Raises if the id is unknown (same not-found contract as the HTTP API)."""
    data = storage.load(assessment_id)
    if not data:
        raise ValueError(f"Assessment not found: {assessment_id}")
    return data


@mcp.tool()
def scan_repository(path: str = ".") -> dict:
    """Scan a repository tree for AI/ML usage and return a structured EU AI Act
    **relevance** flag (dependency manifests, source imports, model artifacts),
    with the Articles worth checking. Deterministic, stdlib-only, no model calls;
    a relevance signal, NOT a classification — run classify_ai_system on any
    system it surfaces. Mirrors the `ai-act scan` CLI and the GitHub Action."""
    return _scan_repo(path)


if __name__ == "__main__":
    mcp.run()
