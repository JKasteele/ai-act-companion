"""Curated evidence for the portfolio case. All organisations and records are fictional.

The contradictions are authored test fixtures, not findings discovered by a model.
Live AI can inspect this material through the read-only tools in agent.py.
"""

from copy import deepcopy

CASE = {
    "id": "meridian-member-assistant-v1",
    "name": "Member service assistant",
    "organisation": "Meridian Health",
    "synthetic": True,
    "documents": [
        {
            "id": "business", "title": "Business proposal", "version": "1.2",
            "owner": "Customer Contact", "date": "2026-08-24", "kind": "Business context",
            "summary": "Purpose, scope, data assumptions, and the intended launch decision.",
            "sections": [
                {"id": "purpose", "title": "Purpose and boundaries", "text": "The assistant answers member questions about policy coverage and retrieves the authenticated member's claim status. It does not determine insurance eligibility, premiums, coverage, claim payment, or fraud outcomes. It hands these decisions to employees. Meridian Health is an EU-based deployer integrating a vendor's model, not a general-purpose model provider."},
                {"id": "data", "title": "Data handling assumption", "text": "No health data is sent to the external language model. Claim information is displayed only in the secure member portal. The model receives the member's question and public policy information."},
                {"id": "oversight", "title": "Proposed change", "text": "The next pilot introduces a tool to update member contact details. An employee must approve each proposed update before execution. There is no evidence of implemented approval enforcement in this proposal."},
            ],
        },
        {
            "id": "architecture", "title": "Architecture notes", "version": "0.9",
            "owner": "AI Engineering", "date": "2026-08-28", "kind": "Technical evidence",
            "summary": "Retrieval, claim-status tools, and the external model boundary.",
            "sections": [
                {"id": "flow", "title": "Request flow", "text": "An authenticated member submits a question. The orchestrator retrieves public policy passages and invokes get_claim_status using the member's delegated identity. The response is scoped to that member. The model creates the answer; an employee can take over the conversation."},
                {"id": "payload", "title": "Model request payload", "text": "The claim-status response includes treatment description, care provider, service date, and payment status. The orchestrator appends the full tool response to the external model's conversation context. Payload redaction is listed as a future improvement; a sanitisation test has not been supplied."},
                {"id": "permissions", "title": "Write access and approval", "text": "The current pilot is read-only. The proposed update_member_contact tool is not enabled yet. The design relies on an approval instruction in the agent prompt; a server-side approval token or permission check has not been demonstrated. Retrieved policy documents can be edited by the content team."},
            ],
        },
        {
            "id": "vendor", "title": "Model vendor guide", "version": "3.0",
            "owner": "Vendor Management", "date": "2026-08-26", "kind": "Supplier evidence",
            "summary": "Illustrative hosting, logging, and retention settings from a fictional vendor.",
            "sections": [
                {"id": "retention", "title": "Logging and retention", "text": "The example service retains request and response content in abuse-monitoring logs for 30 days by default. Reduced-retention settings require an account-level arrangement. No confirmation of those settings for Meridian Health is included in this evidence pack."},
                {"id": "hosting", "title": "Hosting configuration", "text": "EU-region processing is available, but the selected account region and the scope of any support access must be checked against the actual agreement. Availability of a vendor option does not establish that it is enabled."},
            ],
        },
        {
            "id": "governance", "title": "Governance checklist", "version": "0.4",
            "owner": "Data & AI Governance", "date": "2026-08-29", "kind": "Review requirements",
            "summary": "Internal review criteria, accountable roles, and outstanding evidence.",
            "sections": [
                {"id": "gate", "title": "Internal review gate", "text": "Before the pilot can expand, the accountable owner must document the model-boundary data flow, obtain privacy review of the actual data use, and record the agreed vendor retention configuration. These are internal case-review criteria, not a statement of universal statutory requirements."},
                {"id": "controls", "title": "Evidence for write tools", "text": "Before enabling a write tool, the security reviewer requests a server-enforced approval check, tests demonstrating that unapproved calls are rejected, and a trace linking the proposal, approver, and execution. A written policy or prompt alone is not implementation evidence."},
                {"id": "status", "title": "Review status", "text": "The system owner is the Head of Customer Contact. The data steward is not yet assigned. The assessment is a draft; no launch approval has been recorded. AI-generated suggestions must be reviewed by the accountable human reviewer."},
            ],
        },
    ],
    "findings": [
        {
            "id": "data", "title": "Conflicting descriptions of health data",
            "kind": "Evidence conflict", "priority": "High",
            "description": "The business proposal excludes health data from model requests, while the architecture describes sending the full claim-status payload. Confirm the actual boundary before relying on either document.",
            "sources": ["business:data", "architecture:payload"],
            "basis": "Internal data-flow review criterion", "basis_source": "governance:gate",
            "action": "Confirm the deployed payload, document the actual data flow, and obtain privacy review of that use.",
            "owner": "AI Engineering + Privacy",
            "completion": "An inspected payload or sanitisation test, a corrected data-flow record, and the privacy review outcome.",
        },
        {
            "id": "oversight", "title": "Human approval is stated, not evidenced",
            "kind": "Control evidence gap", "priority": "High for proposed write access",
            "description": "The proposed write tool depends on an approval instruction in the prompt. The evidence does not demonstrate a server-enforced approval boundary. Keep the existing read-only pilot separate from the proposed change.",
            "sources": ["business:oversight", "architecture:permissions"],
            "basis": "Internal security review criterion", "basis_source": "governance:controls",
            "action": "Demonstrate server-side approval enforcement before enabling the write tool; retain read-only access until reviewed.",
            "owner": "AI Engineering + Security",
            "completion": "A rejected unapproved tool-call test and a trace linking an approved request to execution.",
        },
        {
            "id": "retention", "title": "Model log retention needs a decision",
            "kind": "Unconfirmed configuration", "priority": "Review needed",
            "description": "The vendor describes a default retention period and an optional reduction. Neither proves which setting applies to this deployment.",
            "sources": ["vendor:retention", "vendor:hosting"],
            "basis": "Internal supplier review criterion", "basis_source": "governance:gate",
            "action": "Confirm the account-specific region and log retention, and record the responsible owner's decision.",
            "owner": "Vendor Management + Privacy",
            "completion": "Account-specific configuration or contractual evidence and a recorded retention decision.",
        },
    ],
}


def get_case():
    return deepcopy(CASE)


def read_evidence(source_id):
    """Read only an allowlisted document or section; never a filesystem path."""
    doc_id, _, section_id = source_id.partition(":")
    for doc in CASE["documents"]:
        if doc["id"] == doc_id:
            if not section_id:
                return deepcopy(doc)
            for section in doc["sections"]:
                if section["id"] == section_id:
                    return {"source": source_id, "document": doc["title"], **section}
    raise ValueError("Unknown evidence source")


def valid_sources():
    return {f"{d['id']}:{s['id']}" for d in CASE["documents"] for s in d["sections"]}
