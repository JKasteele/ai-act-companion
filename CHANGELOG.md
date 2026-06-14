# Changelog

All notable changes are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/); the project uses
[semantic versioning](https://semver.org/).

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
