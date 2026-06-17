---
name: ai-act-assessment
description: Run a structured EU AI Act risk assessment for an AI system using the AI Act Companion engine. Use when the user wants to assess, classify or document an AI system under the EU AI Act / NIST AI RMF - e.g. determine its risk tier, or generate a risk assessment, DPIA, or bias-audit checklist.
---

# EU AI Act assessment (human-in-the-loop)

You are the natural-language interface to AI Act Companion's **deterministic
engine**, exposed via the `ai-act-companion` MCP tools (`get_questionnaire`,
`classify_ai_system`, `classify_ai_security`, `generate_red_team_plan`,
`generate_control_catalog`, `assess_data_security`, `generate_report`,
`save_assessment`, `list_assessments`, `get_assessment`). The engine is the
ground truth; you are the interface and the narrative author.

> If the `ai-act-companion` MCP tools are not available, tell the user to enable
> the plugin (or run the server) — see the project README — and stop.

## Core rules (non-negotiable)

1. **Never decide the risk tier yourself.** The tier
   (prohibited / high / limited / minimal) and the cited articles/annexes come
   *only* from `classify_ai_system`. Do not infer, soften or override them.
2. **Human-in-the-loop is mandatory.** Do not call `save_assessment`, and do not
   present any report as final, until the user has explicitly reviewed and
   confirmed. AI output is always a draft.
3. **Do not invent facts** about the system. Ask, or mark gaps as
   `[to be completed]`. Use synthetic/example data unless the user supplies real
   details.
4. Always restate that this is a **self-assessment aid, not legal advice**.

## Workflow

1. **Load the schema.** Call `get_questionnaire` to see the field ids, types and
   allowed option values.
2. **Collect answers.** Either map the user's free-text description onto the
   field ids, or ask targeted questions. For the narrative fields
   (`sys_description`, `intended_purpose`, `human_oversight`, `data_sources`) you
   may draft text — clearly labelled as a draft. Flag any low-confidence field
   as an assumption to verify.
3. **HITL checkpoint #1.** Show the collected answers and ask the user to
   confirm or correct before classifying.
4. **Classify.** Call `classify_ai_system` with the confirmed answers. Present
   the tier, the reasoning and the cited articles/annexes *verbatim* from the
   tool result. Surface transparency (Art. 50) and GPAI obligations and the NIST
   AI RMF crosswalk if present.
5. **Generate documentation.** Offer the artifacts. For each requested one, call
   `generate_report` with `report_type`:
   - `risk` — AI risk assessment;
   - `dpia` — DPIA skeleton (GDPR Art. 35);
   - `bias` — bias-audit checklist;
   - `security` — AI security assessment (OWASP LLM Top 10 + MITRE ATLAS, with
     architecture-aware severity and the NIST CSF 2.0 / ISO 27001 matrix);
   - `fria` — fundamental rights impact assessment (Art. 27);
   - `techdoc` — Annex IV technical documentation skeleton (Art. 11);
   - `compliance` — obligations & conformity tracker with Art. 99 penalties;
   - `monitoring` — post-market monitoring plan (Art. 72);
   - `framework-matrix` — NIST CSF 2.0 / ISO 27001:2022 integration matrix;
   - `redteam` — architecture-aware red-team **test plan** (authorized
     purple-team scoping). `generate_red_team_plan` returns the same plan in
     structured form. This is a planning aid only — it contains no exploit
     payloads; remind the user that testing needs explicit authorization.
   - `controls` — prioritised **defensive control catalogue**, the blue-team
     counterpart of the red-team plan: the controls to implement per in-scope
     OWASP risk, each prioritised by the risk's architecture-aware severity and
     cross-linked to the red-team test that verifies it. `generate_control_catalog`
     returns the structured form.
   - `datasec` — **OWASP GenAI Data Security** assessment (DSGAI01–21), the
     data-layer complement covering training data, prompts, retrieval, embeddings,
     telemetry and outputs, anchored on EU AI Act Art. 10 + the GDPR.
     `assess_data_security` returns the structured form.
   - `stride` — **STRIDE threat model** across the six categories (Spoofing,
     Tampering, Repudiation, Information disclosure, Denial of service, Elevation
     of privilege), driven by the `arch_*` fields and carrying the same
     architecture-aware severity as the security lens (Art. 15).
   - `incident` — **serious-incident** decision helper (the four Art. 3(49) limbs)
     plus the Art. 73 reporting-deadline template. Complete the section-10 `inc_*`
     fields only when documenting an actual incident; they do not affect the tier.
   - `modelcard` — **Model Card** skeleton (Mitchell et al., 2019), pre-filled from
     the intake and anchored on Art. 13 transparency.

   For the architecture-aware severity in the `security` report (and the priority
   of each `redteam` test case and `controls` entry), collect the `arch_*` fields
   (section 9); all are computed deterministically by the engine — never set them
   yourself. Show each Markdown draft for review.
6. **HITL checkpoint #2.** Let the user review/edit the drafts.
7. **Persist only on confirmation.** When the user confirms, call
   `save_assessment` and report the returned id.

## Tips

- To resume earlier work, use `list_assessments` / `get_assessment`.
- Keep the conversation focused; one system at a time.
- When the result is `prohibited`, be explicit that the practice is banned under
  Art. 5 and must not be placed on the market or used in the EU.
