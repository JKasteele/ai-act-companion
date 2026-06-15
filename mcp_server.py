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
from pathlib import Path
from typing import Literal

# Make the bundled `app` package importable regardless of launch directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from app import reports, storage  # noqa: E402
from app.classifier import classify as _classify  # noqa: E402
from app.controls import generate_control_catalog as _generate_control_catalog  # noqa: E402
from app.data_security import assess_data_security as _assess_data_security  # noqa: E402
from app.questionnaire import QUESTIONNAIRE  # noqa: E402
from app.redteam import generate_test_plan as _generate_test_plan  # noqa: E402
from app.security import assess_security as _assess_security  # noqa: E402

mcp = FastMCP("ai-act-companion")


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
def generate_report(
    answers: dict,
    report_type: Literal[
        "risk", "dpia", "bias", "security", "fria",
        "techdoc", "compliance", "monitoring", "framework-matrix", "redteam",
        "controls", "datasec",
    ] = "risk",
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
        assess_data_security for the structured form).
    The system is classified deterministically first, then the report is
    rendered. Present the draft to the user for review before treating it as
    final.
    """
    assessment = {
        "id": "(unsaved)",
        "created_at": storage.now_iso(),
        "answers": answers,
        "classification": _classify(answers),
        "security": _assess_security(answers),
        "red_team": _generate_test_plan(answers),
        "controls": _generate_control_catalog(answers),
        "data_security": _assess_data_security(answers),
    }
    _rtype, _filename, markdown = reports.render(report_type, assessment)
    return markdown


@mcp.tool()
def save_assessment(answers: dict) -> dict:
    """Classify and PERSIST an assessment to disk, returning its id and the
    classification. Only call this after the user has explicitly reviewed and
    confirmed the answers (human-in-the-loop)."""
    assessment = {
        "id": storage.new_id(answers.get("sys_name")),
        "created_at": storage.now_iso(),
        "answers": answers,
        "classification": _classify(answers),
        "security": _assess_security(answers),
    }
    storage.save(assessment)
    return {"id": assessment["id"], "classification": assessment["classification"]}


@mcp.tool()
def list_assessments() -> list:
    """List previously saved assessments (id, system name, risk tier, date)."""
    return storage.list_all()


@mcp.tool()
def get_assessment(assessment_id: str) -> dict:
    """Load a previously saved assessment (answers + classification) by id."""
    data = storage.load(assessment_id)
    if not data:
        return {"error": f"Assessment not found: {assessment_id}"}
    return data


if __name__ == "__main__":
    mcp.run()
