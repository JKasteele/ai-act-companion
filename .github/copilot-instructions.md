# GitHub Copilot instructions — AI Act Companion

Custom instructions for GitHub Copilot (coding agent, Cowork, VS Code agent mode,
and CLI). This is the Copilot counterpart of `CLAUDE.md` and `DESIGN.md` — read
those for the full rationale; this file is the short, binding version.

## What this is

A local-first, **deterministic** EU AI Act risk classifier + document generator,
crosswalked to NIST AI RMF / ISO 42001 and an OWASP-LLM / MITRE-ATLAS security
lens. One engine drives three front-ends: the FastAPI web app, an **MCP server**
(`mcp_server.py`), and the `ai-act` CLI. Python backend, vanilla JS frontend (no
build step), JSON-file storage.

## The one architectural invariant — do not break it

**A deterministic engine decides the risk tier; the AI is only an interface and
narrative author; human-in-the-loop review is mandatory.**

- The risk tier (`prohibited` / `high` / `limited` / `minimal`) and every cited
  Article/Annex come **only** from `app/classifier.py` (and the security findings
  from `app/security.py`). Never infer, soften, or override them in prose, code,
  or a generated report.
- Tier and severity are **pure functions of structured field ids + option
  values** — crafted free-text must never move them. `tests/test_red_team.py`
  enforces this; keep it passing.
- When using the MCP tools (below), never call `save_assessment` or present a
  report as final until the user has explicitly reviewed and confirmed. All AI
  output is a draft.

## Using the engine via MCP

The `ai-act-companion` MCP server exposes the engine as tools:
`get_questionnaire`, `classify_ai_system`, `classify_ai_security`,
`generate_red_team_plan`, `generate_control_catalog`, `assess_data_security`,
`generate_report`, `save_assessment`, `list_assessments`, `get_assessment`.

Assessment flow: `get_questionnaire` → collect/confirm answers →
`classify_ai_system` (present tier + refs verbatim) → `generate_report`
(`report_type` ∈ `risk`, `dpia`, `bias`, `security`, `fria`, `techdoc`,
`compliance`, `monitoring`, `framework-matrix`, `redteam`, `controls`, `datasec`,
`stride`, `incident`, `modelcard`) → confirm → `save_assessment`. See
`.github/prompts/ai-act-assessment.prompt.md` for the full playbook, and
`docs/COPILOT.md` to wire the MCP server into Copilot.

## Commands

```bash
pip install -e ".[dev,mcp]"             # setup (cloud agent: see copilot-setup-steps.yml)
uvicorn app.main:app --reload           # web app at http://127.0.0.1:8000
pytest                                  # all tests (CI gate)
pytest tests/test_classifier.py         # one file
pytest tests/test_accuracy.py -k high   # one case by name
ruff check .                            # lint (line-length 100, E/F/I/B/UP)
bandit -r app mcp_server.py -ll         # SAST (CI gate)
ai-act classify --answers examples/hiring_cv_screening.json   # CLI over the engine
```

## Architecture

`app/questionnaire.py` is the **single source of truth** — it defines every
intake field id and its options; all front-ends and rules key off those ids.

- `classifier.classify(answers) -> dict` — EU AI Act decision. Highest severity
  wins: Art. 5 → Art. 6 → Art. 50 → minimal; GPAI tracked independently; Art. 2
  applicability checked first. Findings carry `refs` and `source_questions`.
- `security.assess_security(answers) -> dict` — OWASP LLM Top 10 + MITRE ATLAS
  over `sec_*` fields, with architecture-aware severity from `arch_*` fields.
  `redteam.py`, `controls.py`, `stride.py`, `data_security.py` reuse that same
  severity so offense/defense/threat-model views agree by construction.
- `reports.render(report_type, assessment) -> (type, filename, markdown)` —
  fifteen Markdown artifacts. Markdown is canonical; PDF is browser print-to-PDF.
- `app/knowledge/` holds the frameworks as **cited data** (eu_ai_act, nist_rmf,
  ai_security, iso_42001, red_team, controls, data_security, monitoring,
  security_frameworks, stride) — read from here, don't hard-code article text.

Adding a report type touches: a generator module, a branch in `reports.render`, a
`--type` in the CLI, an `/api/.../report?type=` path, a frontend tab in `static/`,
and usually a knowledge module + an MCP tool.

## Project conventions

- **Changing classification logic** → add/adjust a labelled case in
  `examples/golden_set.json`, labelling the expected tier by reasoning from the
  regulation, **not** by running the classifier. `tests/test_accuracy.py` runs
  the 25-case golden set at 100%.
- **Knowledge honesty** → cite a source for any article/standard reference; where
  a cross-framework mapping is the project's own analytical alignment and not an
  official crosswalk, say so in the code/data **and** the output. Match existing
  strings.
- **Scope guard** → this is a structured *self-assessment aid, not legal advice*.
  Never present output as a definitive legal determination, and never let the AI
  layer decide a tier.
- Use synthetic / generic example data only; `data/` is gitignored.
