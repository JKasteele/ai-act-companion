# Changelog

All notable changes are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/); the project uses
[semantic versioning](https://semver.org/).

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
