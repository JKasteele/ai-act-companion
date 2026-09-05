"""Review state has explicit unknowns. Human statements are never proof of a control."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .case import get_case


class ActionUpdate(BaseModel):
    owner: str = Field(default="", max_length=200)
    status: Literal["open", "in_progress", "ready_for_review"] = "open"
    evidence: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def evidence_for_review(self):
        if self.status == "ready_for_review" and not self.evidence.strip():
            raise ValueError("A completion-evidence reference is required before review.")
        return self


class ReviewState(BaseModel):
    data_route: Literal["unknown", "raw", "redacted"] = "unknown"
    data_note: str = Field(default="", max_length=2000)
    oversight: Literal["unknown", "prompt", "server"] = "unknown"
    oversight_note: str = Field(default="", max_length=2000)
    actions: dict[Literal["data", "oversight", "retention"], ActionUpdate] = Field(
        default_factory=dict, max_length=3,
    )


def review_summary(state: ReviewState):
    findings = get_case()["findings"]
    for finding in findings:
        finding["status"] = "Needs evidence"
        finding["reviewer_statement"] = None
        if finding["id"] == "data" and state.data_route != "unknown":
            finding["status"] = "Clarified; evidence review open"
            finding["reviewer_statement"] = {
                "value": state.data_route, "note": state.data_note,
                "provenance": "Reviewer statement; not independently verified",
            }
        if finding["id"] == "oversight" and state.oversight != "unknown":
            finding["status"] = "Clarified; evidence review open"
            finding["reviewer_statement"] = {
                "value": state.oversight, "note": state.oversight_note,
                "provenance": "Reviewer statement; not independently verified",
            }
        action = state.actions.get(finding["id"])
        if action:
            finding["action_status"] = action.status
            finding["action_owner"] = action.owner
            finding["completion_evidence"] = action.evidence
    return {
        "findings": findings, "decision": "Draft; human review required",
        "open_findings": len(findings), "state": state.model_dump(),
        "notice": "Clarification and supplied evidence references do not automatically close findings or approve launch.",
    }
