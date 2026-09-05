"""Stateless workspace API. Each visitor supplies their own bounded review state."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..classifier import classify
from ..knowledge.eu_ai_act import KNOWLEDGE_VERSION
from ..llm.config import settings
from ..security import assess_security
from .agent import AgentUnavailable, run_agent
from .case import get_case
from .review import ReviewState, review_summary
from .toolkit import assess_answers, catalogue, dispatch, missing_screening, validate_answers

router = APIRouter(prefix="/api/workspace", tags=["Evidence workspace"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    state: ReviewState = Field(default_factory=ReviewState)


class AssessmentRequest(BaseModel):
    confirm_synthetic_profile: bool = False


class EvidenceNote(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=10_000)
    reference: str = Field(default="", max_length=300)


class SystemChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    answers: dict = Field(default_factory=dict, max_length=300)
    evidence: list[EvidenceNote] = Field(default_factory=list, max_length=30)
    assessment_confirmed: bool = False
    example_id: str = Field(default="", max_length=100)


@router.post("/system-chat")
def system_chat(req: SystemChatRequest, request: Request):
    import json

    try:
        answers = validate_answers(req.answers)
        documents = [{"id": "system", "title": "Recorded system profile", "sections": [
            {"id": "profile", "title": "Structured answers (reviewer statements)",
             "text": json.dumps(answers)},
        ]}]
        documents += [{"id": f"evidence{i}", "title": note.title, "sections": [
            {"id": "passage", "title": note.reference or "Reviewer-provided evidence",
             "text": note.text},
        ]} for i, note in enumerate(req.evidence)]
        review_data = {"missing_screening": missing_screening(answers),
                       "assessment": assess_answers(answers) if req.assessment_confirmed else None,
                       "notice": "Reviewer-provided profile and evidence; no approval or verified controls."}
        return run_agent(req.message, ReviewState(), request.client.host if request.client else None,
                         documents=documents, review_data=review_data)
    except AgentUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/catalogue")
def toolkit_catalogue():
    return catalogue()


@router.post("/toolkit")
def toolkit_request(payload: dict):
    try:
        return dispatch(payload)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc


def scenario_assessment():
    """Reuse the existing synthetic service-assistant answers without AI mutations."""
    import json

    path = Path(__file__).resolve().parents[2] / "examples/health_insurer_service_assistant.json"
    answers = json.loads(path.read_text(encoding="utf-8"))
    answers["sys_name"] = "Meridian Health member service assistant (read-only pilot)"
    return {
        "classification": classify(answers), "security": assess_security(answers),
        "knowledge_version": KNOWLEDGE_VERSION, "answers": answers,
        "scope": "Existing synthetic read-only service-assistant profile. Proposed write access is not included.",
        "provenance": "Computed by the repository's deterministic engine from the linked scenario inputs.",
        "draft": True,
    }


@router.get("/case")
def case():
    return {**get_case(), "live_configured": settings.provider in {"ollama", "anthropic"},
            "provider": settings.provider,
            "notice": "Guided mode uses curated case findings; live AI is optional and explicitly selected."}


@router.post("/review")
def review(state: ReviewState):
    return review_summary(state)


@router.post("/assess")
def assess(req: AssessmentRequest):
    if not req.confirm_synthetic_profile:
        raise HTTPException(422, "Confirm the synthetic read-only profile before running the engine.")
    return scenario_assessment()


@router.post("/chat")
def chat(req: ChatRequest, request: Request):
    try:
        return run_agent(req.message, req.state, request.client.host if request.client else None)
    except AgentUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
