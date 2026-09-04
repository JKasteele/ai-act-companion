# Changelog

All notable changes are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/); the project uses
[semantic versioning](https://semver.org/).

## [Unreleased]

### Added
- **Abuse hardening for the hosted AI provider**: the per-client cap keys on the proxy-appended hop of `X-Forwarded-For` (a client-supplied first value no longer bypasses it), a per-client cooldown (`AI_COOLDOWN_SECONDS`, 20 s), a one-hour dedupe cache for identical descriptions (repeats cost nothing), tighter defaults (`AI_DAILY_CALLS` 25, `AI_BUDGET_USD` 4.00) so the in-app ceiling stays under the Console spend limit, and Claude Haiku 4.5 as the default hosted model.
- Hosted Anthropic provider (Claude Haiku 4.5 by default) with a spend guard: a lifetime
  USD budget, a daily call cap and a per-IP daily cap (`AI_BUDGET_USD`,
  `AI_DAILY_CALLS`, `AI_CALLS_PER_IP_DAY`), all persisted next to the
  assessments. When any cap is hit — or no `ANTHROPIC_API_KEY` is set — the
  service degrades to the existing `replay` provider and labels the draft as
  such, so the public demo can offer real AI-assist drafts without risking an
  open-ended bill. Uses prompt caching (`cache_control: ephemeral`) on the
  stable FIELDS digest of the prefill prompt to cut repeat-request cost.
- **Sandbox showcase.** The public demo now shows the AI workflow instead of a
  bare form: a *replay* LLM provider (`LLM_PROVIDER=replay`, auto-selected in
  `DEMO_MODE`) replays drafts from the shipped synthetic examples — labelled as
  such, validated like model output, governance sections left for the human —
  so free text → draft → review → deterministic classification is visible with
  no model and no egress; a **How it works** strip (describe → engine decides →
  you review → evidence) with live counters; a **guided tour** button (loads the
  insurer example, classifies, opens the forensic-readiness report); and a
  collapsible **MCP transcript** reconstructed from the engine's real output
  (`scripts/build_demo_assets.py` → `static/demo/mcp_transcript.json`).
- **Two more health-insurer examples** so the three insurer cases cover three
  tiers: `health_insurer_claims_fraud` (claims anomaly & fraud scoring — minimal
  risk under the AI Act but profiling of insured persons: GDPR Art. 22, EIOPA
  Opinion, ZN separation of basic/supplementary data, DORA via a vendor dataset)
  and `health_insurer_service_assistant` (GenAI service assistant on a hosted
  model with claim-status tools — limited risk, health data in prompts, agentic
  controls, governance still in review). Both in the golden set (now 37 cases) and
  the gallery. `foundation_model` gains training-data governance (provenance,
  TDM opt-out, Art. 53 training-content summary) and evidence fields; the
  gallery now also renders its GPAI and data-governance reports.
- `tests/test_examples.py`: every example uses only known fields, classifies
  to its expected tier, and renders all 21 reports in both languages; README
  gains an example index.

### Changed
- **Regulation (EU) 2026/1744 legal pass.** The intake and deterministic engine
  now model the amended Annex-I safety-component filters, safety of persons or
  property, the limited Section-B regime, the Section-A Art. 2(13) delegated-act
  watchpoint, Art. 4a, the new Art. 5(1)(ba)/(bb) prohibitions and their actor
  gateways/application date, and the distinction between providing and merely
  integrating a GPAI model.
- **Actor- and route-specific outputs.** Provider/deployer artifacts, FRIA scope,
  Art. 49 registration and data-governance duties now follow the recorded legal
  role and Annex-I/III route. Art. 4 is described as proportionate literacy
  support measures; the evidence record is explicitly a practical artifact, not
  a prescribed statutory form.
- Portfolio documentation now presents the project as an authored case study,
  distinguishes the maintainer-curated legal regression set from independent
  validation, and aligns demo/privacy/configuration claims with runtime behavior.

### Fixed
- `DEMO_MODE` visitor submissions are now stateless end to end: assessments are
  never written to the inventory, transient reports render directly from the
  submitted answers, and read/export endpoints expose only curated examples.
- Corrected the Art. 2 territorial test (third-country **output used in the
  Union**, not merely effects on people), removed deleted Art. 10(5) references,
  and prevented Annex-I Section-B systems from inheriting Art. 5, Art. 50 or the
  ordinary Chapter-III compliance pack through generic flags.
- Added bounded API inputs, non-empty/trimmed system names, an unprivileged
  container user, blocking mypy/dependency-audit gates and a frontend syntax
  check in CI.
- Raised the MCP and screenshot-tooling dependency floors to patched releases;
  CI audits the complete resolved dev/MCP environment, including transitive
  packages, rather than only the core requirements file.

## [0.9.2] - 2026-09-03

### Added
- **Agentic tool-call controls.** For systems flagged `sec_agentic` the control
  catalogue adds CTL-LLM06-02..05 — per-call identity binding and per-tool least
  privilege (no token passthrough), a tool allowlist with an approval gate for
  irreversible actions, a tamper-evident tool-call audit trail with correlation
  ids (MITRE ATLAS AML.M0024, OWASP AI Exchange #MONITORUSE, EU AI Act Art. 12)
  and loop / blast-radius bounds with a kill switch (Art. 14(4)(e)) — each
  verified by new red-team tests RT-LLM06-02 (tool privilege escalation /
  identity confusion) and RT-LLM06-03 (goal hijack through tool output),
  referencing the OWASP Top 10 for Agentic Applications 2026 (ASI01–03/05/08)
  and the CIS MCP Companion Guide. New gate `agentic` (strictly agentic, narrower
  than `agentic_or_write`).
- **`--lang nl`.** `reports.render(..., lang="nl")` prepends a Dutch summary
  block — risk tier, applicability (Omnibus-aware), determining findings,
  transparency duties, recommended documentation, personal-data flag and the
  governance headlines (forensic readiness, governance status / next review,
  data-governance gaps) — built from the structured results, never from free
  text; the citable English body is unchanged. Exposed as CLI `--lang`, API
  `?lang=`, MCP `lang` and a language selector above the report preview.

### Changed
- **MCP SDK 2.x supported.** `mcp_server.py` imports `MCPServer` from mcp 2.x and
  falls back to `FastMCP` on 1.x; the `mcp` extra now accepts `mcp>=1.2,<3`.
  Verified against mcp 1.29 and 2.1.

## [0.9.1] - 2026-09-03

### Added
- **Governance register** (report 21, `governance`) and intake section 13
  (`gov_*`): policy owner, approval body, status, approval and review dates,
  exceptions with end dates (expired / open-ended flagged), the Art. 4
  AI-literacy record, register contact, public-register flag and DPIA reference.
  `app/governance.py` derives the next review from the approval date and a
  tier cadence (high 6 · limited 12 · minimal 24 months), an overdue flag,
  intake completeness per section and a gap list. Unparseable dates count as
  unknown, never as a pass.
- **Compliance-monitoring portfolio.** `/api/portfolio`, the inventory table and
  `/api/export.csv` now carry per system: forensic-readiness score and band,
  high data-governance gaps, governance status, next review (with overdue
  flag) and documentation completeness, plus roll-up counters. New
  `/api/register.csv`: an AI-register export with Algoritmeregister-style
  fields (name, purpose, legal basis, risk tier, Annex III area, human
  oversight, owners, contact, status, review dates).
- **Monitoring KPIs.** The post-market monitoring plan seeds KPI rows —
  primary metric vs. release baseline, drift, override rate (when a human is in
  or on the loop), complaints/objections, incidents and near-misses — with a
  review cadence derived from the risk tier.
- **MCP tools** `assess_data_governance`, `assess_forensic_readiness` and
  `governance_status` expose the structured forms of the three governance
  lenses (the `generate_report` Literal gains `governance`).
- Flagship examples (`grid_ops_agent`, `support_chatbot`,
  `hiring_cv_screening`, `health_insurance_pricing`) now carry sections 11–13,
  so the gallery shows data-governance, forensic-readiness and governance
  views for an agentic, a RAG, a provider and an insurer system.

### Changed
- Docs: golden set is 31 cases; DESIGN.md and the Claude Code plugin manifest
  list all report types; plugin manifest version follows the package.

## [0.9.0] - 2026-09-03

The governance-depth release: AI governance built on data governance, the
sector frameworks insurers and banks actually use, and forensic readiness.

### Added
- **Forensic readiness & evidence plan** (report 20, `forensics`). New intake
  section 12 (`fr_*`) and a pure assessment function (`app/forensics.py`) that
  derives an **evidence register** (16 artefacts — model identity, prompt version,
  inference record, parameters/seed, retrieval snapshot, tool-call trace,
  human-override events, lineage, training snapshot, evaluation/bias reports,
  drift, change records, guardrail config, data-access logs, incident file,
  integrity evidence — each mapped to the obligation it proves and its typical
  location; relevance depends on architecture and role), an 8-dimension
  **readiness score** (log scope, retention, integrity, time sync, model/prompt
  pinning, oversight evidence, supplier evidence, legal hold), a
  **retention-versus-minimisation** check (Art. 19/26(6) six-month floor vs. GDPR;
  special-category data in logs), the **parallel reporting clocks** (AI Act Art.
  73 from `ART_73_TIMELINE`, GDPR Art. 33/34, DORA Art. 19 for financial entities,
  NIS2/Cyberbeveiligingswet where in scope) and a crosswalk (ISO 27001 5.28 /
  8.15 / 8.17, ISO 42001 A.6.2.8, CIS Control 8, ATLAS AML.M0024, OWASP AI
  Exchange #MONITORUSE, Rowlingson 2004). The serious-incident report gains the
  same clocks table and a "preserve evidence first" note (Art. 73(6)). Free text
  cannot move the score (test).
- **Sector crosswalks and the DORA hook.** New knowledge module
  `app/knowledge/sector_frameworks.py`: ALTAI (EU HLEG, seven requirements)
  rendered in every risk report with EU AI Act / ISO 42001 anchors and the
  intake fields that evidence each requirement (answered vs. missing); for
  financial entities (`org_sector` = insurance / banking / other financial)
  the EIOPA AI governance principles (2021), DNB SAFEST (2019) and the AI
  Act's financial-institution carve-ins (Art. 9(10), 17(4), 18(3), 26(5)–(6),
  74(6)). The compliance tracker gains an "ICT third-party risk (DORA Art.
  28–30)" checklist when a financial entity relies on third-party models or
  vendor-origin datasets. New intake field `org_sector` (section 1).
- **Data-governance layer.** AI governance is built on data governance, so the
  intake gains section 11 (`dg_*`): data owner and data steward (distinct from the
  system owner), catalogue registration, a repeatable **dataset inventory**
  (origin, owner, steward, classification, purpose, retention, lawful basis),
  lineage, and seven data-quality dimensions (accuracy, completeness,
  consistency, timeliness, validity, uniqueness, representativeness & bias
  screening) each with an unknown / assessed / measured status. A new
  **`datagov` report** (19 report types) renders roles, inventory,
  classification & lawful basis, lineage, the quality table, an Art. 10(2)–(5)
  / Art. 26(4) requirement checklist, a **derived gap list** with severities
  and an ISO/IEC 42001 A.7 / NIST AI RMF / EIOPA / DAMA-DMBOK crosswalk. The
  DPIA pulls the personal-data datasets from the same inventory. New knowledge
  module `app/knowledge/data_governance.py`; new `table` question type in the
  questionnaire, rendered by the web form (add/remove rows) and accepted as a
  list of row objects by the CLI and MCP.
- **Annex III(5) split.** `hr_essential_subarea` narrows "essential services"
  to 5(a) public benefits, 5(b) creditworthiness, 5(c) life/health insurance
  risk assessment & pricing, or 5(d) emergency triage; findings cite the
  sub-point. For 5(b)/5(c) the classifier and the FRIA state the Art. 27(1)
  rule that the FRIA applies to *every* deployer, private ones included.
  `hr_insurance_scope` adds sector context for 5(c) (Dutch basic insurance
  under the Zvw, supplementary, life, other). New synthetic example
  `health_insurance_pricing.json` (also in the golden set and the gallery).
- "Data governance & quality record" added to the recommended artifacts for
  high-risk systems (and, as good practice, when personal data is processed).

### Changed
- The `hr_does_profiling` help text now states that profiling rules out the
  Art. 6(3) derogation (per the Commission's draft Art. 6(5) guidelines).

## [0.8.1] - 2026-09-03

Knowledge-base review: the **Digital Omnibus on AI** (Regulation (EU)
2026/1744, in force 27 July 2026) changed the EU AI Act application dates.

### Fixed
- **Application timeline (Art. 113) updated for the Digital Omnibus.** Annex III
  high-risk obligations now apply from **2 Dec 2027** (was 2 Aug 2026) and
  Annex I / regulated-product systems from **2 Aug 2028** (was 2 Aug 2027).
  Affects the "Applies from" headline in the risk report, the per-row dates in
  the obligations & conformity tracker, the portfolio due-date sort, the
  landing-page countdown and the timeline table. Art. 50 transparency, the
  penalty provisions and Art. 4 supervision keep their 2 Aug 2026 date; the
  timeline also records the 2 Dec 2026 grace period for machine-readable
  marking of pre-existing generative systems and the 19 May 2026 draft Art.
  6(5) guidelines.

### Added
- **Knowledge-base freshness stamp.** `eu_ai_act.py` now carries
  `KNOWLEDGE_VERSION`, `LAST_REVIEWED` and an `AMENDMENTS` list (name, effect,
  source URL). Every report header states which state of the law it reflects;
  `/api/timeline` exposes the stamp and the landing page shows it under the
  countdown. Tests pin the amended dates so a stale timeline fails CI.

### Changed
- The GitHub Action installs from PyPI now that the package is published: a new
  `version` input pins the PyPI release (default: latest); `ref` still installs
  from a git ref when set.
- Example gallery (`docs/examples/`) regenerated with the amended dates.

## [0.8.0] - 2026-08-26

A review-driven correctness, testing and hardening pass (see
[docs/ROADMAP-REVIEW.md](docs/ROADMAP-REVIEW.md)).

### Added
- **Three new report types** (18 total): EU **Declaration of Conformity**
  (Art. 47 + Annex V), EU-database **registration** data sheet (Art. 49 +
  Annex VIII), and a **GPAI obligations** report (Art. 53–55) with
  copyright-policy and training-content-summary templates.
- **MCP surface**: a `scan_repository` tool, a report-by-id path in
  `generate_report`, and a `confirmed` flag on `save_assessment` that enforces
  human-in-the-loop as a contract (nothing is stored without it).
- **PyPI release automation** — a tag-triggered `release.yml` using PyPI Trusted
  Publishing; `pip install ai-act-companion` works after the first `v*` tag.
- **Art. 2 scope exemptions** — intake fields and classifier logic for the
  military/defence (Art. 2(3)), scientific-R&D (Art. 2(6)), pre-market
  (Art. 2(8)) and personal-use (Art. 2(10)) carve-outs, each returning
  out-of-scope with the specific paragraph cited.
- **Provider vs. deployer obligations** — `HIGH_RISK_OBLIGATIONS` is split by
  role and filtered on `provider_role`, so a deployer is no longer shown
  provider-only conformity-assessment/CE-marking duties. Adds Art. 16/20/22/25.
- **GPAI open-source carve-out (Art. 53(2))** and a GPAI-aware applicability
  date, so a minimal-tier GPAI model no longer reports "no mandatory deadline".
- **Art. 4 AI literacy** surfaced as a baseline obligation for in-scope systems.
- New test suites: `test_cli.py`, `test_mcp.py`, `test_llm_service.py`,
  `test_storage.py`, plus report-injection and role-filtering cases; five new
  golden-set cases (exemptions, deployer-only, open-source GPAI). Coverage now
  reported in CI (`pytest-cov`), with a Windows matrix entry and a Docker smoke
  test.

### Changed
- **Report free-text is sanitised** before Markdown interpolation (pipes escaped,
  line breaks collapsed) so a crafted description cannot break tables or inject
  structure — the tier/severity were already injection-proof.
- **Atomic storage writes** (temp file + `os.replace`); single-read `load_all()`.
- **`DEMO_MODE` is enforced server-side** (deletion returns 403), no longer
  honour-system. AI-endpoint errors no longer leak raw exception text.
- Deduplicated the `_truthy`/`_select` helpers into `app/_normalize.py` (was
  copied across seven modules); report types now have a single source of truth
  (`reports.REPORT_CATALOG`) driving the API, frontend tabs and MCP tool.
- Frontend no longer fetches Google Fonts (privacy); removed dead code and
  tightened two `innerHTML` sinks.

### Fixed
- Out-of-scope systems no longer emit GPAI (Chapter V) obligations.
- `reports._bool` now matches the classifier's truthiness (e.g. `"0"`/`"off"`).

[0.8.0]: https://github.com/JKasteele/ai-act-companion/releases/tag/v0.8.0

## [0.7.0] - 2026-06-17

A distribution release: makes the project easy to *see* and to *adopt*.

### Added
- **Repository AI-usage scanner** (`app/scan.py`, `ai-act scan`) + a reusable
  **GitHub Action** (`action.yml`) — flags whether a codebase appears to use AI/ML
  (dependency manifests, source imports, model artifacts) and points to the EU AI
  Act questions worth asking (Art. 2/5/6/10/50). Deterministic, stdlib-only, no
  model calls; a relevance flag, **not** a classification. Writes a Markdown
  summary to the PR/job; `--fail-on-detect` can turn it into a gate.
- **Static example report gallery** (`docs/examples/`, generated by
  `scripts/build_gallery.py`) — real artifacts for the synthetic examples (risk,
  AI-security, STRIDE, red-team, controls, data-security, FRIA, …), viewable on
  GitHub without running anything. Linked from the README.
- **Demo inventory seeding** — in `DEMO_MODE`, the synthetic examples are
  pre-loaded so the inventory and the portfolio roll-up are populated on a fresh
  (ephemeral) public Space rather than starting empty.

### Changed
- Refreshed the README hero GIF and all screenshots against the v0.6.0 UI.

[0.7.0]: https://github.com/JKasteele/ai-act-companion/releases/tag/v0.7.0

## [0.6.0] - 2026-06-17

A visibility + polish release: a redesigned UI, a live EU AI Act deadline
countdown, and two new examples that exercise the security and GPAI depth.

### Added
- **UI refresh** — a refined "regtech" dark theme: Fraunces (display) / IBM Plex
  Sans (body) / IBM Plex Mono (legal citations), a layered atmospheric backdrop,
  a stronger hero, staggered load-in motion (respecting `prefers-reduced-motion`),
  and refined cards, tabs, badges and the report "document" preview. No engine or
  report-content changes; print/PDF output is unaffected.
- **EU AI Act deadline countdown** — the hero shows a live "N days until <next
  milestone>" pill (e.g. high-risk & Art. 50 obligations on 2 Aug 2026). Dates come
  from the knowledge base via a new `GET /api/timeline`; the countdown itself is
  presentational (client-side), so the deterministic engine stays date-independent.
- **Two new examples** — `GridSentinel autonomous operations agent` (Annex III-2
  critical-infrastructure, **High risk** with a **Critical** AI-security profile —
  showcases architecture-aware severity, STRIDE, the red-team plan and control
  catalogue) and `OpenScribe-7B foundation model` (a **GPAI** provider — showcases
  the Chapter V obligations and the OWASP GenAI Data Security lens). Six examples now.
- `docs/DEMO-SCRIPT.md` — a 60–90s demo-video script + shot list for the README
  hero / LinkedIn.

### Fixed
- Mixed-language UI: the form's select placeholder and Yes/No toggle now render in
  English (were `— kies —` / `Ja`/`Nee`).

[0.6.0]: https://github.com/JKasteele/ai-act-companion/releases/tag/v0.6.0

## [0.5.1] - 2026-06-17

Completes the last roadmap item: the ISO/IEC 42001 Annex A control mapping.

### Added
- **ISO/IEC 42001 Annex A control mapping** (`app/knowledge/iso_42001.py`) — the
  38 Annex A reference controls (A.2.2 … A.10.4), titles only, each tagged with
  its most-relevant EU AI Act article as a Companion-derived analytical alignment.
  Rendered as section 5.2.1 of the risk-assessment report to support drafting an
  AIMS Statement of Applicability alongside the assessment. The control list was
  cross-verified against multiple public summaries (the depth at which third-party
  summaries diverge); the 38-control count and the A.6.1.x / A.6.2.x life-cycle
  sub-structure match the standard.
- Tests (`tests/test_iso_42001.py`): the 38-control count, well-formedness, that
  every control resolves to a real EU AI Act article, full category coverage and
  rendering. 110 tests pass.

[0.5.1]: https://github.com/JKasteele/ai-act-companion/releases/tag/v0.5.1

## [0.5.0] - 2026-06-17

Adds the Tier 3 set: a STRIDE threat model that reuses the architecture-aware
severity, a serious-incident decision helper, a Model Card generator, and an
inventory portfolio roll-up.

### Added
- **STRIDE threat model** (`app/stride.py`, `stride` report) — models the system
  across the six STRIDE categories (Spoofing, Tampering, Repudiation, Information
  disclosure, Denial of service, Elevation of privilege), driven by the
  security-architecture fields (section 9). Four categories reuse the AI security
  lens's architecture-aware severity (`security.severity_for`) for the OWASP family
  they map to — so the STRIDE view and the OWASP severity view agree by
  construction — while Spoofing and Repudiation are scored directly from
  `arch_auth_strength` / `arch_logging`. Anchored on Art. 15 (and Art. 12 for
  Repudiation).
- **Serious-incident decision helper + report** (`app/incident.py`, `incident`
  report) — a boolean-driven helper over the four Art. 3(49) limbs that returns the
  binding Art. 73 reporting deadline (15 days general; 2 days for a widespread
  infringement or a serious/irreversible critical-infrastructure disruption;
  10 days on death), plus a fill-in incident-report template. Maps to NIST CSF
  Respond (RS) and ISO 27001 A.5.24/A.5.26. New section-10 `inc_*` intake fields
  drive it deterministically; they do not affect the risk tier.
- **Model Card generator** (`app/modelcard.py`, `modelcard` report) — a Model Card
  skeleton (Mitchell et al., 2019) pre-filled from the intake, anchored on Art. 13
  transparency, with gaps left as `[to be completed]`.
- **Inventory portfolio roll-up** — new `GET /api/portfolio` (risk-tier
  distribution, obligations coming due by date, Art. 50 disclosure count) and
  extra CSV columns (`obligations_date`, `art50_disclosure`,
  `has_high_risk_obligations`); the web inventory shows the roll-up summary plus
  Due-from / Art. 50 columns. Pure aggregation over stored JSON — no new
  persistence.
- All three report types wired into the CLI (`--type stride|incident|modelcard`),
  the web UI (STRIDE threat model / Serious incident / Model card tabs) and the MCP
  `generate_report`; `security.arch_view` / `security.severity_for` promoted to
  public so the STRIDE lens reuses the same severity engine.
- Tests (`tests/test_stride.py`, `tests/test_incident.py`,
  `tests/test_modelcard.py`, extended `tests/test_api.py`): determinism, the
  free-text invariant, severity-reuse parity with the security lens, the Art. 73
  deadline logic, Model Card pre-fill, and the portfolio/CSV roll-up.

[0.5.0]: https://github.com/JKasteele/ai-act-companion/releases/tag/v0.5.0

## [0.4.0] - 2026-06-15

Completes the Tier 2 purple-team set: pairs the red-team plan with its defensive
counterpart and adds a data-layer security lens.

### Added
- **Defensive control catalogue** (`app/controls.py`, `controls` report + MCP
  `generate_control_catalog`) — the blue-team mirror of the red-team test plan.
  A prioritised, architecture-aware catalogue of the controls to implement per
  in-scope OWASP LLM risk: what to implement, what it prevents, how to verify it,
  the NIST CSF 2.0 / ISO 27001:2022 anchors and the EU AI Act / NIST AI RMF
  references. Each control's priority *is* the architecture-aware severity of the
  risk it mitigates (the same number the red-team plan uses), conditional controls
  are gated on the *same* architecture conditions as the offense, and each control
  names the red-team test case(s) that verify it — *implement, then test*.
- **OWASP GenAI Data Security lens** (`app/data_security.py`, `datasec` report +
  MCP `assess_data_security`) — maps the system to the 21 OWASP GenAI Data
  Security risks (DSGAI01–DSGAI21, from the 2026 v1.0 guidance), the data-layer
  complement to the OWASP LLM Top 10 lens. Relevance is deterministic over the
  `sec_*`/`arch_*`/`data_*` intake; each applicable risk carries its related OWASP
  LLM item(s) and EU AI Act (Art. 10 anchor) / GDPR / NIST AI RMF controls.
- Both report types added to the CLI (`--type controls|datasec`) and the web UI
  (Control catalogue / Data security tabs); `architecture_flags`/`gate_open`
  promoted to public in `redteam.py` so offense and defense share gate semantics.
- Tests (`tests/test_control_catalog.py`, `tests/test_data_security.py`):
  determinism, severity-driven priority, architecture gating, the free-text
  invariant, the offense↔defense cross-link integrity, DSGAI knowledge-base
  fidelity (21 ids), coverage consistency, and rendering.

[0.4.0]: https://github.com/JKasteele/ai-act-companion/releases/tag/v0.4.0

## [0.3.0] - 2026-06-15

Turns the security lens into an actionable, purple-team artifact.

### Added
- **AI red-team test plan** generator (`app/redteam.py`, `redteam` report) — turns
  the architecture-aware security lens into a prioritised, system-specific
  adversarial **test plan** to scope an *authorized* purple-team exercise. Each
  test case carries an objective, the MITRE ATLAS technique(s), preconditions,
  methodology (no exploit payloads), success criteria, expected detection &
  logging, and the EU AI Act / NIST control it validates. A test case's priority
  *is* the architecture-aware severity of its parent OWASP risk, and conditional
  tests are gated on the architecture (e.g. a Critical cross-tenant test only
  when the LLM is the access-control boundary over all-users data).
- New MCP tool `generate_red_team_plan` (structured); `redteam` added to
  `generate_report`, the CLI (`--type redteam`) and the web UI (Red-team plan tab).
- Tests (`tests/test_redteam_plan.py`): determinism, severity-driven priority,
  architecture gating, the free-text invariant (prose cannot add/drop/re-prioritise
  a test), coverage consistency, and rendering.

[0.3.0]: https://github.com/JKasteele/ai-act-companion/releases/tag/v0.3.0

## [0.2.0] - 2026-06-15

Completes the high-risk documentation pack and deepens the security lens.

### Added
- **Annex IV technical-documentation** report (`techdoc`, Art. 11) — the nine
  Annex IV sections as a fill-in skeleton, pre-filled from the intake.
- **Obligations & conformity tracker** report (`compliance`) — every applicable
  obligation as a trackable row (status never inferred), plus a deterministic
  **Art. 99 / 101 penalty-exposure** block keyed to the triggered tier.
- **Architecture-aware severity** for the AI security lens — a new "Security
  architecture" intake section (`arch_*` fields) drives a deterministic severity
  (Critical / High / Medium / Low) per OWASP item, each with a rationale naming
  the deciding architecture field(s). Severity is a pure function of structured
  fields; the red-team suite now proves free-text cannot move it.
- **Post-market monitoring plan** report (`monitoring`, Art. 72) — six monitoring
  categories from NIST AI 800-4 (March 2026), each a fill-in table with seeded
  rows derived from the intake.
- **Framework Integration Matrix** — a new `knowledge/security_frameworks.py`
  (NIST CSF 2.0 functions + ISO/IEC 27001:2022 Annex A control titles + the
  matrix), surfaced both as a section in the security report and as a standalone
  `framework-matrix` report.
- Tests: techdoc/compliance/monitoring/framework-matrix render tests, severity
  golden cases, and two new red-team severity-invariant tests.

[0.2.0]: https://github.com/JKasteele/ai-act-companion/releases/tag/v0.2.0

## [0.1.0] - 2026-06-14

First public release.

### Added
- Rule-based, explainable **EU AI Act** risk classifier (prohibited / high /
  limited / minimal) with cited articles and annexes, the Art. 6(3) derogation
  nuance, and the Art. 2 scope check.
- Document generators: AI risk assessment, **DPIA** skeleton (GDPR Art. 35),
  bias-audit checklist, **AI security assessment**, and **FRIA** (Art. 27) —
  Markdown + browser print-to-PDF.
- Framework crosswalks: **NIST AI RMF**, **ISO/IEC 42001** (category level), and
  an **AI security lens** mapping findings to the **OWASP Top 10 for LLM
  Applications (2025)** and **MITRE ATLAS**.
- Phased applicability timeline (Art. 113) and EUR-Lex / AI Act Explorer deep links.
- Optional, human-in-the-loop **AI layer** (local Ollama or paste-into-your-own-LLM).
- **Claude Code plugin**: MCP server + assessment skill + `ai-act` CLI.
- **AI system inventory** dashboard with CSV register and JSON export/import, plus
  a loadable example per risk tier.
- Tooling: unit tests including a 25-case golden-set accuracy evaluation and an
  adversarial red-team suite; `ruff`, `mypy`, `bandit` and `pip-audit` in CI;
  Dockerfile; `THREAT_MODEL.md` and `DESIGN.md`.

[0.1.0]: https://github.com/JKasteele/ai-act-companion/releases/tag/v0.1.0
