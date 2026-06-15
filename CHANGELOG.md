# Changelog

All notable changes are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/); the project uses
[semantic versioning](https://semver.org/).

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
