# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A local-first, **deterministic** EU AI Act risk classifier + document generator,
crosswalked to NIST AI RMF / ISO 42001 and an OWASP-LLM/MITRE-ATLAS security
lens. One engine drives three front-ends: the FastAPI web app, the MCP server
(Claude Code plugin), and the `ai-act` CLI. Python backend, vanilla JS frontend
(no build step), JSON-file storage.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev,mcp]"

# Run the web app
uvicorn app.main:app --reload                         # http://127.0.0.1:8000

# Tests / lint / types (what CI runs)
pytest                                                # all tests; addopts = -q
pytest tests/test_classifier.py                       # one file
pytest tests/test_accuracy.py -k high_risk            # one case by name
ruff check .                                           # lint (line-length 100, E/F/I/B/UP)
mypy app                                               # types (non-blocking in CI)
bandit -r app mcp_server.py -ll                        # SAST (blocking in CI)

# CLI over the same engine
ai-act questionnaire
ai-act classify --answers examples/hiring_cv_screening.json
ai-act report --answers a.json --type dpia --out dpia.md
ai-act scan .                                          # repo AI-usage relevance scan
```

The MCP server runs `python mcp_server.py` (registered via `.mcp.json`); the
`python` on PATH must have `.[mcp]` installed.

## The one architectural invariant

**A deterministic engine decides the risk tier; the LLM is only an interface and
narrative author; human-in-the-loop review is mandatory.** Everything else
follows from this. Concretely:

- The AI layer (`app/llm/`) and Claude (via MCP) may **only** pre-fill answers
  and draft prose. They must **never** set or influence the risk tier, and
  nothing is classified/stored without explicit human confirmation.
- The risk tier and all citations come **only** from `classifier.py` /
  `security.py`. Severity and tier are pure functions of structured field ids
  and option values — crafted free-text must not be able to move them. The
  red-team suite (`tests/test_red_team.py`) enforces this; keep it passing.

## Architecture

`questionnaire.py` is the **single source of truth** — it defines every intake
field id and its options. All three front-ends and the whole engine are bound to
those ids. Change a field id and you must update the rules and reports that key
off it.

The engine is pure functions, no I/O, fully testable:
- `classifier.classify(answers) -> dict` — EU AI Act decision. Highest severity
  wins: Art. 5 (prohibited) → Art. 6 (high) → Art. 50 (limited) → minimal; GPAI
  (Chapter V) tracked independently. Does an Art. 2 applicability check first.
  Every finding carries `refs` (articles/annexes) and `source_questions` (the
  field ids that fired the rule).
- `security.assess_security(answers) -> dict` — OWASP LLM Top 10 + MITRE ATLAS
  lens over the `sec_*` fields, with deterministic **architecture-aware
  severity** computed from the `arch_*` fields. `redteam.py`, `controls.py`,
  `stride.py`, and `data_security.py` reuse this same severity so the offense
  (red-team), defense (controls), and threat-model views agree by construction.
- `reports.render(report_type, assessment) -> (type, filename, markdown)` —
  renders one of fifteen Markdown artifacts: `risk`, `dpia`, `bias`, `security`,
  `fria`, `techdoc`, `compliance`, `monitoring`, `framework-matrix`, `redteam`,
  `controls`, `datasec`, `stride`, `incident`, `modelcard`. Markdown is the
  canonical export; PDF is browser print-to-PDF (no dependency).

`app/knowledge/` holds the frameworks **encoded as cited data** (eu_ai_act,
nist_rmf, ai_security, iso_42001, red_team, controls, data_security, monitoring,
security_frameworks, stride) — the classifier reads from here rather than
hard-coding article text.

Adding a new report type means: a generator module (e.g. `app/foo.py`), a branch
in `reports.render`, a `--type foo` in the CLI, an `/api/.../report?type=foo`
path, a frontend tab in `static/`, and usually a knowledge module + MCP tool.

## Working in this codebase (project conventions)

- **Changing classification logic** → add or adjust a labelled case in
  `examples/golden_set.json`, labelling the expected tier by reasoning from the
  regulation, **not** by running the classifier. `tests/test_accuracy.py` runs
  the 25-case golden set and expects 100%.
- **Knowledge base honesty** → cite a source for any article/standard reference.
  Where a cross-framework mapping is the project's own analytical alignment and
  not an official published crosswalk, it must say so — in the code/data **and**
  in the generated output. (Existing strings already do this; match them.)
- **Scope guard** → this is a structured *self-assessment aid, not legal advice*.
  Do not add features that present output as a definitive legal determination, or
  that let the AI layer decide a tier.
- Use synthetic / generic example data only; `data/` (saved assessments) is
  gitignored.
