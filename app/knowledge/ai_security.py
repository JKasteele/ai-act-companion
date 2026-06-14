"""AI security knowledge base: OWASP Top 10 for LLM Applications (2025) +
MITRE ATLAS, cross-mapped to the EU AI Act and NIST AI RMF.

This is the "security lens": it complements the governance classification by
relating an AI system to concrete AI-security threats and their controls. Each
OWASP item carries the relevant MITRE ATLAS technique(s), the EU AI Act
article(s) that demand the control (chiefly Art. 15 - accuracy, robustness and
cybersecurity, whose para. 5 explicitly names data/model poisoning, adversarial
examples, model evasion and confidentiality attacks), the NIST AI RMF
subcategory (anchored on MEASURE 2.7 - security & resilience), and a mitigation.

Identifier provenance:
  * OWASP IDs/titles verified against genai.owasp.org (2025 edition).
  * MITRE ATLAS IDs/names verified against the canonical atlas-data ATLAS.yaml
    (atlas.mitre.org). Note ATLAS renamed many techniques "ML" -> "AI".
  * The OWASP <-> ATLAS <-> EU AI Act <-> NIST mappings are NOT an official
    published crosswalk - they are a Companion-derived analytical alignment that
    is traceable to the verified identifiers above.

Self-assessment aid, not a substitute for a penetration test or red-team.
"""

# Each entry: name, summary, atlas [(id, name)], ai_act_refs, nist_refs, mitigation.
# `atlas_note` flags OWASP items that ATLAS has no single dedicated technique for
# (modelled as an attack chain instead).
OWASP_LLM_TOP10 = {
    "LLM01": {
        "id": "LLM01:2025",
        "name": "Prompt Injection",
        "summary": "Crafted inputs (direct or indirect, e.g. via retrieved "
                   "content) alter the model's behaviour, bypassing instructions "
                   "or controls.",
        "atlas": [("AML.T0051", "LLM Prompt Injection"),
                  ("AML.T0054", "LLM Jailbreak")],
        "ai_act_refs": ["Art. 15(5) (resilience to manipulation)", "Art. 9"],
        "nist_refs": ["MEASURE 2.7"],
        "mitigation": "Constrain and validate inputs, separate system/user "
                      "content, least-privilege tool access, output filtering, "
                      "and human approval for high-impact actions.",
    },
    "LLM02": {
        "id": "LLM02:2025",
        "name": "Sensitive Information Disclosure",
        "summary": "The model reveals confidential data (training data, PII, "
                   "secrets) through its outputs or via inference attacks.",
        "atlas": [("AML.T0057", "LLM Data Leakage"),
                  ("AML.T0024", "Exfiltration via AI Inference API")],
        "ai_act_refs": ["Art. 10 (data governance)", "Art. 15 (cybersecurity)"],
        "nist_refs": ["MEASURE 2.7", "MEASURE 2.10"],
        "mitigation": "Data minimisation, scrubbing/PII redaction, output "
                      "filtering, access controls, and limiting memorisation.",
    },
    "LLM03": {
        "id": "LLM03:2025",
        "name": "Supply Chain",
        "summary": "Vulnerabilities in third-party models, datasets, plugins or "
                   "dependencies compromise integrity or security.",
        "atlas": [("AML.T0010", "AI Supply Chain Compromise")],
        "ai_act_refs": ["Art. 15", "Art. 25 (responsibilities along the value chain)"],
        "nist_refs": ["GOVERN 1.1", "MEASURE 2.7"],
        "mitigation": "Vet and pin model/dataset/dependency provenance, verify "
                      "signatures, maintain an SBOM/AIBOM, scan dependencies.",
    },
    "LLM04": {
        "id": "LLM04:2025",
        "name": "Data and Model Poisoning",
        "summary": "Manipulated training/fine-tuning/embedding data introduces "
                   "backdoors, bias or degraded integrity.",
        "atlas": [("AML.T0020", "Poison Training Data"),
                  ("AML.T0031", "Erode AI Model Integrity")],
        "ai_act_refs": ["Art. 15(5) (data/model poisoning)", "Art. 10 (data governance)"],
        "nist_refs": ["MEASURE 2.7", "MAP 2.3"],
        "mitigation": "Vet data sources, integrity checks, anomaly detection on "
                      "training data, and provenance tracking.",
    },
    "LLM05": {
        "id": "LLM05:2025",
        "name": "Improper Output Handling",
        "summary": "Unvalidated model output is passed to downstream systems "
                   "(code, SQL, shell, browsers), enabling injection/XSS/RCE.",
        "atlas": [("AML.T0051", "LLM Prompt Injection")],
        "atlas_note": "No dedicated ATLAS technique; modelled as an "
                      "injection-driven downstream chain.",
        "ai_act_refs": ["Art. 15 (robustness)"],
        "nist_refs": ["MEASURE 2.7"],
        "mitigation": "Treat model output as untrusted: encode/escape, validate "
                      "against schemas, and sandbox downstream execution.",
    },
    "LLM06": {
        "id": "LLM06:2025",
        "name": "Excessive Agency",
        "summary": "Excessive functionality, permissions or autonomy lets the "
                   "system take damaging actions on ambiguous or manipulated input.",
        "atlas": [("AML.T0051", "LLM Prompt Injection")],
        "atlas_note": "No single ATLAS technique; modelled as a chain "
                      "(injection vector -> downstream action/impact).",
        "ai_act_refs": ["Art. 14 (human oversight)", "Art. 9 (risk management)"],
        "nist_refs": ["MANAGE 2.3", "GOVERN 2.1"],
        "mitigation": "Least-privilege tools/permissions, human-in-the-loop for "
                      "consequential actions, and bounded scopes.",
    },
    "LLM07": {
        "id": "LLM07:2025",
        "name": "System Prompt Leakage",
        "summary": "Disclosure of system prompts exposes secrets, logic or "
                   "controls that were wrongly relied upon for security.",
        "atlas": [("AML.T0056", "Extract LLM System Prompt"),
                  ("AML.T0057", "LLM Data Leakage")],
        "ai_act_refs": ["Art. 15 (cybersecurity)"],
        "nist_refs": ["MEASURE 2.7"],
        "mitigation": "Never put secrets/authz logic in the system prompt; "
                      "enforce controls server-side and assume the prompt is public.",
    },
    "LLM08": {
        "id": "LLM08:2025",
        "name": "Vector and Embedding Weaknesses",
        "summary": "Weaknesses in RAG vector stores/embeddings enable data "
                   "leakage, poisoning of retrieved context, or access bypass.",
        "atlas": [("AML.T0051.001", "LLM Prompt Injection: Indirect"),
                  ("AML.T0024", "Exfiltration via AI Inference API")],
        "ai_act_refs": ["Art. 10 (data governance)", "Art. 15"],
        "nist_refs": ["MEASURE 2.7"],
        "mitigation": "Access-control and tenant-isolate the vector store, "
                      "validate ingested documents, and audit retrieval.",
    },
    "LLM09": {
        "id": "LLM09:2025",
        "name": "Misinformation",
        "summary": "Hallucinated or biased output is relied upon as fact, causing "
                   "harm or unsafe decisions.",
        "atlas": [("AML.T0031", "Erode AI Model Integrity")],
        "atlas_note": "Partly a safety/trust issue outside ATLAS's attack scope.",
        "ai_act_refs": ["Art. 13 (transparency)", "Art. 50", "Art. 15 (accuracy)"],
        "nist_refs": ["MEASURE 2.5", "MEASURE 2.8"],
        "mitigation": "Grounding/RAG with citations, uncertainty signalling, "
                      "human review, and clear AI-output labelling.",
    },
    "LLM10": {
        "id": "LLM10:2025",
        "name": "Unbounded Consumption",
        "summary": "Uncontrolled resource use (inference flooding, model "
                   "extraction, cost harvesting) causes denial of service or cost.",
        "atlas": [("AML.T0029", "Denial of AI Service"),
                  ("AML.T0034", "Cost Harvesting")],
        "ai_act_refs": ["Art. 15 (robustness & availability)"],
        "nist_refs": ["MEASURE 2.7", "MANAGE 4.1"],
        "mitigation": "Rate limiting and quotas, input/size limits, monitoring "
                      "and alerting on anomalous usage.",
    },
}

PROVENANCE = (
    "Mappings are Companion-derived analytical alignments, traceable to verified "
    "OWASP (2025) and MITRE ATLAS identifiers - not an official published "
    "crosswalk."
)

DISCLAIMER = (
    "The AI security lens maps the system to the OWASP Top 10 for LLM "
    "Applications (2025) and MITRE ATLAS as a self-assessment aid. It does not "
    "replace a penetration test, red-team exercise or formal threat model."
)
