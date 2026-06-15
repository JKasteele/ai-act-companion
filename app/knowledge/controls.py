"""Defensive control-catalogue knowledge base.

Declarative templates for the **defensive** counterpart of the red-team test
plan. Each template is keyed to an OWASP Top 10 for LLM Applications (2025) item
and describes a *control to implement*, not an attack to run. It is the blue-team
mirror of `red_team.py`: where a red-team test asks "can this risk be exploited?",
the matching control answers "what do we put in place so it can't?" — and each
control names the red-team test case(s) (`validated_by`) that would verify it.

The generator (`app/controls.py`) selects and prioritises these for a specific
system: a control's priority is the architecture-aware *severity* of its parent
OWASP risk (the same number the red-team plan uses), and conditional controls are
gated on the architecture via the *same* gate vocabulary the test plan uses
(`red_team.GATES`, evaluated by `redteam.architecture_flags`/`gate_open`), so
offense and defense never disagree about whether e.g. retrieved content is
untrusted.

Framework anchors. Each control names the NIST CSF 2.0 function(s) it sits under
and the ISO/IEC 27001:2022 Annex A control(s) it maps to — using only the public
control titles already encoded in `security_frameworks.py`. The EU AI Act / NIST
AI RMF references and the mitigation summary are taken from the parent OWASP item
in `ai_security.py` (single source of truth), so they are not duplicated here.

These are control *designs* for a self-assessment, not a hardening script; they
describe what to implement and how to verify it, not product-specific config.
"""

# base OWASP id -> list of control templates (highest-value first). Fields:
#   ref          stable control id (CTL-LLMxx-yy)
#   title        what the control is
#   gate         None (always applies when the parent risk fires) or a
#                red_team.GATES key (applies only under that architecture)
#   control      the defensive measure to implement (methodology-level)
#   intent       the failure it prevents (one line)
#   verify       how to confirm it is actually in place
#   validated_by red-team test case ref(s) that exercise this control
#   csf          NIST CSF 2.0 function code(s) the control sits under
#   iso          ISO/IEC 27001:2022 Annex A control id(s) — must exist in
#                security_frameworks.ISO_27001_2022 (public titles only)
CONTROLS = {
    "LLM01": [
        {
            "ref": "CTL-LLM01-01",
            "title": "Separate trusted instructions from untrusted input",
            "gate": None,
            "control": "Keep the system instructions in a channel the user "
                       "cannot edit, constrain and validate user input, and "
                       "never let input redefine the task or the guardrails. "
                       "Give the model least-privilege access to any tools.",
            "intent": "Contain direct prompt injection / instruction override.",
            "verify": "A direct-injection attempt (RT-LLM01-01) cannot make the "
                      "model disregard its system prompt or task schema.",
            "validated_by": ["RT-LLM01-01"],
            "csf": ["PR"],
            "iso": ["A.8.26", "A.8.28"],
        },
        {
            "ref": "CTL-LLM01-02",
            "title": "Treat retrieved/ingested content as data, never as instructions",
            "gate": "indirect",
            "control": "Track the provenance of retrieved content, keep a trust "
                       "boundary between the RAG corpus / inbound documents and "
                       "the system prompt, and neutralise instruction-like markup "
                       "before content reaches the model.",
            "intent": "Stop indirect (retrieved-content) prompt injection.",
            "verify": "Seeded instructions in a retrieved source (RT-LLM01-02) do "
                      "not change the model's behaviour or actions.",
            "validated_by": ["RT-LLM01-02"],
            "csf": ["PR"],
            "iso": ["A.8.26"],
        },
    ],
    "LLM02": [
        {
            "ref": "CTL-LLM02-01",
            "title": "Minimise and filter sensitive data in context and output",
            "gate": None,
            "control": "Minimise the personal/confidential data placed in the "
                       "context window, redact/scrub PII on the way in and filter "
                       "it on the way out, and limit memorisation of sensitive "
                       "training data.",
            "intent": "Prevent sensitive-information disclosure via outputs.",
            "verify": "Crafted / incremental disclosure probing (RT-LLM02-01) does "
                      "not return data the session should not see.",
            "validated_by": ["RT-LLM02-01"],
            "csf": ["PR"],
            "iso": ["A.5.12", "A.8.26"],
        },
        {
            "ref": "CTL-LLM02-02",
            "title": "Enforce per-request authorization at the data/API layer, not in the prompt",
            "gate": "cross_tenant",
            "control": "Move access control out of the model: scope every "
                       "retrieval and backend call to the requesting identity, "
                       "deny cross-tenant access by default, and never rely on the "
                       "model honouring a prompt-level scoping rule.",
            "intent": "Prevent cross-tenant / out-of-scope data access.",
            "verify": "A low-privilege identity cannot reach another user's data "
                      "(RT-LLM02-02 / RT-LLM08-01); enforcement is server-side.",
            "validated_by": ["RT-LLM02-02", "RT-LLM08-01"],
            "csf": ["PR"],
            "iso": ["A.5.12"],
        },
    ],
    "LLM03": [
        {
            "ref": "CTL-LLM03-01",
            "title": "Vet and pin the model, data and dependency supply chain",
            "gate": None,
            "control": "Maintain an AIBOM/SBOM, pin model/dataset/dependency "
                       "versions, verify signatures or hashes, scan dependencies "
                       "in CI, and vet the provenance of third-party models and "
                       "datasets.",
            "intent": "Prevent supply-chain compromise of integrity or security.",
            "verify": "A supply-chain integrity review (RT-LLM03-01) finds every "
                      "model/dataset/dependency has verified, pinned provenance.",
            "validated_by": ["RT-LLM03-01"],
            "csf": ["ID"],
            "iso": ["A.5.7", "A.5.9"],
        },
    ],
    "LLM04": [
        {
            "ref": "CTL-LLM04-01",
            "title": "Validate and monitor data entering training / RAG pipelines",
            "gate": "indirect",
            "control": "Vet data sources, run integrity checks and anomaly "
                       "detection on ingestion, track provenance, and keep "
                       "ingested data quarantined from production until it is "
                       "validated.",
            "intent": "Prevent data/model poisoning and backdoors.",
            "verify": "Anomalous samples introduced into a controlled ingestion "
                      "path (RT-LLM04-01) are detected and do not shift behaviour.",
            "validated_by": ["RT-LLM04-01"],
            "csf": ["PR"],
            "iso": ["A.5.9", "A.8.16"],
        },
    ],
    "LLM05": [
        {
            "ref": "CTL-LLM05-01",
            "title": "Treat model output as untrusted before any downstream use",
            "gate": "agentic_or_write",
            "control": "Encode/escape model output, validate it against a schema, "
                       "and sandbox any downstream interpreter (HTML/JS, SQL, "
                       "shell, code, a browser). Never pass raw output to an "
                       "execution sink and never eval it.",
            "intent": "Prevent injection / XSS / RCE from improper output handling.",
            "verify": "Output induced to contain markup/query/code (RT-LLM05-01) is "
                      "treated as data by the downstream component, not executed.",
            "validated_by": ["RT-LLM05-01"],
            "csf": ["PR"],
            "iso": ["A.8.26", "A.8.28"],
        },
    ],
    "LLM06": [
        {
            "ref": "CTL-LLM06-01",
            "title": "Constrain agency: least-privilege tools + human approval for consequential actions",
            "gate": "agentic_or_write",
            "control": "Give tools the narrowest scopes and permissions that work, "
                       "require human approval for high-impact or irreversible "
                       "actions, and make every action logged and reversible.",
            "intent": "Prevent excessive-agency abuse on ambiguous/manipulated input.",
            "verify": "Attempts to drive an out-of-scope action (RT-LLM06-01) are "
                      "blocked by permission scopes or a human-approval gate.",
            "validated_by": ["RT-LLM06-01"],
            "csf": ["PR"],
            "iso": ["A.8.26"],
        },
    ],
    "LLM07": [
        {
            "ref": "CTL-LLM07-01",
            "title": "Keep secrets and authorization logic out of the system prompt",
            "gate": None,
            "control": "Treat the system prompt as public: enforce all access "
                       "control server-side, and put no credentials, keys or "
                       "security-relevant business rules in the prompt.",
            "intent": "Make system-prompt leakage harmless.",
            "verify": "Even if the prompt is extracted (RT-LLM07-01), it contains "
                      "no secret or control relied upon for security.",
            "validated_by": ["RT-LLM07-01"],
            "csf": ["PR"],
            "iso": ["A.8.26"],
        },
    ],
    "LLM08": [
        {
            "ref": "CTL-LLM08-01",
            "title": "Access-control and tenant-isolate the vector store; validate ingested documents",
            "gate": None,
            "control": "Scope retrieval to the requesting identity, isolate "
                       "tenants in the vector store, validate documents on ingest, "
                       "and audit what is retrieved.",
            "intent": "Prevent cross-boundary retrieval leakage and RAG poisoning.",
            "verify": "Retrieval isolation testing (RT-LLM08-01) returns no "
                      "out-of-scope documents and rejects context-poisoning inserts.",
            "validated_by": ["RT-LLM08-01"],
            "csf": ["PR"],
            "iso": ["A.5.12", "A.8.16"],
        },
    ],
    "LLM09": [
        {
            "ref": "CTL-LLM09-01",
            "title": "Ground and label outputs; review where they drive decisions",
            "gate": None,
            "control": "Ground answers in retrieval with citations, signal "
                       "uncertainty, label AI-generated output (Art. 50), and keep "
                       "a human reviewing outputs that are relied upon for a "
                       "decision.",
            "intent": "Prevent confident misinformation being relied upon.",
            "verify": "Edge-case / unanswerable probing (RT-LLM09-01) yields "
                      "grounded, uncertainty-flagged or human-reviewed output.",
            "validated_by": ["RT-LLM09-01"],
            "csf": ["GV"],
            "iso": ["A.5.1"],
        },
    ],
    "LLM10": [
        {
            "ref": "CTL-LLM10-01",
            "title": "Rate-limit, quota and cost-cap; monitor anomalous usage",
            "gate": None,
            "control": "Enforce rate limits, quotas and cost caps, bound input "
                       "and output sizes, and monitor and alert on anomalous "
                       "volume or systematic extraction-style query patterns.",
            "intent": "Prevent unbounded consumption, cost harvesting and extraction.",
            "verify": "High-volume / expensive / systematic requests (RT-LLM10-01) "
                      "are throttled and raise an alert.",
            "validated_by": ["RT-LLM10-01"],
            "csf": ["DE"],
            "iso": ["A.8.15", "A.8.16"],
        },
    ],
}

PROVENANCE = (
    "Controls are a Companion-derived defensive design, traceable to the verified "
    "OWASP Top 10 for LLM Applications (2025) items in the security lens and "
    "anchored to public NIST CSF 2.0 functions and ISO/IEC 27001:2022 Annex A "
    "control titles — not an official published control set. Framework citations "
    "are analytical alignments, not certifications."
)

DISCLAIMER = (
    "This is a prioritised **control catalogue** to guide hardening; it is a "
    "self-assessment aid, not a guarantee of compliance or security. Each control "
    "names the red-team test case that verifies it — implement, then test."
)
