"""OWASP GenAI Data Security lens.

Pure function `assess_data_security(answers) -> dict`. Maps an AI system to the
applicable **OWASP GenAI Data Security** risks (DSGAI01-DSGAI21), each carrying
its related OWASP LLM Top 10 item(s) and EU AI Act / GDPR / NIST AI RMF controls.
Relevance is driven by the structured intake (`sec_*`, `arch_*`, `data_*` fields),
so the lens adapts to the system — a public RAG helpbot surfaces a different data
surface than a self-contained classifier.

Deterministic and AI-free, like the governance classifier and the security lens.
Relevance reads only the structured fields (never narrative/free-text), so crafted
text cannot add or drop a risk (the same injection invariant; asserted in tests).

DSGAI risks have no official severity ranking, so the lens reports applicable
risks in the document's own DSGAI01..21 order rather than inventing a severity —
the architecture-aware *severity* story lives in the OWASP LLM Top 10 security
lens (`security.py`); this lens contributes data-governance breadth.
"""

from .knowledge import data_security as ds


def _truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "ja", "on", "1"}
    return bool(value)


def _select(answers, key):
    v = answers.get(key)
    return v.strip().lower() if isinstance(v, str) else ""


def assess_data_security(answers):
    """Return the applicable OWASP GenAI Data Security risks for the answers."""
    answers = answers or {}

    def a(key):
        return _truthy(answers.get(key))

    is_llm = a("sec_is_llm")
    external = a("sec_external_data")
    public = a("sec_public")
    agentic = a("sec_agentic")
    third_party = a("sec_third_party_models") or a("gpai_model")
    outputs = a("sec_outputs_to_systems")
    personal = a("data_personal") or a("data_special_category") or a("data_biometric")
    special = a("data_special_category")
    biometric = a("data_biometric")
    large_scale = answers.get("data_scale") == "large"
    eu_market = a("eu_market")
    synthetic = a("t_synthetic_content")
    api_write = a("arch_api_write")
    downstream = a("arch_downstream_actions")
    scope_all = _select(answers, "arch_data_scope") == "all-users"
    shared_sa = _select(answers, "arch_identity_model") == "shared-service-account"
    logging = a("arch_logging")
    # RAG is plausible if the corpus is user-modifiable, or the system is an LLM
    # working over personal/external content (mirrors the LLM08 relevance rule).
    rag = a("arch_rag_modifiable") or (is_llm and (personal or third_party))

    # DSGAI id -> (applies, reason). Reads only structured fields.
    rules = {
        "DSGAI01": (is_llm and (personal or external or public),
                    "an LLM exposed to untrusted input and/or sensitive data can "
                    "be made to disclose it"),
        "DSGAI02": (agentic or outputs or api_write or shared_sa,
                    "the system holds agent/tool credentials or a shared service "
                    "identity that can be exposed or over-scoped"),
        "DSGAI03": (is_llm,
                    "adopting GenAI risks unsanctioned ('shadow') tools and data "
                    "flows outside governance"),
        "DSGAI04": (external or third_party or rag,
                    "it ingests untrusted external data, third-party artifacts or "
                    "a modifiable corpus that could be poisoned"),
        "DSGAI05": (external or rag or outputs,
                    "unvalidated data flows through prompts, retrieval or outputs"),
        "DSGAI06": (agentic or third_party or outputs,
                    "data is exchanged with tools, plugins or downstream systems"),
        "DSGAI07": (is_llm or personal,
                    "GenAI data (prompts, embeddings, logs, outputs) needs "
                    "classification, retention and lifecycle governance"),
        "DSGAI08": (personal or eu_market,
                    "personal-data processing / EU market exposure brings privacy "
                    "and AI-Act compliance obligations"),
        "DSGAI09": (synthetic or biometric,
                    "multimodal capture (images/audio/biometrics) can ingest more "
                    "than intended across channels"),
        "DSGAI10": (synthetic or personal,
                    "synthetic or 'anonymised' data derived from real data can "
                    "leak the original"),
        "DSGAI11": (scope_all or shared_sa or public,
                    "multiple users/tenants share the system, risking context or "
                    "memory bleed across the boundary"),
        "DSGAI12": (outputs or api_write or downstream,
                    "a natural-language-to-data gateway (LLM-to-SQL/API) reaches "
                    "backend data or actions"),
        "DSGAI13": (rag,
                    "a vector store / retrieval layer holds embedded data"),
        "DSGAI14": (personal or logging,
                    "telemetry, logs and traces can capture prompts and outputs "
                    "verbatim"),
        "DSGAI15": (is_llm and (personal or external or rag),
                    "context windows can be over-filled with more data than the "
                    "task needs"),
        "DSGAI16": (agentic or outputs or downstream,
                    "an assistant with reach into endpoints/sessions can overreach "
                    "into local data"),
        "DSGAI17": (large_scale or public or rag,
                    "data stores (training data, vectors, memory) must stay "
                    "available and resilient"),
        "DSGAI18": (personal or third_party,
                    "a model trained on sensitive data is exposed to inference / "
                    "reconstruction attacks"),
        "DSGAI19": (personal or special,
                    "human labelers and reviewers may be over-exposed to raw "
                    "sensitive data"),
        "DSGAI20": (public or third_party,
                    "an exposed or valuable model is a target for extraction / IP "
                    "replication"),
        "DSGAI21": (external or rag,
                    "a poisonable retrieval pipeline can be steered to produce "
                    "false or biased output"),
    }

    risks = []
    for oid in ds.ORDER:
        applies, reason = rules[oid]
        if not applies:
            continue
        info = ds.DSGAI[oid]
        risks.append({
            "id": oid,
            "name": info["name"],
            "why": reason,
            "summary": info["summary"],
            "owasp_refs": list(info["owasp_refs"]),
            "ai_act_refs": list(info["ai_act_refs"]),
            "gdpr_refs": list(info["gdpr_refs"]),
            "nist_refs": list(info["nist_refs"]),
            "mitigation": info["mitigation"],
        })

    answered = any(a(k) for k in (
        "sec_is_llm", "sec_third_party_models", "sec_external_data",
        "sec_agentic", "sec_public", "sec_outputs_to_systems",
        "data_personal", "data_special_category", "data_biometric"))

    if not risks:
        summary = (
            "No OWASP GenAI Data Security risks were triggered by the answers. "
            + ("Provide the AI security context (section 8) and data answers "
               "(section 6) for a meaningful assessment." if not answered else
               "Baseline data governance and minimisation still apply.")
        )
    else:
        summary = (
            f"{len(risks)} of 21 OWASP GenAI Data Security risks (DSGAI01-21) "
            "apply, mapped to the OWASP LLM Top 10, EU AI Act Art. 10 (data "
            "governance) and the GDPR where personal data is processed."
        )

    return {
        "risks": risks,
        "summary": summary,
        "count": len(risks),
        "answered": answered,
        "provenance": ds.PROVENANCE,
        "disclaimer": ds.DISCLAIMER,
    }
