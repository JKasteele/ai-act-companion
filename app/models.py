"""Pydantic request/response models for the API.

The intake answers are kept loosely validated (free-form dict) so the
questionnaire can evolve without breaking the models. The classifier
normalises the values.
"""

import json
from typing import Any

from pydantic import BaseModel, Field, model_validator

MAX_NAME_LENGTH = 200
MAX_FREE_TEXT_LENGTH = 10_000
MAX_ANSWERS_BYTES = 100_000
MAX_ANSWER_FIELDS = 300
MAX_ANSWER_DEPTH = 8


def _validate_answer_value(value: Any, depth: int = 0) -> None:
    """Bound user-controlled questionnaire values, including nested tables."""
    if depth > MAX_ANSWER_DEPTH:
        raise ValueError(f"Answers may be nested at most {MAX_ANSWER_DEPTH} levels.")
    if isinstance(value, str) and len(value) > MAX_FREE_TEXT_LENGTH:
        raise ValueError(
            f"Answer text must be at most {MAX_FREE_TEXT_LENGTH} characters.")
    if isinstance(value, dict):
        if len(value) > MAX_ANSWER_FIELDS:
            raise ValueError(f"Nested objects may contain at most {MAX_ANSWER_FIELDS} fields.")
        for key, nested in value.items():
            if len(str(key)) > 200:
                raise ValueError("Answer field names must be at most 200 characters.")
            _validate_answer_value(nested, depth + 1)
    elif isinstance(value, (list, tuple)):
        if len(value) > MAX_ANSWER_FIELDS:
            raise ValueError(f"Answer lists may contain at most {MAX_ANSWER_FIELDS} items.")
        for nested in value:
            _validate_answer_value(nested, depth + 1)


class AssessRequest(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_answers(self):
        name = self.answers.get("sys_name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("A non-empty system name is required.")
        if len(name.strip()) > MAX_NAME_LENGTH:
            raise ValueError(f"System name must be at most {MAX_NAME_LENGTH} characters.")
        if len(self.answers) > MAX_ANSWER_FIELDS:
            raise ValueError(f"Answers may contain at most {MAX_ANSWER_FIELDS} fields.")
        _validate_answer_value(self.answers)
        if len(json.dumps(self.answers, ensure_ascii=False).encode("utf-8")) > MAX_ANSWERS_BYTES:
            raise ValueError(f"Answers must be at most {MAX_ANSWERS_BYTES} bytes in total.")
        self.answers["sys_name"] = name.strip()
        return self


# --- AI layer (phase 4) ---
class PrefillRequest(BaseModel):
    description: str = Field(default="", max_length=MAX_FREE_TEXT_LENGTH)


class ParseRequest(BaseModel):
    text: str = Field(default="", max_length=MAX_FREE_TEXT_LENGTH)


class NarrativeRequest(BaseModel):
    field: str = Field(min_length=1, max_length=200)
    answers: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_answers_size(self):
        _validate_answer_value(self.answers)
        if len(json.dumps(self.answers, ensure_ascii=False).encode("utf-8")) > MAX_ANSWERS_BYTES:
            raise ValueError(f"Answers must be at most {MAX_ANSWERS_BYTES} bytes in total.")
        return self


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
    persisted: bool = True


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
