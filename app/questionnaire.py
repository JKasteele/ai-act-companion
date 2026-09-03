"""Intake questionnaire - the single source of truth.

This structure is:
  1. sent as JSON to the frontend to render the form dynamically;
  2. read by the classifier based on the question ids.

Question types: text | textarea | radio | select | boolean | multiselect | table

A `table` question carries `columns` (each: id, label, type text|select,
optional options) and is answered with a list of row objects keyed by
column id. The three front-ends render it; the engine reads it through
`knowledge.data_governance.dataset_rows()`.
"""

from .knowledge.forensics import LOG_SCOPE_OPTIONS as _LOG_SCOPE_OPTIONS

# Shared option list for the seven data-quality dimensions (section 11).
_QUALITY_STATUS_OPTIONS = [
    {"value": "unknown", "label": "Unknown — not assessed"},
    {"value": "assessed", "label": "Assessed qualitatively (reviewed, no metric)"},
    {"value": "measured", "label": "Measured (metric, threshold and evidence exist)"},
    {"value": "na", "label": "Not applicable"},
]

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
                {"id": "org_sector", "type": "select", "required": False,
                 "label": "Sector of the organisation",
                 "help": "Drives the sector crosswalks (EIOPA / DNB SAFEST for insurers "
                         "and banks) and the DORA third-party hook for financial entities.",
                 "options": [
                     {"value": "general", "label": "General / not sector-specific"},
                     {"value": "insurance", "label": "Insurance (incl. health insurer)"},
                     {"value": "banking_credit", "label": "Banking / credit / payments"},
                     {"value": "other_financial", "label": "Other financial entity (DORA scope)"},
                     {"value": "healthcare", "label": "Healthcare provider"},
                     {"value": "public_sector", "label": "Public sector"},
                     {"value": "other", "label": "Other"},
                 ]},
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
                {"id": "exempt_military", "type": "boolean", "required": False,
                 "label": "Is the system used exclusively for military, defence or "
                          "national-security purposes?",
                 "help": "Carve-out under Art. 2(3); if yes, the AI Act does not apply."},
                {"id": "exempt_research", "type": "boolean", "required": False,
                 "label": "Is it developed and used solely for scientific research "
                          "and development?",
                 "help": "Carve-out under Art. 2(6)."},
                {"id": "exempt_premarket", "type": "boolean", "required": False,
                 "label": "Is all activity limited to research, testing or "
                          "development prior to being placed on the market "
                          "(not real-world testing)?",
                 "help": "Carve-out under Art. 2(8); does not cover testing in real-world conditions."},
                {"id": "exempt_personal", "type": "boolean", "required": False,
                 "label": "Is it used only by a natural person in a purely "
                          "personal, non-professional capacity?",
                 "help": "Carve-out under Art. 2(10)."},
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
                {"id": "hr_essential_subarea", "type": "select", "required": False,
                 "label": "If Annex III-5: which sub-point?",
                 "help": "Point 5 has four distinct cases. For 5(b) and 5(c) the FRIA "
                         "(Art. 27) is mandatory for every deployer, private ones included.",
                 "options": [
                     {"value": "public_benefits",
                      "label": "5(a) Eligibility for public benefits / services"},
                     {"value": "creditworthiness",
                      "label": "5(b) Creditworthiness / credit scoring"},
                     {"value": "insurance_life_health",
                      "label": "5(c) Risk assessment & pricing in life / health insurance"},
                     {"value": "emergency_triage",
                      "label": "5(d) Emergency calls / emergency healthcare triage"},
                 ]},
                {"id": "hr_insurance_scope", "type": "select", "required": False,
                 "label": "If 5(c): which insurance product?",
                 "help": "Sector rules decide where the risk sits (e.g. the Dutch basic "
                         "package has an acceptance duty and no premium differentiation).",
                 "options": [
                     {"value": "health_basic_nl", "label": "Health — Dutch basic insurance (Zvw)"},
                     {"value": "health_supplementary", "label": "Health — supplementary insurance"},
                     {"value": "life", "label": "Life insurance"},
                     {"value": "other", "label": "Other product / other jurisdiction"},
                 ]},
                {"id": "hr_does_profiling", "type": "boolean", "required": False,
                 "label": "Does the system perform profiling of natural persons?",
                 "help": "Relevant for the Art. 6(3) derogation: once a system profiles, "
                         "the derogation is off the table (also per the Commission's draft "
                         "Art. 6(5) guidelines of May 2026; e.g. claims-fraud scoring of "
                         "persons)."},
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
                {"id": "gpai_open_source", "type": "boolean", "required": False,
                 "label": "Is the model released under a free and open-source "
                          "licence, with weights and usage information made "
                          "publicly available?",
                 "help": "Art. 53(2) exempts open-source GPAI models from part of "
                         "the documentation duties — unless they have systemic risk."},
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
        {
            "id": "incident",
            "title": "10. Serious-incident assessment (Art. 73)",
            "description": (
                "Complete these ONLY when documenting an actual incident that has "
                "occurred. They drive the serious-incident report (Art. 3(49) "
                "definition + Art. 73 reporting deadline) and do not affect the "
                "risk classification."
            ),
            "questions": [
                {"id": "inc_death", "type": "boolean", "required": False,
                 "label": "Did the incident lead to the death of a person?"},
                {"id": "inc_health", "type": "boolean", "required": False,
                 "label": "Did it lead to serious harm to a person's health?"},
                {"id": "inc_critical_infra", "type": "boolean", "required": False,
                 "label": "Did it cause a serious and irreversible disruption of "
                          "the management or operation of critical infrastructure?"},
                {"id": "inc_fundamental_rights", "type": "boolean", "required": False,
                 "label": "Did it infringe obligations under Union law intended to "
                          "protect fundamental rights?"},
                {"id": "inc_property_env", "type": "boolean", "required": False,
                 "label": "Did it cause serious harm to property or the environment?"},
                {"id": "inc_widespread", "type": "boolean", "required": False,
                 "label": "Is the infringement widespread (affecting many persons "
                          "or several Member States)?",
                 "help": "Shortens the Art. 73 reporting deadline."},
            ],
        },
        {
            "id": "datagov",
            "title": "11. Data governance & quality (Art. 10)",
            "description": (
                "AI governance is built on data governance. Per dataset: where it "
                "comes from, who owns and stewards it, how it is classified and how "
                "good it is. Feeds the data-governance report, the DPIA and the "
                "Annex IV data description. None of these fields affect the risk tier."
            ),
            "questions": [
                {"id": "dg_data_owner", "type": "text", "required": False,
                 "label": "Data owner (business role accountable for the data domain)",
                 "help": "Distinct from the AI system owner; the two carry different "
                         "accountabilities.",
                 "placeholder": "e.g. Head of Claims (data domain: claims)"},
                {"id": "dg_data_steward", "type": "text", "required": False,
                 "label": "Data steward (day-to-day definitions, metadata, quality)",
                 "placeholder": "e.g. Claims data steward"},
                {"id": "dg_catalog_registered", "type": "boolean", "required": False,
                 "label": "Are the datasets registered in a data catalogue / metadata "
                          "store with lineage?"},
                {"id": "dg_datasets", "type": "table", "required": False,
                 "label": "Dataset inventory (training, validation, test and "
                          "inference-time input)",
                 "help": "One row per dataset. Use synthetic names.",
                 "columns": [
                     {"id": "name", "label": "Dataset", "type": "text"},
                     {"id": "origin", "label": "Origin", "type": "select", "options": [
                         {"value": "internal", "label": "Internal"},
                         {"value": "external_vendor", "label": "Vendor / licensed"},
                         {"value": "external_public", "label": "Public / open"},
                         {"value": "partner", "label": "Partner / shared"},
                         {"value": "user_generated", "label": "User-generated / runtime"},
                         {"value": "synthetic", "label": "Synthetic"},
                     ]},
                     {"id": "owner", "label": "Data owner", "type": "text"},
                     {"id": "steward", "label": "Steward", "type": "text"},
                     {"id": "classification", "label": "Classification", "type": "select",
                      "options": [
                          {"value": "public", "label": "Public"},
                          {"value": "internal", "label": "Internal"},
                          {"value": "confidential", "label": "Confidential"},
                          {"value": "personal", "label": "Personal data"},
                          {"value": "special_category", "label": "Special category (Art. 9)"},
                      ]},
                     {"id": "purpose", "label": "Purpose (limitation)", "type": "text"},
                     {"id": "retention", "label": "Retention", "type": "text"},
                     {"id": "legal_basis", "label": "Lawful basis", "type": "select",
                      "options": [
                          {"value": "na", "label": "n/a (no personal data)"},
                          {"value": "consent", "label": "Consent"},
                          {"value": "contract", "label": "Contract"},
                          {"value": "legal_obligation", "label": "Legal obligation"},
                          {"value": "vital_interest", "label": "Vital interests"},
                          {"value": "public_task", "label": "Public task"},
                          {"value": "legitimate_interest", "label": "Legitimate interest"},
                          {"value": "unknown", "label": "Unknown"},
                      ]},
                 ]},
                {"id": "dg_lineage", "type": "textarea", "required": False,
                 "label": "Lineage (source → preparation → training/input set → model → output)",
                 "help": "One line per hop is enough; name the systems, not the vendors.",
                 "placeholder": "e.g. Claims DWH → dedupe + label (steward) → train_v3 → "
                                "model v3 → risk score → underwriting queue"},
                {"id": "dg_q_accuracy", "type": "select", "required": False,
                 "label": "Data quality — accuracy",
                 "options": _QUALITY_STATUS_OPTIONS},
                {"id": "dg_q_completeness", "type": "select", "required": False,
                 "label": "Data quality — completeness",
                 "options": _QUALITY_STATUS_OPTIONS},
                {"id": "dg_q_consistency", "type": "select", "required": False,
                 "label": "Data quality — consistency",
                 "options": _QUALITY_STATUS_OPTIONS},
                {"id": "dg_q_timeliness", "type": "select", "required": False,
                 "label": "Data quality — timeliness",
                 "options": _QUALITY_STATUS_OPTIONS},
                {"id": "dg_q_validity", "type": "select", "required": False,
                 "label": "Data quality — validity",
                 "options": _QUALITY_STATUS_OPTIONS},
                {"id": "dg_q_uniqueness", "type": "select", "required": False,
                 "label": "Data quality — uniqueness",
                 "options": _QUALITY_STATUS_OPTIONS},
                {"id": "dg_q_representativeness", "type": "select", "required": False,
                 "label": "Data quality — representativeness & bias screening",
                 "help": "The AI Act-specific dimension (Art. 10(3), Art. 10(2)(f–g)).",
                 "options": _QUALITY_STATUS_OPTIONS},
                {"id": "dg_q_evidence", "type": "textarea", "required": False,
                 "label": "Quality evidence (metrics, thresholds, dates, where recorded)",
                 "placeholder": "e.g. completeness 98.7% on mandatory fields (DQ dashboard, "
                                "2026-08); representativeness: coverage per age band vs. "
                                "portfolio, report DQ-2026-14"},
            ],
        },
        {
            "id": "forensics",
            "title": "12. Forensic readiness & evidence",
            "description": (
                "Can you reconstruct and evidence what the system did, why, with which "
                "data and model version — after an incident, a complaint, a regulator "
                "request or a dispute? Feeds the forensic-readiness report and the "
                "parallel reporting clocks in the incident report. Model output is "
                "non-deterministic, so evidence comes from recording, not re-running. "
                "None of these fields affect the risk tier."
            ),
            "questions": [
                {"id": "fr_log_scope", "type": "multiselect", "required": False,
                 "label": "What is recorded? (multiple allowed)",
                 "options": [{"value": v, "label": lab} for v, lab in _LOG_SCOPE_OPTIONS]},
                {"id": "fr_retention_months", "type": "select", "required": False,
                 "label": "Retention of the logs",
                 "help": "Art. 19 / Art. 26(6): at least six months unless Union or national "
                         "law (in particular data-protection law) provides otherwise.",
                 "options": [
                     {"value": "lt6", "label": "Less than 6 months"},
                     {"value": "6", "label": "6 months (the AI Act floor)"},
                     {"value": "7_24", "label": "7–24 months"},
                     {"value": "gt24", "label": "More than 24 months"},
                 ]},
                {"id": "fr_retention_basis", "type": "select", "required": False,
                 "label": "Basis for that retention period",
                 "options": [
                     {"value": "ai_act_floor", "label": "AI Act floor (Art. 19 / 26(6))"},
                     {"value": "financial_services",
                      "label": "Financial-services documentation term (Art. 19(2) / 26(6))"},
                     {"value": "gdpr_limited", "label": "Shorter term required by data-protection law"},
                     {"value": "other", "label": "Other / not yet decided"},
                 ]},
                {"id": "fr_integrity", "type": "select", "required": False,
                 "label": "Integrity of the logs",
                 "options": [
                     {"value": "none", "label": "None"},
                     {"value": "access_only", "label": "Access control only"},
                     {"value": "hashing", "label": "Hashing of records"},
                     {"value": "hash_chain_worm", "label": "Hash chain + WORM / append-only storage"},
                     {"value": "signed", "label": "Signed records with an independent time anchor"},
                 ]},
                {"id": "fr_time_sync", "type": "boolean", "required": False,
                 "label": "Is there one synchronised time source across all evidence sources "
                          "(application, gateway, workflow, data access)?"},
                {"id": "fr_model_pinned", "type": "boolean", "required": False,
                 "label": "Is the exact model version / revision recorded per inference?"},
                {"id": "fr_prompt_versioned", "type": "boolean", "required": False,
                 "label": "Is the system instruction under version control, with the version "
                          "in each record?"},
                {"id": "fr_rag_snapshot", "type": "boolean", "required": False,
                 "label": "Is it recorded which documents were in the context (retrieval snapshot)?"},
                {"id": "fr_override_logged", "type": "boolean", "required": False,
                 "label": "Are human reviews and deviations from the model advice logged, with reason?"},
                {"id": "fr_log_pii", "type": "select", "required": False,
                 "label": "Personal data in the logs",
                 "help": "A hash of the input proves what the input was without keeping it.",
                 "options": [
                     {"value": "none", "label": "None"},
                     {"value": "case_id", "label": "Only a reference / case id"},
                     {"value": "hash", "label": "Hash of the input"},
                     {"value": "pseudonymised", "label": "Pseudonymised content"},
                     {"value": "full", "label": "Full content, incl. special categories"},
                 ]},
                {"id": "fr_vendor_log_access", "type": "select", "required": False,
                 "label": "Evidence held by the model / platform supplier",
                 "options": [
                     {"value": "own_logs_sufficient", "label": "Own logs suffice (no external model)"},
                     {"value": "contractual_access",
                      "label": "Contractual right of access (Art. 25(4) / DORA Art. 30(3))"},
                     {"value": "portal_only", "label": "Only via the supplier's portal"},
                     {"value": "none", "label": "No access"},
                 ]},
                {"id": "fr_legal_hold", "type": "boolean", "required": False,
                 "label": "Is there a documented legal-hold / evidence-freeze procedure (stop log "
                          "rotation, pin the model version)?",
                 "help": "Art. 73: the system must not be altered before the authorities are "
                         "informed."},
                {"id": "fr_evidence_owner", "type": "text", "required": False,
                 "label": "Owner of the evidence file (role)",
                 "placeholder": "e.g. AI governance lead, with SecOps as custodian"},
                {"id": "fr_drill", "type": "boolean", "required": False,
                 "label": "Has evidence retrieval been exercised in the last 12 months "
                          "(reconstruct one past decision end-to-end)?"},
            ],
        },
        {
            "id": "governance",
            "title": "13. Governance register & policy metadata",
            "description": (
                "Who owns this record, who approved it, when it is reviewed, which "
                "exceptions run, and who has been trained (Art. 4). Feeds the governance "
                "register report, the portfolio status columns and the AI-register CSV. "
                "Dates as YYYY-MM-DD. None of these fields affect the risk tier."
            ),
            "questions": [
                {"id": "gov_policy_owner", "type": "text", "required": False,
                 "label": "Policy owner (role accountable for this governance record)",
                 "placeholder": "e.g. AI governance lead"},
                {"id": "gov_approval_body", "type": "text", "required": False,
                 "label": "Approval body (committee / board that decided)",
                 "placeholder": "e.g. AI & Data Governance Board"},
                {"id": "gov_status", "type": "select", "required": False,
                 "label": "Governance status",
                 "options": [
                     {"value": "proposed", "label": "Proposed (not yet decided)"},
                     {"value": "approved", "label": "Approved"},
                     {"value": "in_review", "label": "In review"},
                     {"value": "exception", "label": "Running under an exception"},
                     {"value": "retired", "label": "Retired"},
                 ]},
                {"id": "gov_approved_on", "type": "text", "required": False,
                 "label": "Approval date (YYYY-MM-DD)", "placeholder": "2026-09-01"},
                {"id": "gov_next_review", "type": "text", "required": False,
                 "label": "Next review date (YYYY-MM-DD)",
                 "help": "Leave empty to derive it from the approval date and the tier "
                         "cadence (high 6 · limited 12 · minimal 24 months).",
                 "placeholder": "2027-03-01"},
                {"id": "gov_exceptions", "type": "table", "required": False,
                 "label": "Exceptions / deviations from policy",
                 "help": "Every exception needs a decision, a decider and an end date.",
                 "columns": [
                     {"id": "exception", "label": "Exception", "type": "text"},
                     {"id": "decision", "label": "Decision / condition", "type": "text"},
                     {"id": "decided_by", "label": "Decided by", "type": "text"},
                     {"id": "expires", "label": "Expires (YYYY-MM-DD)", "type": "text"},
                 ]},
                {"id": "gov_literacy", "type": "table", "required": False,
                 "label": "AI-literacy record (Art. 4): who was trained on this system",
                 "columns": [
                     {"id": "role", "label": "Role / group", "type": "text"},
                     {"id": "training", "label": "Training / briefing", "type": "text"},
                     {"id": "date", "label": "Date (YYYY-MM-DD)", "type": "text"},
                 ]},
                {"id": "gov_register_contact", "type": "text", "required": False,
                 "label": "Contact for questions about this system (register entry)",
                 "placeholder": "e.g. ai-governance@example.org (synthetic)"},
                {"id": "gov_public_register", "type": "boolean", "required": False,
                 "label": "Listed in a public algorithm register (e.g. the Dutch "
                          "Algoritmeregister) or an internal AI register?"},
                {"id": "gov_dpia_ref", "type": "text", "required": False,
                 "label": "DPIA / FRIA reference (document id)",
                 "placeholder": "e.g. DPIA-2026-014"},
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
