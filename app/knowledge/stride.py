"""STRIDE threat-model knowledge for AI-backend architectures.

The six STRIDE categories (Microsoft's threat-modelling frame), each tied to the
security-architecture intake fields (section 9) that determine whether the
threat is real for a given system, plus the OWASP LLM Top 10 family and the EU AI
Act article it maps to.

Provenance / honesty:
  * STRIDE is Microsoft's threat-modelling framework; the category names are its.
  * The mapping of each category to the `arch_*` intake fields, to the OWASP LLM
    Top 10 family and to EU AI Act articles is a Companion-derived analytical
    alignment — not an official crosswalk. Severity is computed by the AI security
    lens (`security.py`) from the same structured fields, so the STRIDE view and
    the OWASP severity view agree by construction.
"""

# Each category:
#   code/name      - the STRIDE letter and label
#   summary        - what the category asks about this architecture
#   questions      - the guiding questions (rendered as the per-category prompts)
#   arch           - the arch_* field ids that determine the risk (read-only inputs)
#   owasp          - the OWASP LLM Top 10 id whose architecture-aware severity is
#                    reused for this category, or None when no single OWASP item is
#                    a faithful proxy (Spoofing is auth-only; Repudiation is
#                    logging-only) — those two are scored directly from the field.
#   ai_act_refs    - the natural EU AI Act anchor(s)
STRIDE = [
    {
        "code": "S", "name": "Spoofing",
        "summary": ("Can an actor impersonate a user, or drive the system, "
                    "without proving identity?"),
        "questions": [
            "How do users authenticate (none / weak / strong SSO)?",
            "Is the system internal-only or exposed to untrusted users?",
            "Is user identity verified on every request?",
        ],
        "arch": ["arch_auth_strength"],
        "owasp": None,
        "ai_act_refs": ["Art. 15"],
    },
    {
        "code": "T", "name": "Tampering",
        "summary": ("Can data, backend state or model inputs be modified through "
                    "the system?"),
        "questions": [
            "Is backend access read-only, or read-write?",
            "Can it trigger downstream actions (email, tickets, code/SQL) "
            "without human review?",
            "Is retrieval (RAG) over a corpus users can modify?",
        ],
        "arch": ["arch_api_write", "arch_downstream_actions", "arch_rag_modifiable"],
        "owasp": "LLM05",
        "ai_act_refs": ["Art. 15"],
    },
    {
        "code": "R", "name": "Repudiation",
        "summary": ("Can actions be denied afterwards for lack of attributable, "
                    "retained logs?"),
        "questions": [
            "Are interactions logged with user identity?",
            "Is retention bounded?",
        ],
        "arch": ["arch_logging"],
        "owasp": None,
        "ai_act_refs": ["Art. 12"],
    },
    {
        "code": "I", "name": "Information disclosure",
        "summary": ("Can a user reach data they should not — other users' data, "
                    "secrets, or the system prompt?"),
        "questions": [
            "Own-user data only, or all-users / organisation-wide?",
            "Is access control enforced at the API/backend layer, or only in "
            "the prompt?",
            "Could the system prompt or retrieved context leak?",
        ],
        "arch": ["arch_data_scope", "arch_access_control_layer", "arch_rag_modifiable"],
        "owasp": "LLM02",
        "ai_act_refs": ["Art. 10", "Art. 15"],
    },
    {
        "code": "D", "name": "Denial of service",
        "summary": ("Can the system be exhausted, or made unaffordable, through "
                    "volume or cost?"),
        "questions": [
            "Are there rate limits / quotas / cost caps?",
            "How business-critical is availability?",
        ],
        "arch": ["arch_rate_limits"],
        "owasp": "LLM10",
        "ai_act_refs": ["Art. 15"],
    },
    {
        "code": "E", "name": "Elevation of privilege",
        "summary": ("Can a user inherit more reach than intended via the system's "
                    "backend identity?"),
        "questions": [
            "Per-user delegated identity, or a shared service account?",
            "Is backend RBAC enforced independently of the model?",
        ],
        "arch": ["arch_identity_model", "arch_access_control_layer"],
        "owasp": "LLM06",
        "ai_act_refs": ["Art. 15"],
    },
]

# Friendly labels for the arch_* values, for the "Answer (from intake)" column.
FIELD_LABELS = {
    "arch_auth_strength": {
        "none": "None (anonymous / unauthenticated)",
        "weak": "Weak (shared / static credentials)",
        "strong-sso": "Strong (SSO / MFA)",
    },
    "arch_access_control_layer": {
        "api-backend": "API / backend layer",
        "llm-prompt": "In the LLM / prompt (the model is the boundary)",
        "none": "No real access control",
    },
    "arch_data_scope": {
        "own-user": "Only the requesting user's data",
        "all-users": "All users' / organisation-wide data",
    },
    "arch_identity_model": {
        "per-user-delegated": "Per-user delegated identity",
        "shared-service-account": "Shared service account",
    },
}

# Human-readable question for each arch_* field (for the per-category table rows).
FIELD_QUESTIONS = {
    "arch_auth_strength": "User authentication",
    "arch_api_write": "Write/modify access to backend data",
    "arch_downstream_actions": "Unreviewed downstream actions",
    "arch_access_control_layer": "Where access control is enforced",
    "arch_data_scope": "Data the system can reach",
    "arch_rag_modifiable": "RAG over a user-modifiable corpus",
    "arch_identity_model": "Backend identity model",
    "arch_logging": "Identity-attributed logging with bounded retention",
    "arch_rate_limits": "Rate limits / quotas / cost caps",
}

PROVENANCE = (
    "STRIDE is Microsoft's threat-modelling framework. The mapping of each "
    "category to the security-architecture intake fields, to the OWASP LLM Top 10 "
    "family and to the EU AI Act articles is a Companion-derived analytical "
    "alignment, not an official crosswalk. Severity is computed deterministically "
    "from the structured arch_* fields by the AI security lens."
)

DISCLAIMER = (
    "This STRIDE view is a structured threat-modelling aid driven by the stated "
    "architecture. It does not replace a full threat-modelling exercise, a "
    "security review or legal advice."
)
