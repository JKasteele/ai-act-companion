"""Intake questionnaire - the single source of truth.

This structure is:
  1. sent as JSON to the frontend to render the form dynamically;
  2. read by the classifier based on the question ids.

Question types: text | textarea | radio | select | boolean | multiselect
"""

QUESTIONNAIRE = {
    "title": "AI system intake",
    "intro": (
        "Describe the AI system. The answers feed a rule-based EU AI Act "
        "classification and the generated documentation. Use synthetic/generic "
        "example data only."
    ),
    "sections": [
        {
            "id": "identification",
            "title": "1. System identification",
            "description": "What is the system and who is responsible?",
            "questions": [
                {"id": "sys_name", "type": "text", "required": True,
                 "label": "Name of the AI system",
                 "placeholder": "e.g. TalentMatch CV screening"},
                {"id": "sys_version", "type": "text", "required": False,
                 "label": "Version", "placeholder": "e.g. 1.0"},
                {"id": "sys_owner", "type": "text", "required": False,
                 "label": "Owner / organisation (synthetic)",
                 "placeholder": "e.g. Example Ltd."},
                {"id": "sys_description", "type": "textarea", "required": True,
                 "label": "Short description",
                 "help": "What does the system do, technically and functionally?"},
                {"id": "intended_purpose", "type": "textarea", "required": True,
                 "label": "Intended purpose",
                 "help": "What is the system intended for, in which context?"},
                {"id": "provider_role", "type": "radio", "required": True,
                 "label": "Your role (Art. 3)",
                 "options": [
                     {"value": "provider", "label": "Provider"},
                     {"value": "deployer", "label": "Deployer"},
                     {"value": "both", "label": "Both"},
                     {"value": "other", "label": "Other / not yet known"},
                 ]},
                {"id": "eu_market", "type": "boolean", "required": True,
                 "label": "Placed on the market or used in the EU, or affecting persons in the EU?",
                 "help": "If not, the AI Act may not apply (Art. 2)."},
                {"id": "lifecycle_stage", "type": "select", "required": False,
                 "label": "Lifecycle stage",
                 "options": [
                     {"value": "concept", "label": "Concept / idea"},
                     {"value": "development", "label": "Development"},
                     {"value": "testing", "label": "Test / pilot"},
                     {"value": "production", "label": "Production"},
                     {"value": "retired", "label": "Retired"},
                 ]},
            ],
        },
        {
            "id": "prohibited",
            "title": "2. Prohibited practices screening (Art. 5)",
            "description": (
                "Answer honestly; a single 'yes' can classify the system as "
                "prohibited. When in doubt: choose 'yes' and document the nuance."
            ),
            "questions": [
                {"id": "p_manipulation", "type": "boolean", "required": True,
                 "label": "Does the system use subliminal, manipulative or "
                          "deceptive techniques that materially distort behaviour?"},
                {"id": "p_vulnerability", "type": "boolean", "required": True,
                 "label": "Does it exploit vulnerabilities (age, disability, "
                          "socio-economic situation)?"},
                {"id": "p_social_scoring", "type": "boolean", "required": True,
                 "label": "Does it perform social scoring with detrimental/"
                          "unfavourable treatment in an unrelated context?"},
                {"id": "p_predictive_policing", "type": "boolean", "required": True,
                 "label": "Does it predict criminal behaviour based solely on "
                          "profiling or personality traits?"},
                {"id": "p_facial_scraping", "type": "boolean", "required": True,
                 "label": "Does it untargetedly scrape facial images "
                          "(internet/CCTV) for facial recognition databases?"},
                {"id": "p_emotion_work_edu", "type": "boolean", "required": True,
                 "label": "Does it recognise emotions in the workplace or in "
                          "education (not for medical/safety reasons)?"},
                {"id": "p_biometric_categorization_sensitive", "type": "boolean", "required": True,
                 "label": "Does it infer sensitive attributes via biometrics "
                          "(race, religion, political opinion, sexual orientation, ...)?"},
                {"id": "p_realtime_rbi_le", "type": "boolean", "required": True,
                 "label": "Is it real-time remote biometric identification in "
                          "public spaces for law enforcement?"},
            ],
        },
        {
            "id": "high_risk",
            "title": "3. High-risk screening (Art. 6 + Annex III)",
            "description": "Determines whether the heavy obligations apply.",
            "questions": [
                {"id": "hr_safety_component", "type": "boolean", "required": True,
                 "label": "Is the system a product, or the safety component of a "
                          "product, covered by EU harmonisation legislation "
                          "(Annex I) that requires third-party conformity assessment?"},
                {"id": "hr_usecases", "type": "multiselect", "required": False,
                 "label": "In which Annex III areas is it used? (multiple allowed)",
                 "options": [
                     {"value": "biometrics", "label": "Biometrics (Annex III-1)"},
                     {"value": "critical_infra", "label": "Critical infrastructure (III-2)"},
                     {"value": "education", "label": "Education / vocational training (III-3)"},
                     {"value": "employment", "label": "Employment & workforce management (III-4)"},
                     {"value": "essential_services", "label": "Essential services, credit, insurance (III-5)"},
                     {"value": "law_enforcement", "label": "Law enforcement (III-6)"},
                     {"value": "migration_border", "label": "Migration, asylum, border control (III-7)"},
                     {"value": "justice_democracy", "label": "Administration of justice & democracy (III-8)"},
                     {"value": "none", "label": "None of the above"},
                 ]},
                {"id": "hr_does_profiling", "type": "boolean", "required": False,
                 "label": "Does the system perform profiling of natural persons?",
                 "help": "Relevant for the Art. 6(3) derogation."},
                {"id": "hr_art6_3_minor", "type": "boolean", "required": False,
                 "label": "Within Annex III, does it only perform a narrow, "
                          "preparatory or procedural task without materially "
                          "influencing the outcome of decision-making?",
                 "help": "Possible Art. 6(3) derogation; only relevant for an Annex III area."},
            ],
        },
        {
            "id": "transparency",
            "title": "4. Transparency (Art. 50)",
            "description": "Determines any information/marking obligations.",
            "questions": [
                {"id": "t_interacts_humans", "type": "boolean", "required": True,
                 "label": "Does the system interact directly with natural persons "
                          "(e.g. chatbot, voice assistant)?"},
                {"id": "t_synthetic_content", "type": "boolean", "required": True,
                 "label": "Does it generate or manipulate audio, image, video or text?"},
                {"id": "t_deepfake", "type": "boolean", "required": True,
                 "label": "Does it generate deepfakes (realistic fake images/audio of persons)?"},
                {"id": "t_emotion_or_biometric_cat", "type": "boolean", "required": True,
                 "label": "Does it perform emotion recognition or biometric "
                          "categorisation (permitted, not prohibited)?"},
            ],
        },
        {
            "id": "gpai",
            "title": "5. General-purpose AI (GPAI)",
            "description": "Chapter V - in addition to the risk tier.",
            "questions": [
                {"id": "gpai_model", "type": "boolean", "required": False,
                 "label": "Is this (or does this contain) a general-purpose AI "
                          "model (a broadly applicable foundation/language model)?"},
                {"id": "gpai_systemic", "type": "boolean", "required": False,
                 "label": "Does the model have systemic risk (>= 10^25 FLOP "
                          "training compute or designated as such)?"},
            ],
        },
        {
            "id": "data",
            "title": "6. Data & fundamental rights",
            "description": "Feeds the DPIA skeleton and the bias checklist.",
            "questions": [
                {"id": "data_personal", "type": "boolean", "required": True,
                 "label": "Does the system process personal data?"},
                {"id": "data_special_category", "type": "boolean", "required": False,
                 "label": "Special categories of personal data (GDPR Art. 9: "
                          "health, ethnicity, religion, ...)?"},
                {"id": "data_biometric", "type": "boolean", "required": False,
                 "label": "Biometric data?"},
                {"id": "automated_decision", "type": "boolean", "required": False,
                 "label": "Automated decision-making with legal or similarly "
                          "significant effects (GDPR Art. 22)?"},
                {"id": "affects_vulnerable", "type": "boolean", "required": False,
                 "label": "Does it affect vulnerable groups (e.g. children, patients)?"},
                {"id": "data_scale", "type": "select", "required": False,
                 "label": "Scale of data processing",
                 "options": [
                     {"value": "small", "label": "Small"},
                     {"value": "medium", "label": "Medium"},
                     {"value": "large", "label": "Large-scale"},
                 ]},
                {"id": "data_sources", "type": "textarea", "required": False,
                 "label": "Origin of training/input data (brief)",
                 "help": "e.g. internal CRM, public datasets, user input."},
            ],
        },
        {
            "id": "autonomy",
            "title": "7. Autonomy & human oversight",
            "description": "Feeds the risk assessment and the Art. 14 mapping.",
            "questions": [
                {"id": "autonomy_level", "type": "radio", "required": True,
                 "label": "Level of autonomy",
                 "options": [
                     {"value": "advisory", "label": "Advisory (human decides fully)"},
                     {"value": "human_in_the_loop", "label": "Human-in-the-loop (human approves every action)"},
                     {"value": "human_on_the_loop", "label": "Human-on-the-loop (human monitors and can intervene)"},
                     {"value": "fully_autonomous", "label": "Fully autonomous (no human intervention)"},
                 ]},
                {"id": "can_override", "type": "boolean", "required": False,
                 "label": "Can a human override decisions or stop the system?"},
                {"id": "human_oversight", "type": "textarea", "required": False,
                 "label": "Describe the human oversight measures",
                 "help": "Who oversees, with which means, and at what thresholds?"},
            ],
        },
        {
            "id": "security",
            "title": "8. AI security context",
            "description": (
                "Feeds the AI security lens: maps the system to the OWASP Top 10 "
                "for LLM Applications and MITRE ATLAS, linked to EU AI Act Art. 15."
            ),
            "questions": [
                {"id": "sec_is_llm", "type": "boolean", "required": False,
                 "label": "Is it an LLM / generative-AI system (generates text, "
                          "code, images, audio, …)?"},
                {"id": "sec_third_party_models", "type": "boolean", "required": False,
                 "label": "Does it rely on third-party or foundation models, or "
                          "external ML components/datasets?",
                 "help": "Supply-chain exposure."},
                {"id": "sec_external_data", "type": "boolean", "required": False,
                 "label": "Does it ingest untrusted external or user-supplied "
                          "content (at training or inference)?",
                 "help": "Prompt-injection and data-poisoning exposure."},
                {"id": "sec_agentic", "type": "boolean", "required": False,
                 "label": "Can it autonomously take actions, call tools/APIs or "
                          "trigger downstream effects (agentic)?"},
                {"id": "sec_public", "type": "boolean", "required": False,
                 "label": "Is it accessible to untrusted/external users (e.g. the "
                          "public internet)?"},
                {"id": "sec_outputs_to_systems", "type": "boolean", "required": False,
                 "label": "Is its output passed to other systems (code execution, "
                          "SQL, downstream automation) without human review?"},
            ],
        },
        {
            "id": "architecture",
            "title": "9. Security architecture",
            "description": (
                "Drives the architecture-aware severity of the AI security lens "
                "(and the STRIDE view). The severity of an AI risk depends on the "
                "architecture around the model, not just on whether a control box "
                "is ticked."
            ),
            "questions": [
                {"id": "arch_auth_strength", "type": "select", "required": False,
                 "label": "How do users authenticate?",
                 "options": [
                     {"value": "none", "label": "None (anonymous / unauthenticated)"},
                     {"value": "weak", "label": "Weak (e.g. shared/static credentials)"},
                     {"value": "strong-sso", "label": "Strong (SSO / MFA)"},
                 ]},
                {"id": "arch_api_write", "type": "boolean", "required": False,
                 "label": "Does the system have write/modify access to backend "
                          "systems or data (not read-only)?"},
                {"id": "arch_downstream_actions", "type": "boolean", "required": False,
                 "label": "Can it trigger downstream actions (email, tickets, "
                          "code/SQL execution) without human review?"},
                {"id": "arch_access_control_layer", "type": "select", "required": False,
                 "label": "Where is data access control enforced?",
                 "options": [
                     {"value": "api-backend", "label": "API / backend layer"},
                     {"value": "llm-prompt", "label": "In the LLM / prompt (the model is the boundary)"},
                     {"value": "none", "label": "No real access control"},
                 ]},
                {"id": "arch_data_scope", "type": "select", "required": False,
                 "label": "Which data can it reach?",
                 "options": [
                     {"value": "own-user", "label": "Only the requesting user's data"},
                     {"value": "all-users", "label": "All users' / organisation-wide data"},
                 ]},
                {"id": "arch_rag_modifiable", "type": "boolean", "required": False,
                 "label": "Does it use RAG over a knowledge base that users or "
                          "integrations can modify?"},
                {"id": "arch_identity_model", "type": "select", "required": False,
                 "label": "How does it call backends?",
                 "options": [
                     {"value": "per-user-delegated", "label": "Per-user delegated identity"},
                     {"value": "shared-service-account", "label": "Shared service account"},
                 ]},
                {"id": "arch_logging", "type": "boolean", "required": False,
                 "label": "Are interactions logged with user identity, with "
                          "bounded retention?"},
                {"id": "arch_rate_limits", "type": "boolean", "required": False,
                 "label": "Are there rate limits / quotas / cost caps?"},
            ],
        },
    ],
}


def all_question_ids():
    """All question ids (handy for validation/tests)."""
    ids = []
    for section in QUESTIONNAIRE["sections"]:
        for q in section["questions"]:
            ids.append(q["id"])
    return ids
