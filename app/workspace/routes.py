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

router = APIRouter(prefix="/api/workspace", tags=["Evidence workspace"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    state: ReviewState = Field(default_factory=ReviewState)


class AssessmentRequest(BaseModel):
    confirm_synthetic_profile: bool = False


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
