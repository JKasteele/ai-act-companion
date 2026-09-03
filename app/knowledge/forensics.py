"""Forensic readiness for AI systems — can the organisation reconstruct and
evidence what an AI system did, why, with which data and model version, after
an incident, a complaint, a regulator request or a dispute?

The EU AI Act makes this a design requirement (Art. 12: systems must be able
to log), a retention duty (Art. 19 / Art. 26(6): at least six months) and an
evidence-preservation duty (Art. 73: do not alter the system before reporting).
Classic forensic-readiness thinking (Rowlingson, 2004) adds what the AI-specific
guidance leaves out: integrity, chain of custody and a legal-hold procedure.
Because model output is non-deterministic, evidence comes from *recording*, not
from re-running — so the artefacts below have to exist at the time of the event.

Provenance / honesty:
  * EU AI Act, GDPR, DORA and NIS2 references are to the public legal texts.
  * ISO/IEC 27001:2022 and ISO/IEC 42001:2023 entries reproduce control *titles*
    only. CIS Control 8 safeguard titles are public. MITRE ATLAS AML.M0024 and
    OWASP AI Exchange #MONITORUSE are public.
  * The register, the scoring and the crosswalk are Companion-derived; the
    reporting clocks for DORA are per the RTS and must be verified for the
    entity's classification. See PROVENANCE; ship it in any rendered output.
"""

# --- What can be logged: the fr_log_scope options ---------------------------
# (value, label)
LOG_SCOPE_OPTIONS = [
    ("inference_io", "Inference records: input, output, timestamp, calling identity"),
    ("parameters_seed", "Inference parameters (temperature, top-p, seed)"),
    ("model_version", "Exact model version / weights hash / endpoint revision per inference"),
    ("system_prompt_version", "System-instruction (prompt template) version + hash"),
    ("retrieval_snapshot", "Retrieval snapshot: which documents/chunks were in the context"),
    ("tool_calls", "Agent tool calls: tool, arguments, identity, permission, approval, result"),
    ("human_override", "Human-oversight events: who reviewed, who overrode, when, why"),
    ("data_access", "Access and authorisation logs on the underlying data"),
    ("config_changes", "Change records: model/prompt/config releases, approver, timestamp"),
    ("guardrail_config", "Guardrail / filter configuration in force at time T"),
    ("training_snapshot", "Training/validation set snapshot or hash, hyperparameters, seeds"),
    ("eval_reports", "Evaluation and bias reports per release, with group statistics"),
    ("drift_metrics", "Drift measurements and threshold breaches"),
    ("incident_file", "Incident file: timeline, root cause, notifications, decisions"),
]

# --- Evidence artefacts (the evidence register) ------------------------------
# (id, artefact, proves, legal/standard anchors, typical location,
#  relevance: "always" | "llm" | "agentic" | "provider" | "high")
EVIDENCE_ARTEFACTS = [
    ("model_version", "Model identity: name, version, weights hash, provider, endpoint revision",
     "\"this model, this version, was running\"",
     "Art. 12(2), Annex IV(2)(b); ATLAS AML.M0024", "model registry", "always"),
    ("system_prompt_version", "System-instruction version: prompt template + hash",
     "\"this instruction applied at the time\"",
     "Art. 12(2), Art. 13(3); OWASP AI Exchange #MONITORUSE", "prompt repo under version control",
     "llm"),
    ("inference_io", "Inference record: input, output, timestamp, calling identity",
     "\"this went in, that came out\"",
     "Art. 12(1)–(2), Art. 26(6); ISO 27001 8.15", "application log / trace span", "always"),
    ("parameters_seed", "Inference parameters: temperature, top-p, seed",
     "reproducibility limits are known and documented",
     "Art. 12(2), Art. 15(1); EIOPA Opinion Annex I §2", "application log", "llm"),
    ("retrieval_snapshot", "Retrieval snapshot: documents/chunks in the context, with source id + version",
     "\"this was in the context\"",
     "Art. 12(2); OWASP LLM08 (immutable retrieval logs)", "RAG log, vector-store version", "llm"),
    ("tool_calls", "Tool-call trace: tool, arguments, identity, permission, approval state, result",
     "\"the agent did this, authorised by that\"",
     "Art. 12(2), Art. 14; ATLAS AML.M0024; CIS MCP guide", "agent gateway", "agentic"),
    ("human_override", "Human-oversight events: who saw what, who overrode, when, with what reason",
     "Art. 14 oversight and GDPR Art. 22 human intervention actually happened",
     "Art. 14(4), Art. 26(2); GDPR Art. 22(3)", "workflow / case system", "always"),
    ("lineage", "Data lineage: source → preparation → training/input set → model → output",
     "Art. 10 data governance; separation of data domains",
     "Art. 10(2)(b)–(c), Annex IV(2)(d); GDPR Art. 5(2)", "data catalogue (section 11)", "always"),
    ("training_snapshot", "Training/validation set snapshot or hash + datasheet, hyperparameters, seeds",
     "\"it was trained on this\"",
     "Art. 10, Art. 11 + Annex IV(2)(d),(g); EIOPA Opinion Annex I §2", "data lake, version control",
     "provider"),
    ("eval_reports", "Evaluation and bias reports per release, with group statistics",
     "non-discrimination claim; Art. 10(5) processing was necessary",
     "Art. 10(2)(f)–(g), Art. 15(1); NIST MEASURE 2.11", "MLOps artefacts", "high"),
    ("drift_metrics", "Drift measurements and threshold breaches",
     "post-market monitoring actually ran",
     "Art. 72, Art. 26(5); DNB expectation", "monitoring platform", "high"),
    ("config_changes", "Change records: which model/prompt/config went live when, approved by whom",
     "\"which version was running on the day of the complaint\"",
     "Art. 12(2), Art. 17(1); ISO 27001 8.32", "CI/CD, change management", "always"),
    ("guardrail_config", "Guardrail / filter configuration at time T",
     "\"the block was on\"",
     "Art. 15(4)–(5); ISO 27001 8.9", "policy-as-code repo", "llm"),
    ("data_access", "Access and authorisation logs on the underlying data",
     "GDPR Art. 32 security; who could reach the data",
     "GDPR Art. 32; ISO 27001 8.15; NEN 7510", "IAM / SIEM", "always"),
    ("incident_file", "Incident file: timeline, root-cause analysis, notifications, decisions",
     "Art. 73 report; DORA / GDPR Art. 33(5) documentation duty",
     "Art. 73; GDPR Art. 33(5); ISO 27001 5.24–5.27", "GRC system", "always"),
    ("integrity", "Integrity evidence: hashes, WORM retention, timestamps, chain of custody",
     "the evidence itself was not altered",
     "ISO 27001 5.28, 8.15, 8.17; CIS 8.4/8.9/8.10; ISO/IEC 27037", "archive", "always"),
]

# --- Readiness dimensions (each scored 0 / 1 / 2) ---------------------------
# (id, name, what 2 means)
READINESS_DIMENSIONS = [
    ("scope", "Log scope", "Inference, model version and the artefacts the architecture needs "
                           "are all recorded."),
    ("retention", "Retention", "Retention meets the Art. 19 / 26(6) floor (6 months) or a "
                               "documented longer sector term, with a recorded basis."),
    ("integrity", "Log integrity", "Tamper-evident logs (hash chain / WORM) or signed records "
                                   "with an independent time anchor."),
    ("time", "Time synchronisation", "One synchronised time source across all evidence sources."),
    ("model_version", "Model & prompt pinning", "Exact model revision and prompt version are "
                                                "recorded per inference."),
    ("override", "Oversight evidence", "Human reviews and overrides are logged with reason."),
    ("vendor", "Supplier evidence", "Own logs suffice or a contractual right of access to the "
                                    "supplier's logs exists (Art. 25(4); DORA Art. 30(3))."),
    ("legal_hold", "Legal hold", "A documented evidence-freeze procedure exists (stop rotation, "
                                 "pin the model version) — Art. 73 forbids altering the system "
                                 "before reporting."),
]

MAX_SCORE = 2 * len(READINESS_DIMENSIONS)

# (upper bound inclusive, band label)
BANDS = [
    (5, "Not ready"),
    (10, "Partially ready"),
    (14, "Ready with gaps"),
    (MAX_SCORE, "Forensic-ready"),
]

# --- Parallel reporting clocks ---------------------------------------------
# One incident can start several clocks with different start triggers. The AI
# Act row is built from eu_ai_act.ART_73_TIMELINE at render time (single source
# of truth); these are the other regimes.
# (regime, trigger, clock starts at, deadlines, recipient, condition, note)
OTHER_CLOCKS = [
    ("GDPR Art. 33 / 34", "personal-data breach", "awareness",
     "72 h to the supervisory authority; data subjects 'without undue delay' when high risk",
     "Autoriteit Persoonsgegevens (NL)", "personal_data", ""),
    ("DORA Art. 19", "major ICT-related incident", "classification (initial) / detection",
     "initial notification 4 h after classification and no later than 24 h after detection; "
     "intermediate report 72 h; final report 1 month",
     "financial supervisor (DNB)", "financial",
     "Deadlines per the DORA RTS/ITS on incident reporting — verify against the entity's "
     "classification thresholds."),
    ("NIS2 / Cyberbeveiligingswet", "significant incident", "awareness",
     "24 h early warning; 72 h notification; 1 month final report",
     "national CSIRT / competent authority", "nis2",
     "Only where the organisation is an essential or important entity under the "
     "Cyberbeveiligingswet; for financial entities DORA is lex specialis."),
]

# --- Crosswalk ---------------------------------------------------------------
# (topic, EU AI Act, ISO/IEC 42001, ISO/IEC 27001:2022, CIS Control 8, other)
CROSSWALK = [
    ("Logging capability & scope", "Art. 12(1)–(2), Art. 13(3)(f)", "A.6.2.8",
     "8.15 Logging", "8.2, 8.5", "ATLAS AML.M0024; OWASP AI Exchange #MONITORUSE"),
    ("Retention", "Art. 19(1)–(2), Art. 26(6)", "A.6.2.8", "8.15, 5.33 Protection of records",
     "8.3, 8.10", "GDPR Art. 5(1)(e); Solvency II Del. Reg. 2015/35 Art. 258"),
    ("Integrity & chain of custody", "Art. 12(2) traceability", "A.6.2.8",
     "5.28 Collection of evidence, 8.15", "8.9", "ISO/IEC 27037 / 27043; NIS2 guidance §3.2.5"),
    ("Time synchronisation", "—", "—", "8.17 Clock synchronization", "8.4",
     "NIS2 guidance §3.2.6"),
    ("Human-oversight evidence", "Art. 14(4), Art. 26(2)", "A.9.2", "8.15", "8.5",
     "GDPR Art. 22(3); EIOPA Opinion §3.29–3.33"),
    ("Supplier evidence", "Art. 25(4), Art. 13", "A.10.3", "5.19–5.22 Supplier relationships",
     "8.12 Collect service provider logs", "DORA Art. 28–30"),
    ("Incident reporting & evidence preservation", "Art. 73, Art. 26(5)", "A.8.3, A.8.4",
     "5.24–5.27 Incident management", "8.11", "GDPR Art. 33(5); DORA Art. 17–19; NIS2 Art. 23"),
    ("Evidence register / readiness programme", "Art. 17(1)(k),(m)", "A.2.2, A.3.2",
     "5.28", "8.1 Audit log management process", "Rowlingson (2004) steps 1–10"),
]

PROVENANCE = (
    "Evidence register, readiness scoring and crosswalk are a Companion-derived "
    "analytical structure, not an official template. Legal references: Regulation (EU) "
    "2024/1689 as amended by Regulation (EU) 2026/1744; GDPR; DORA (Regulation (EU) "
    "2022/2554); NIS2 as implemented by the Dutch Cyberbeveiligingswet. Standards are "
    "cited by public control titles only. Rowlingson, R. (2004), 'A Ten Step Process "
    "for Forensic Readiness', IJDE 2(3)."
)
