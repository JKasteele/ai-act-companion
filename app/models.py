"""Pydantic request/response models for the API.

The intake answers are kept loosely validated (free-form dict) so the
questionnaire can evolve without breaking the models. The classifier
normalises the values.
"""

from typing import Any

from pydantic import BaseModel, Field


class AssessRequest(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)


# --- AI layer (phase 4) ---
class PrefillRequest(BaseModel):
    description: str = ""


class ParseRequest(BaseModel):
    text: str = ""


class NarrativeRequest(BaseModel):
    field: str
    answers: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    tier: str
    refs: list[str]
    title: str
    rationale: str
    source_questions: list[str] = Field(default_factory=list)


class Classification(BaseModel):
    tier: str
    tier_label: str
    tier_description: str
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    transparency_obligations: list[Finding] = Field(default_factory=list)
    gpai_obligations: list[Finding] = Field(default_factory=list)
    high_risk_obligations: list[list[str]] = Field(default_factory=list)
    nist_crosswalk: list[list[str]] = Field(default_factory=list)
    recommended_artifacts: list[str] = Field(default_factory=list)
    applicability: dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = ""


class AssessResponse(BaseModel):
    id: str
    created_at: str
    classification: Classification
    security: dict[str, Any] = Field(default_factory=dict)


class AssessmentSummary(BaseModel):
    id: str
    sys_name: str
    tier: str
    tier_label: str
    security_risks: int = 0
    created_at: str


class ReportResponse(BaseModel):
    type: str
    filename: str
    markdown: str
