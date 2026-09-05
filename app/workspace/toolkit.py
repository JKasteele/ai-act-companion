"""Dependency-free bridge to the complete toolkit, shared by FastAPI and Pyodide.

No model, storage writes, dynamic code, or arbitrary file paths. Drafts retain
unknown screening answers; the legacy classifier only runs after completeness.
Immutable shipped examples are explicitly identified as reference snapshots.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from .. import reports
from ..classifier import classify
from ..governance import governance_status
from ..knowledge.eu_ai_act import KNOWLEDGE_VERSION
from ..questionnaire import QUESTIONNAIRE
from ..security import assess_security

QUESTIONS: dict[str, Any] = {q["id"]: q for s in cast(Any, QUESTIONNAIRE)["sections"] for q in s["questions"]}
# These optional-in-the-legacy-form fields can change the classification.
SCREENING = {q["id"] for q in QUESTIONS.values() if q.get("required")} | {
    "hr_usecases", "hr_does_profiling", "gpai_model",
    "exempt_military", "exempt_research", "exempt_premarket", "exempt_personal",
}


def validate_answers(raw):
    if not isinstance(raw, dict) or len(raw) > 300:
        raise ValueError("Answers must be an object with at most 300 fields.")
    if len(json.dumps(raw).encode()) > 100_000:
        raise ValueError("The answer set is too large.")
    result = {}
    for key, value in raw.items():
        if key not in QUESTIONS:
            continue
        q = QUESTIONS[key]
        if value is None or value == "":
            continue
        kind = q["type"]
        if kind == "boolean":
            if not isinstance(value, bool):
                raise ValueError(f"{key}: choose Yes, No, or Unknown.")
        elif kind in {"text", "textarea"}:
            if not isinstance(value, str) or len(value) > (200 if key == "sys_name" else 10_000):
                raise ValueError(f"{key}: invalid or oversized text.")
            value = value.strip()
        elif kind in {"select", "radio", "multiselect"}:
            allowed = {o["value"] for o in q.get("options", [])}
            if kind == "multiselect":
                if not isinstance(value, list) or any(not isinstance(v, str) or v not in allowed for v in value):
                    raise ValueError(f"{key}: invalid choices.")
                if "none" in value and len(value) > 1:
                    raise ValueError(f"{key}: None cannot be combined with other choices.")
            elif not isinstance(value, str) or value not in allowed:
                raise ValueError(f"{key}: invalid choice.")
        elif kind == "table":
            if not isinstance(value, list) or len(value) > 100:
                raise ValueError(f"{key}: a table must contain at most 100 rows.")
            columns = {c["id"]: c for c in q["columns"]}
            for row in value:
                if not isinstance(row, dict):
                    raise ValueError(f"{key}: each row must be an object.")
                for column, text in row.items():
                    if column not in columns or not isinstance(text, str) or len(text) > 10_000:
                        raise ValueError(f"{key}: invalid table cell.")
                    spec = columns[column]
                    if spec["type"] == "select" and text and text not in {o["value"] for o in spec.get("options", [])}:
                        raise ValueError(f"{key}: invalid table choice.")
        result[key] = value
    return result


def missing_screening(answers):
    needed = set(SCREENING)
    if answers.get("hr_safety_component"):
        needed.update({"hr_annex_i_relation", "hr_annex_i_section", "hr_safety_function",
                       "hr_failure_endangers_health_safety", "hr_third_party_health_safety"})
    if any(v != "none" for v in answers.get("hr_usecases", [])):
        needed.add("hr_art6_3_minor")
    if answers.get("gpai_model"):
        needed.update({"gpai_open_source", "gpai_systemic"})
    if answers.get("p_nonconsensual_intimate") or answers.get("p_child_sexual_material"):
        needed.update({k for k in QUESTIONS if k.startswith("p_sexual_")})
    return [{"id": k, "label": QUESTIONS[k]["label"]} for k in QUESTIONS
            if k in needed and (k not in answers or answers[k] in (None, "", "unknown", []))]


def assess_answers(raw, reference=False):
    answers = validate_answers(raw)
    missing = missing_screening(answers)
    if missing and not reference:
        return {"status": "incomplete", "missing": missing, "classification": None,
                "draft": True, "knowledge_version": KNOWLEDGE_VERSION}
    return {
        "status": "reference" if reference else "assessed", "answers": answers,
        "classification": classify(answers), "security": assess_security(answers),
        "governance": governance_status(answers, classify(answers)),
        "knowledge_version": KNOWLEDGE_VERSION, "draft": True,
        "provenance": "Shipped example input snapshot" if reference else "Confirmed structured screening answers",
    }


def examples():
    directory = Path(__file__).resolve().parents[2] / "examples"
    result = []
    for path in sorted(directory.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or not raw.get("sys_name"):
            continue
        answers = {k: v for k, v in raw.items() if not k.startswith("_")}
        result.append({"id": path.stem, "name": answers["sys_name"], "answers": answers,
                       "result": assess_answers(answers, reference=True)})
    return result


def catalogue():
    return {"questionnaire": QUESTIONNAIRE, "examples": examples(),
            "reports": [{"id": r, "label": label} for r, label in reports.REPORT_CATALOG],
            "screening": sorted(SCREENING), "knowledge_version": KNOWLEDGE_VERSION}


def dispatch(payload):
    if not isinstance(payload, dict):
        raise ValueError("Expected a toolkit request.")
    operation = payload.get("operation")
    if operation == "validate":
        return {"answers": validate_answers(payload.get("answers", {}))}
    if operation not in {"assess", "report", "example_report"}:
        raise ValueError("Unknown toolkit operation.")
    reference = operation == "example_report"
    if reference:
        example = next((e for e in examples() if e["id"] == payload.get("example_id")), None)
        if not example:
            raise ValueError("Unknown shipped example.")
        answers = example["answers"]
    else:
        answers = payload.get("answers", {})
    result = assess_answers(answers, reference=reference)
    if operation == "assess" or result["status"] == "incomplete":
        return result
    report_type = payload.get("report_type", "risk")
    language = payload.get("language", "en")
    if report_type not in reports.REPORT_TYPES or language not in {"en", "nl"}:
        raise ValueError("Unknown report type or language.")
    assessment = {**result, "id": "workspace-draft",
                  "created_at": datetime.now(timezone.utc).isoformat()}
    kind, filename, markdown = reports.render(report_type, assessment, lang=language)
    if reference:
        markdown = "> Reference example generated from the shipped input snapshot. Review and complete screening before using an edited copy.\n\n" + markdown
    return {"status": "reference" if reference else "draft", "type": kind,
            "filename": filename, "markdown": markdown, "draft": True}
