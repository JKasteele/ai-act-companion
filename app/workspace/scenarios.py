"""Fictional portfolio dossiers. Findings and proposals are authored, never AI claims.

Every source describes the fictional deployment on the stated review date.
Internal acceptance criteria are not presented as universal legal requirements.
"""

from copy import deepcopy

from .case import get_case


def document(id, title, owner, version, date, sections):
    return {"id": id, "title": title, "owner": owner, "version": version, "date": date,
            "sections": [{"id": key, "title": heading, "text": text} for key, heading, text in sections]}


def proposal(field, value, source, quote, reason):
    return {"field": field, "value": value, "source": source, "quote": quote, "reason": reason}


def finding(id, title, description, sources, owner, action, completion, priority="High"):
    return {"id": id, "title": title, "description": description, "sources": sources,
            "owner": owner, "action": action, "completion": completion, "priority": priority,
            "basis": "Fictional organisation's internal review criteria"}


def scenarios():
    meridian = get_case()
    health = {
        "id": "meridian", "organisation": "Meridian Health", "sector": "Health insurance",
        "name": "Member service assistant", "stage": "Pilot expansion review",
        "brief": "A member-support pilot works well enough to expand. The product owner wants contact-detail updates next, but the privacy and engineering documents disagree about what reaches the model.",
        "decision": "What must be evidenced before expanding the read-only pilot to write access?",
        "owner": "Head of Customer Contact", "date": "2026-09-03",
        "reports": ["risk", "dpia", "security", "controls", "governance"],
        "documents": meridian["documents"] + [document("pilot", "Pilot review minutes", "Service Operations", "1.0", "2026-09-03", [
            ("results", "Observed service performance", "In the fictional August pilot, 18 service employees reviewed 240 synthetic member conversations. Coverage answers were accepted without correction in 211 conversations; 29 were escalated. These figures measure service usefulness, not privacy or security assurance. The test set included no hostile retrieved documents."),
            ("decision", "Review meeting outcome", "The group agreed to keep contact-detail updates disabled. Engineering will supply an inspected model request and a denied unapproved-write trace. Privacy requested account-specific retention evidence. The Head of Customer Contact requested a follow-up review on 10 September; this minute records no expansion approval."),
        ])],
        "findings": meridian["findings"],
        "proposals": [
            proposal("provider_role", "deployer", "business:purpose", "Meridian Health is an EU-based deployer integrating a vendor's model", "The business owner explicitly describes the organisation's role."),
            proposal("eu_market", True, "business:purpose", "Meridian Health is an EU-based deployer", "The declared deployment context is in the EU."),
            proposal("arch_api_write", False, "architecture:permissions", "The current pilot is read-only.", "Assess the current pilot separately from the proposed write tool."),
            proposal("arch_data_scope", "own-user", "architecture:flow", "The response is scoped to that member.", "The architecture states a per-member scope; this is not proof of enforcement."),
            proposal("data_personal", True, "architecture:payload", "treatment description, care provider, service date, and payment status", "The described payload includes member-linked claim information."),
        ],
    }
    water = {
        "id": "boreal", "organisation": "Boreal Water Operations", "sector": "Water infrastructure",
        "name": "FlowWatch operations copilot", "stage": "Shadow-mode exit review",
        "brief": "A regional water operator uses an agent to summarise alarms and propose pump schedules. A supplier calls it advisory, while a connector test shows a path to operational writes. A wet-weather trial is approaching.",
        "decision": "Can the team move beyond shadow mode, and which operational boundaries remain unproven?",
        "owner": "Operations Engineering Manager", "date": "2026-09-04",
        "reports": ["risk", "security", "redteam", "forensics", "governance"],
        "documents": [
            document("brief", "FlowWatch pilot charter", "Operations Engineering", "1.3", "2026-08-21", [
                ("purpose", "Purpose and deployment", "Boreal Water Operations is a fictional EU-based deployer of a supplier's operations copilot. FlowWatch summarises station alarms, retrieves maintenance instructions and proposes pump schedules for operators. The current approved scope is shadow mode: a human decides fully and the copilot must not send commands to field equipment."),
                ("boundary", "Operational boundary", "The service supports operation of a drinking-water supply network. It is not certified as a safety controller. Existing PLC interlocks stay authoritative. The charter describes it as advisory and assumes a read-only connection; whether the proposed production integration is a safety component has not been determined."),
                ("trial", "Trial objective", "The planned wet-weather trial covers four stations and two shifts. Its purpose is to evaluate operator workload and the quality of proposed schedules. The operations manager requires a tested rollback path and a named duty engineer before changing the shadow-mode boundary."),
            ]),
            document("design", "Connector and retrieval design", "Control Systems Team", "0.8", "2026-08-28", [
                ("write", "Command path", "In staging, the agent service account holds read_alarm and set_pump_schedule permissions. The set_pump_schedule endpoint accepted request T-184 without an approval token during a connector smoke test. The UI still hides the Execute button. The staging environment uses a simulator; no field pump was changed. The proposed production role has not been exported for review."),
                ("retrieval", "Maintenance knowledge", "The agent retrieves maintenance PDFs from a shared engineering folder. A contractor can upload revised documents. Retrieved text is included in the agent's planning context. No test has yet checked whether an instruction embedded in a maintenance document can influence a tool call."),
                ("logging", "Operational trace", "Application logs record user session and tool name for seven days. They omit the retrieved-document version, proposed arguments and PLC acknowledgement. Station clocks were not compared with the application clock in the current test report."),
            ]),
            document("supplier", "Supplier assurance response", "Supplier Management", "2.1", "2026-08-26", [
                ("approval", "Human oversight claim", "The supplier describes the copilot as advisory because an operator normally selects Execute. Its default connector service role permits scheduling writes. Customers are responsible for enforcing any approval requirement at the connector boundary; a UI confirmation alone is not a documented access-control guarantee."),
                ("recovery", "Recovery procedure", "The supplier supports disabling the copilot and returning to the existing control interface. Reverting a schedule already accepted by a station requires an operator action in that interface. No Boreal-specific recovery rehearsal is supplied."),
            ]),
            document("review", "Operational readiness record", "Duty Engineering + Security", "0.3", "2026-09-04", [
                ("test", "What has been tested", "A simulator replay of 36 ordinary alarm sequences completed without application crashes. No replay covered stale telemetry, conflicting alarms, hostile maintenance text, lost connectivity, or an expired operator approval. This is functional test evidence, not proof of a safe operational deployment."),
                ("gate", "Internal review criteria", "Before a live write-enabled trial, Boreal requests a server-enforced approval boundary, bounded command arguments, safe behaviour on stale telemetry, an exercised return-to-manual procedure, and an end-to-end incident trace. These are internal case criteria. The current decision is to remain in shadow mode pending evidence and an accountable operational review."),
            ]),
        ],
        "findings": [
            finding("write", "Advisory scope conflicts with connector permissions", "A hidden Execute button does not explain the accepted unapproved staging request. Production permissions are unknown; do not claim the staging result proves a live field write.", ["brief:purpose", "design:write", "supplier:approval"], "Control Systems + Security", "Remove unnecessary write permission and demonstrate rejection of requests without a valid operator approval.", "A production-role export, denied unauthorised-call trace, and an approved simulator trace with bounded arguments."),
            finding("injection", "Untrusted maintenance documents can influence planning", "Contractor-editable retrieval content enters the planning context. The ordinary-alarm replay does not test hostile instructions.", ["design:retrieval", "review:test"], "AI Engineering + Security", "Exercise indirect prompt injection against a simulator and verify the connector rejects unsafe actions independently of model output.", "Versioned test documents, expected denied calls, actual traces and reviewer interpretation."),
            finding("recovery", "Recovery and incident reconstruction are not demonstrated", "The supplier describes a manual recovery route, but the team has neither rehearsed it nor captured enough context to reconstruct a command.", ["design:logging", "supplier:recovery", "review:gate"], "Duty Engineer + Platform", "Rehearse return to manual operation and record a trace across model context, approval, connector and simulator acknowledgement.", "A witnessed recovery record with timing and an aligned end-to-end trace."),
        ],
        "proposals": [
            proposal("provider_role", "deployer", "brief:purpose", "EU-based deployer of a supplier's operations copilot", "The charter names the deployment role."),
            proposal("eu_market", True, "brief:purpose", "EU-based deployer", "The fictional deployment is in the EU."),
            proposal("autonomy_level", "advisory", "brief:purpose", "a human decides fully", "This is the declared shadow-mode scope, not assurance about connector permissions."),
            proposal("hr_usecases", ["critical_infra"], "brief:boundary", "operation of a drinking-water supply network", "This use context warrants critical-infrastructure screening; applicability still requires review."),
        ],
    }
    hiring = {
        "id": "northstar", "organisation": "Northstar Services", "sector": "Recruitment",
        "name": "Shortlist recruitment assistant", "stage": "Procurement review",
        "brief": "A growing services company wants to reduce recruiter workload. The vendor promises decision support, but a proposed workflow removes low-ranked applicants before recruiter review. The validation pack gives little visibility into who was tested.",
        "decision": "Which workflow, data, and candidate safeguards need clarification before procurement proceeds?",
        "owner": "Head of Talent Acquisition", "date": "2026-09-02",
        "reports": ["risk", "fria", "dpia", "governance", "security"],
        "documents": [
            document("business", "Recruitment requirements", "Talent Acquisition", "1.1", "2026-08-20", [
                ("purpose", "Recruitment use", "Northstar Services is a fictional EU-based deployer procuring a vendor's recruitment assistant. Shortlist compares CVs with a vacancy description and ranks applicants for recruiter review. It analyses personal CV information, employment history and qualifications. The purchasing team describes it as decision support: every candidate should remain available for a human decision."),
                ("scope", "Pilot population", "The proposed pilot covers Dutch- and English-language applications for customer-service roles. No use of facial analysis, voice analysis or emotion inference is included. The stated objective is to reduce manual sorting time, not predict personality or future misconduct."),
            ]),
            document("workflow", "Applicant tracking integration", "HR Systems", "0.6", "2026-08-27", [
                ("filter", "Score-based filtering", "The proposed integration sets applications below score 60 to not-progressing overnight and removes them from the recruiter's default queue. A recruiter can find them through an archived-results filter. The design does not require review of each application before this status change. Rejection emails remain disabled in the test environment."),
                ("features", "Scoring inputs", "The score uses extracted qualifications, employment-gap duration and similarity to previously shortlisted applicants. The model vendor does not expose per-feature weights. Employment gaps can reflect caring responsibilities or disability; the team has not evaluated those effects in this workflow."),
                ("access", "Access and retention", "Recruiters sign in through corporate SSO. The connector uses a shared organisation-wide token to read CVs. Removing an applicant in the tracking system does not trigger deletion of the vendor's extracted profile; the integration backlog contains a deletion callback but no implementation test."),
            ]),
            document("vendor", "Validation and product statement", "Procurement", "2.4", "2026-08-25", [
                ("metrics", "Reported validation", "The vendor reports 87% agreement with historical recruiter shortlists on 2,400 English-language applications from several sectors. The pack contains no Dutch-language result, subgroup breakdown, label-quality review or explanation of how historical recruiter preferences were checked for bias. This metric is agreement with past decisions, not proof of fair outcomes."),
                ("retention", "Data processing options", "The standard configuration retains extracted applicant profiles for twelve months. An earlier deletion can be requested through a support process. The draft contract has not recorded Northstar's selected retention period or responsibility for deletion confirmation."),
                ("oversight", "Decision-support statement", "The vendor markets Shortlist as a recommendation service. Customers configure the applicant tracking workflow and must determine how recommendations affect candidates. The product statement does not validate Northstar's overnight filtering rule."),
            ]),
            document("review", "People and privacy review note", "HR Governance + Privacy", "0.2", "2026-09-02", [
                ("criteria", "Internal acceptance criteria", "Before procurement approval, the review group requests a documented actual decision workflow, role- and language-relevant validation, a reviewer override process, candidate-facing explanation and contact route, and an agreed deletion process. These are Northstar's internal criteria; the note does not declare legal compliance."),
                ("status", "Open decisions", "The Head of Talent Acquisition owns the use decision. Privacy has not accepted a retention period. No one is assigned to monitor subgroup outcomes after rollout. Procurement remains open, and the draft recommendation is to remove automatic status changes until the workflow has been reviewed."),
            ]),
        ],
        "findings": [
            finding("oversight", "The workflow filters candidates before human review", "The business promise of a human decision for every applicant is not reflected in the overnight status change. An archived-results filter is not evidence of routine review.", ["business:purpose", "workflow:filter", "vendor:oversight"], "Talent Acquisition + HR Systems", "Map the actual candidate journey and remove automatic progression changes pending a reviewed oversight design.", "A revised workflow, tests of reviewer access and override, and a documented accountable use decision."),
            finding("validation", "Supplier validation does not cover the intended population", "Agreement with historical English-language shortlists does not establish performance for Dutch applications or fair outcomes across relevant groups.", ["business:scope", "workflow:features", "vendor:metrics"], "Data Science + HR Governance", "Agree appropriate evaluation criteria and evaluate a lawful, representative test set for the intended roles and languages.", "A dataset rationale, label review, relevant performance and subgroup analysis, limitations and a monitoring owner."),
            finding("deletion", "Applicant deletion stops at the tracking system", "An unimplemented callback and an optional support process do not show that vendor profiles are removed when applicants are deleted.", ["workflow:access", "vendor:retention", "review:status"], "HR Systems + Privacy", "Agree the retention decision and verify the end-to-end deletion process with the supplier.", "An account-specific retention agreement, deletion test and confirmation that includes extracted profiles."),
        ],
        "proposals": [
            proposal("provider_role", "deployer", "business:purpose", "EU-based deployer procuring a vendor's recruitment assistant", "The purchasing team declares its role."),
            proposal("eu_market", True, "business:purpose", "EU-based deployer", "The fictional deployment is in the EU."),
            proposal("data_personal", True, "business:purpose", "personal CV information, employment history and qualifications", "These are the declared personal inputs."),
            proposal("hr_usecases", ["employment"], "business:purpose", "ranks applicants for recruiter review", "The described use is candidate ranking for recruitment."),
            proposal("arch_auth_strength", "strong-sso", "workflow:access", "Recruiters sign in through corporate SSO.", "This records the stated user authentication; it does not verify connector isolation."),
        ],
    }
    result = [health, water, hiring]
    for case in result:
        case["synthetic"] = True
        case["provenance"] = "Authored fictional dossier; findings and intake proposals are scenario material, not model discoveries."
    return deepcopy(result)
