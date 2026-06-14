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
from app.questionnaire import QUESTIONNAIRE  # noqa: E402

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
def generate_report(
    answers: dict,
    report_type: Literal["risk", "dpia", "bias"] = "risk",
) -> str:
    """Generate a documentation artifact as Markdown from the given answers.

    report_type: 'risk' (AI risk assessment), 'dpia' (DPIA skeleton, GDPR
    Art. 35) or 'bias' (bias-audit checklist). The system is classified
    deterministically first, then the report is rendered. Present the draft to
    the user for review before treating it as final.
    """
    assessment = {
        "id": "(unsaved)",
        "created_at": storage.now_iso(),
        "answers": answers,
        "classification": _classify(answers),
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
