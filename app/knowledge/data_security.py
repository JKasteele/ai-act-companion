"""OWASP GenAI Data Security knowledge base (DSGAI01-DSGAI21).

Encodes the 21 risk categories of the **OWASP GenAI Data Security Risks &
Mitigations (2026, v1.0)** as cited data, cross-mapped to the OWASP Top 10 for
LLM Applications (the project's existing security lens), the EU AI Act and the
NIST AI RMF. It is the data-layer complement to `ai_security.py`: where the
LLM Top 10 lens reasons about *application* threats, this lens reasons about the
*data* — training/fine-tuning sets, prompts, retrieved context, embeddings,
telemetry and outputs — across the GenAI lifecycle. Its natural EU AI Act anchor
is **Art. 10 (data and data governance)**, with Art. 12 (record-keeping),
Art. 15 (cybersecurity) and the GDPR where personal data is processed.

Identifier provenance:
  * The DSGAI01-DSGAI21 identifiers and titles are from the OWASP GenAI Security
    Project's "GenAI Data Security Risks & Mitigations" (2026, v1.0), verified
    against genai.owasp.org and corroborating public summaries.
  * Summaries and mitigations here are concise Companion-authored paraphrases —
    NOT the OWASP document's text. The source organises its mitigations into
    Foundational / Hardening / Advanced tiers; this module names a representative
    control rather than reproducing those tiers.
  * The DSGAI <-> OWASP LLM Top 10 <-> EU AI Act <-> NIST AI RMF mappings are a
    Companion-derived analytical alignment, traceable to verified identifiers —
    not an official published crosswalk.

Self-assessment aid, not a substitute for a data-protection or security review.
"""

# Each entry: name (verbatim DSGAI title), summary, owasp_refs (LLM Top 10 ids it
# relates to), ai_act_refs (linkifiable tokens), gdpr_refs (plain; GDPR is not on
# the AI Act Explorer), nist_refs (AI RMF subcategories), mitigation.
DSGAI = {
    "DSGAI01": {
        "name": "Sensitive Data Leakage",
        "summary": "Models and RAG systems return PII, secrets or IP through "
                   "crafted prompts, enumeration or over-permissive retrieval.",
        "owasp_refs": ["LLM02:2025", "LLM07:2025"],
        "ai_act_refs": ["Art. 10 (data governance)", "Art. 15 (cybersecurity)"],
        "gdpr_refs": ["GDPR Art. 5(1)(f) (integrity & confidentiality)", "GDPR Art. 32"],
        "nist_refs": ["MEASURE 2.7", "MEASURE 2.10"],
        "mitigation": "Data minimisation into context, PII redaction, output "
                      "filtering and scoped retrieval.",
    },
    "DSGAI02": {
        "name": "Agent Identity & Credential Exposure",
        "summary": "Agent and tool credentials, tokens or identities are exposed "
                   "or over-scoped, letting data be accessed beyond intent.",
        "owasp_refs": ["LLM06:2025", "LLM07:2025"],
        "ai_act_refs": ["Art. 15 (cybersecurity)"],
        "gdpr_refs": ["GDPR Art. 32"],
        "nist_refs": ["MEASURE 2.7"],
        "mitigation": "Per-agent least-privilege identities, short-lived secrets "
                      "in a vault, and no credentials in prompts or code.",
    },
    "DSGAI03": {
        "name": "Shadow AI & Unsanctioned Data Flows",
        "summary": "Employees use unapproved AI tools, creating uncontrolled data "
                   "flows of corporate or personal data outside any governance.",
        "owasp_refs": ["LLM03:2025"],
        "ai_act_refs": ["Art. 10 (data governance)", "Art. 26 (deployer obligations)"],
        "gdpr_refs": ["GDPR Art. 5(2) (accountability)"],
        "nist_refs": ["GOVERN 1.1", "MAP 2.3"],
        "mitigation": "An inventory of sanctioned AI tools, egress controls and an "
                      "acceptable-use policy backed by monitoring.",
    },
    "DSGAI04": {
        "name": "Data, Model & Artifact Poisoning",
        "summary": "Manipulated training data, fine-tuning sets, embeddings or "
                   "stored memory implant backdoors, bias or integrity loss.",
        "owasp_refs": ["LLM04:2025"],
        "ai_act_refs": ["Art. 15(5) (data/model poisoning)", "Art. 10 (data governance)"],
        "gdpr_refs": [],
        "nist_refs": ["MEASURE 2.7", "MAP 2.3"],
        "mitigation": "Vet sources, integrity-check and anomaly-scan ingested "
                      "data, and track provenance of every artifact.",
    },
    "DSGAI05": {
        "name": "Data Integrity & Validation Failures",
        "summary": "Unvalidated or corrupted data flows through prompts, "
                   "pipelines and outputs, propagating errors and tampering.",
        "owasp_refs": ["LLM04:2025", "LLM05:2025"],
        "ai_act_refs": ["Art. 10 (data governance)", "Art. 15 (robustness)"],
        "gdpr_refs": ["GDPR Art. 5(1)(d) (accuracy)"],
        "nist_refs": ["MEASURE 2.7"],
        "mitigation": "Schema and integrity validation at every boundary, with "
                      "checksums/signatures on data at rest and in transit.",
    },
    "DSGAI06": {
        "name": "Tool, Plugin & Agent Data Exchange Risks",
        "summary": "Data passed to or from third-party tools, plugins and agents "
                   "is exfiltrated or tampered with in transit.",
        "owasp_refs": ["LLM03:2025", "LLM06:2025"],
        "ai_act_refs": ["Art. 25 (value chain responsibilities)", "Art. 15"],
        "gdpr_refs": ["GDPR Art. 28 (processors)", "GDPR Art. 32"],
        "nist_refs": ["GOVERN 1.1", "MEASURE 2.7"],
        "mitigation": "Vet and contract tool/plugin providers, minimise data "
                      "shared, and enforce least-privilege, audited exchanges.",
    },
    "DSGAI07": {
        "name": "Data Governance, Lifecycle & Classification",
        "summary": "Data is not classified, retained or disposed of under a "
                   "lifecycle, so sensitive data lingers in prompts, logs and stores.",
        "owasp_refs": ["LLM02:2025"],
        "ai_act_refs": ["Art. 10 (data governance)", "Art. 12 (record-keeping)"],
        "gdpr_refs": ["GDPR Art. 5(1)(e) (storage limitation)", "GDPR Art. 30"],
        "nist_refs": ["GOVERN 1.1", "MAP 2.3"],
        "mitigation": "Classify data, set retention/disposal per class, and apply "
                      "the policy to prompts, embeddings, logs and outputs alike.",
    },
    "DSGAI08": {
        "name": "Non-Compliance & Regulatory Violations",
        "summary": "GenAI data processing breaches privacy, sectoral or AI-specific "
                   "regulation (e.g. unlawful processing, missing DPIA/FRIA).",
        "owasp_refs": [],
        "ai_act_refs": ["Art. 10 (data governance)", "Art. 9 (risk management)"],
        "gdpr_refs": ["GDPR Art. 6 (lawfulness)", "GDPR Art. 35 (DPIA)"],
        "nist_refs": ["GOVERN 1.1"],
        "mitigation": "Map data flows to a lawful basis, run the required DPIA/"
                      "FRIA, and record processing — see the DPIA and FRIA reports.",
    },
    "DSGAI09": {
        "name": "Multimodal Capture & Cross-Channel Data Leakage",
        "summary": "Image, audio, video and document inputs capture more than "
                   "intended (faces, screens, metadata), leaking across channels.",
        "owasp_refs": ["LLM02:2025"],
        "ai_act_refs": ["Art. 10 (data governance)"],
        "gdpr_refs": ["GDPR Art. 9 (special categories)", "GDPR Art. 5(1)(c) (minimisation)"],
        "nist_refs": ["MEASURE 2.10"],
        "mitigation": "Minimise and pre-process multimodal input (crop, redact, "
                      "strip metadata) and separate channels by sensitivity.",
    },
    "DSGAI10": {
        "name": "Synthetic Data, Anonymization & Transformation Pitfalls",
        "summary": "Synthetic or 'anonymised' data still leaks the original "
                   "through re-identification, memorisation or weak transforms.",
        "owasp_refs": ["LLM02:2025", "LLM04:2025"],
        "ai_act_refs": ["Art. 10 (data governance)"],
        "gdpr_refs": ["GDPR Art. 25 (data protection by design)", "GDPR Recital 26"],
        "nist_refs": ["MEASURE 2.10"],
        "mitigation": "Validate anonymisation against re-identification, and treat "
                      "synthetic data derived from real data as still in scope.",
    },
    "DSGAI11": {
        "name": "Cross-Context & Multi-User Conversation Bleed",
        "summary": "Context, memory or cache from one user or session bleeds into "
                   "another, exposing data across an authorization boundary.",
        "owasp_refs": ["LLM02:2025", "LLM08:2025"],
        "ai_act_refs": ["Art. 10 (data governance)", "Art. 15 (cybersecurity)"],
        "gdpr_refs": ["GDPR Art. 5(1)(f) (confidentiality)", "GDPR Art. 32"],
        "nist_refs": ["MEASURE 2.7"],
        "mitigation": "Isolate per-user/per-tenant context, memory and cache, and "
                      "enforce the boundary server-side, not in the prompt.",
    },
    "DSGAI12": {
        "name": "Unsafe Natural-Language Data Gateways",
        "summary": "Natural-language-to-data gateways (LLM-to-SQL/API) let crafted "
                   "input read or change data beyond the user's authorization.",
        "owasp_refs": ["LLM05:2025", "LLM01:2025"],
        "ai_act_refs": ["Art. 15 (cybersecurity)"],
        "gdpr_refs": ["GDPR Art. 32"],
        "nist_refs": ["MEASURE 2.7"],
        "mitigation": "Parameterise and allow-list generated queries, run them "
                      "under the user's authorization, and validate every result.",
    },
    "DSGAI13": {
        "name": "Vector Store Platform Data Security",
        "summary": "Misconfigured vector APIs, weak tenant scoping or traversal "
                   "flaws expose embeddings and the data they encode.",
        "owasp_refs": ["LLM08:2025"],
        "ai_act_refs": ["Art. 10 (data governance)", "Art. 15 (cybersecurity)"],
        "gdpr_refs": ["GDPR Art. 32"],
        "nist_refs": ["MEASURE 2.7"],
        "mitigation": "Authenticate and tenant-isolate the vector store, scope "
                      "retrieval per identity, and audit access.",
    },
    "DSGAI14": {
        "name": "Excessive Telemetry & Monitoring Leakage",
        "summary": "Logs, traces and analytics capture prompts and outputs "
                   "verbatim, turning observability into a sensitive-data store.",
        "owasp_refs": ["LLM02:2025"],
        "ai_act_refs": ["Art. 12 (record-keeping)", "Art. 10 (data governance)"],
        "gdpr_refs": ["GDPR Art. 5(1)(c) (minimisation)", "GDPR Art. 25"],
        "nist_refs": ["MEASURE 2.10"],
        "mitigation": "Redact sensitive content from telemetry, scope log access, "
                      "and set bounded retention on logs and traces.",
    },
    "DSGAI15": {
        "name": "Over-Broad Context Windows & Prompt Over-Sharing",
        "summary": "More data than the task needs is stuffed into the context "
                   "window, widening exposure if the prompt or output leaks.",
        "owasp_refs": ["LLM02:2025", "LLM01:2025"],
        "ai_act_refs": ["Art. 10 (data governance)"],
        "gdpr_refs": ["GDPR Art. 5(1)(c) (data minimisation)"],
        "nist_refs": ["MEASURE 2.10"],
        "mitigation": "Inject only the minimum context the task needs, filtered "
                      "and scoped to the requesting user.",
    },
    "DSGAI16": {
        "name": "Endpoint & Browser Assistant Overreach",
        "summary": "Endpoint, browser or OS assistants read screens, files and "
                   "sessions beyond their remit, exfiltrating local data.",
        "owasp_refs": ["LLM06:2025"],
        "ai_act_refs": ["Art. 14 (human oversight)", "Art. 15 (cybersecurity)"],
        "gdpr_refs": ["GDPR Art. 5(1)(c) (minimisation)"],
        "nist_refs": ["MANAGE 2.3"],
        "mitigation": "Scope assistant permissions to the minimum, require consent "
                      "for sensitive captures, and keep a human approval gate.",
    },
    "DSGAI17": {
        "name": "Data Availability & Resilience Failures",
        "summary": "Loss, corruption or unavailability of training data, vector "
                   "stores or memory degrades or halts the system.",
        "owasp_refs": ["LLM10:2025"],
        "ai_act_refs": ["Art. 15 (robustness & availability)"],
        "gdpr_refs": ["GDPR Art. 32(1)(c) (availability & resilience)"],
        "nist_refs": ["MANAGE 4.1"],
        "mitigation": "Back up and integrity-check data stores, test restore, and "
                      "plan for graceful degradation.",
    },
    "DSGAI18": {
        "name": "Inference & Data Reconstruction",
        "summary": "Membership-inference, model-inversion and reconstruction "
                   "attacks recover training data or attributes from the model.",
        "owasp_refs": ["LLM02:2025"],
        "ai_act_refs": ["Art. 15 (cybersecurity)", "Art. 10 (data governance)"],
        "gdpr_refs": ["GDPR Art. 5(1)(f) (confidentiality)", "GDPR Art. 25"],
        "nist_refs": ["MEASURE 2.7", "MEASURE 2.10"],
        "mitigation": "Limit memorisation, consider privacy-preserving training "
                      "(e.g. DP), and rate-limit/monitor inference probing.",
    },
    "DSGAI19": {
        "name": "Human-in-the-Loop & Labeler Overexposure",
        "summary": "Annotators, reviewers and HITL operators see more raw "
                   "sensitive data than their task requires.",
        "owasp_refs": ["LLM02:2025"],
        "ai_act_refs": ["Art. 10 (data governance)", "Art. 14 (human oversight)"],
        "gdpr_refs": ["GDPR Art. 5(1)(c) (minimisation)", "GDPR Art. 32(4)"],
        "nist_refs": ["GOVERN 1.1"],
        "mitigation": "Minimise, mask and access-scope data shown to labelers and "
                      "reviewers, with confidentiality controls and logging.",
    },
    "DSGAI20": {
        "name": "Model Exfiltration & IP Replication",
        "summary": "Weights, prompts or behaviour are stolen or cloned via "
                   "extraction queries or insider access, replicating the IP.",
        "owasp_refs": ["LLM10:2025"],
        "ai_act_refs": ["Art. 15 (cybersecurity)"],
        "gdpr_refs": [],
        "nist_refs": ["MEASURE 2.7"],
        "mitigation": "Protect weights at rest with strict access control, and "
                      "rate-limit/monitor for systematic extraction patterns.",
    },
    "DSGAI21": {
        "name": "Disinformation & Integrity Attacks via Data Poisoning",
        "summary": "Poisoned retrieval pipelines or sources steer the model to "
                   "produce attacker-chosen, false or biased output.",
        "owasp_refs": ["LLM04:2025", "LLM09:2025"],
        "ai_act_refs": ["Art. 15(5) (poisoning)", "Art. 13 (transparency)", "Art. 50"],
        "gdpr_refs": ["GDPR Art. 5(1)(d) (accuracy)"],
        "nist_refs": ["MEASURE 2.8", "MEASURE 2.5"],
        "mitigation": "Vet and sign retrieval sources, detect anomalous ingestion, "
                      "and ground outputs with verifiable citations.",
    },
}

# Canonical DSGAI ordering (the document's own numbering).
ORDER = [f"DSGAI{i:02d}" for i in range(1, 22)]

PROVENANCE = (
    "Risk identifiers and titles are from the OWASP GenAI Security Project's "
    "\"GenAI Data Security Risks & Mitigations\" (2026, v1.0); summaries and "
    "mitigations are concise Companion-authored paraphrases, and the DSGAI <-> "
    "OWASP LLM Top 10 <-> EU AI Act <-> NIST AI RMF mappings are a "
    "Companion-derived analytical alignment, not an official published crosswalk. "
    "The source organises mitigations into Foundational / Hardening / Advanced "
    "tiers; consult it for the full control set."
)

DISCLAIMER = (
    "This lens maps the system to the OWASP GenAI Data Security risks as a "
    "data-governance self-assessment aid. It does not replace a data protection "
    "impact assessment, a security review or legal advice."
)
