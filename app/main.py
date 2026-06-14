"""FastAPI app: serves the frontend and the API.

Endpoints:
  GET  /                                   -> frontend (static/index.html)
  GET  /api/questionnaire                  -> questionnaire definition
  POST /api/assess                         -> classify + store
  GET  /api/assessments                    -> list stored assessments
  GET  /api/assessments/{id}               -> full assessment
  GET  /api/assessments/{id}/report?type=  -> report (markdown) per type
  GET  /api/health                         -> health check
  GET  /api/ai/status, POST /api/ai/{prefill,parse,narrative} -> optional AI layer
"""

import csv
import io
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import __version__, reports, storage
from .classifier import classify
from .models import (
    AssessmentSummary,
    AssessRequest,
    AssessResponse,
    Classification,
    NarrativeRequest,
    ParseRequest,
    PrefillRequest,
    ReportResponse,
)
from .questionnaire import QUESTIONNAIRE
from .security import assess_security

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="AI Act Companion",
    version=__version__,
    description="Local EU AI Act / NIST AI RMF assessment toolkit.",
)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": __version__, "ai_layer": True}


# --- AI layer (phase 4) ----------------------------------------------------
# Optional: the rule-based core keeps working even if this import fails.
try:
    from .llm import service as ai_service
except Exception:  # noqa: BLE001
    ai_service = None


def _require_ai():
    if ai_service is None:
        raise HTTPException(status_code=503, detail="AI layer not available.")
    return ai_service


@app.get("/api/ai/status")
def ai_status():
    if ai_service is None:
        return {"enabled": False, "provider": "none"}
    return ai_service.status()


@app.post("/api/ai/prefill")
def ai_prefill(req: PrefillRequest):
    svc = _require_ai()
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="Provide a description.")
    try:
        return svc.prefill_from_text(req.description)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI call failed: {e}") from e


@app.post("/api/ai/parse")
def ai_parse(req: ParseRequest):
    svc = _require_ai()
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="No text to parse.")
    return svc.parse_completion(req.text)


@app.post("/api/ai/narrative")
def ai_narrative(req: NarrativeRequest):
    svc = _require_ai()
    try:
        return svc.draft_narrative(req.field, req.answers)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI call failed: {e}") from e


@app.get("/api/questionnaire")
def get_questionnaire():
    return QUESTIONNAIRE


@app.get("/api/examples")
def list_examples():
    """Ready-made synthetic examples (one per risk tier) users can load."""
    out = []
    ex_dir = BASE_DIR / "examples"
    if ex_dir.exists():
        for path in sorted(ex_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            answers = {k: v for k, v in data.items() if not k.startswith("_")}
            out.append({
                "id": path.stem,
                "name": answers.get("sys_name", path.stem),
                "tier_label": classify(answers)["tier_label"],
                "answers": answers,
            })
    return out


@app.post("/api/assess", response_model=AssessResponse)
def assess(req: AssessRequest):
    answers = req.answers or {}
    classification = classify(answers)
    security = assess_security(answers)
    assessment = {
        "id": storage.new_id(answers.get("sys_name")),
        "created_at": storage.now_iso(),
        "answers": answers,
        "classification": classification,
        "security": security,
    }
    storage.save(assessment)
    return AssessResponse(
        id=assessment["id"],
        created_at=assessment["created_at"],
        classification=Classification(**classification),
        security=security,
    )


@app.get("/api/assessments", response_model=list[AssessmentSummary])
def list_assessments():
    return [AssessmentSummary(**s) for s in storage.list_all()]


@app.get("/api/export.csv")
def export_csv():
    """Export the assessment inventory as a CSV register."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "sys_name", "tier", "tier_label", "security_risks", "created_at"])
    for r in storage.list_all():
        writer.writerow([r["id"], r["sys_name"], r["tier"], r["tier_label"],
                         r.get("security_risks", 0), r["created_at"]])
    return PlainTextResponse(
        buf.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ai-act-inventory.csv"})


@app.get("/api/assessments/{assessment_id}")
def get_assessment(assessment_id: str):
    data = storage.load(assessment_id)
    if not data:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return data


@app.delete("/api/assessments/{assessment_id}")
def delete_assessment(assessment_id: str):
    if not storage.delete(assessment_id):
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {"deleted": assessment_id}


@app.get("/api/assessments/{assessment_id}/report", response_model=ReportResponse)
def get_report(assessment_id: str, type: str = "risk"):
    if type not in reports.REPORT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown type: {type}")
    data = storage.load(assessment_id)
    if not data:
        raise HTTPException(status_code=404, detail="Assessment not found")
    rtype, filename, markdown = reports.render(type, data)
    return ReportResponse(type=rtype, filename=filename, markdown=markdown)


# Static frontend. Mounted last so that /api/* takes precedence.
if STATIC_DIR.exists():
    @app.get("/")
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
