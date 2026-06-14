# AI Act Companion

> Local-first, explainable **EU AI Act** risk classifier + **AI risk assessment / DPIA / bias-audit** generator, mapped to the **NIST AI Risk Management Framework** — with an optional, human-in-the-loop AI assistant.

[![CI](https://github.com/USERNAME/ai-act-companion/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/ai-act-companion/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](https://github.com/astral-sh/ruff)

AI Act Companion helps you run a structured AI risk assessment for an AI system,
aligned with the **EU AI Act** (Regulation (EU) 2024/1689) and the **NIST AI
RMF**, and generates the accompanying documentation. It runs entirely on your
own machine.

> ⚠️ **Not legal advice.** This is an aid for a structured self-assessment. It
> does not replace an assessment by a qualified lawyer or the competent
> supervisory authority. Use synthetic / generic example data only.

---

## Why this one?

Most open EU AI Act repos are either static checklists or heavyweight platforms.
This project focuses on three things that are uncommon in free tooling:

- **Explainable & cited.** Every verdict tells you *which* Article/Annex drove it
  and *why* — a traceable, deterministic rule engine, not a black box.
- **Tested.** The classifier ships with a unit-test suite (golden cases per risk
  tier), so the compliance logic is *validated, not vibes*.
- **Local & private, with honest AI.** Optional AI assist runs locally (Ollama)
  or via a paste-into-your-own-LLM flow — and **never** decides for you: a
  human-in-the-loop review is mandatory by design (EU AI Act Art. 14 in spirit).
- **Claude-native.** Ships as a **Claude Code plugin**: an MCP server exposes
  the deterministic engine as tools, and a skill orchestrates a full
  human-in-the-loop assessment. Claude becomes the interface; the audited rule
  engine stays the ground truth. See [Use inside Claude Code](#use-inside-claude-code).

> **On the roadmap (next milestone):** an **AI security lens** that maps each
> result to the **OWASP LLM Top 10** and **MITRE ATLAS** alongside NIST AI RMF —
> the governance × security intersection that today only exists in commercial
> tools. See [Roadmap](#roadmap).

## Screenshots

| Classification result | Generated report | AI assist (human-in-the-loop) |
|---|---|---|
| ![Classification](docs/img/result.png) | ![Report](docs/img/report.png) | ![AI assist](docs/img/ai-assist.png) |

## What it does

1. **Intake questionnaire** describing an AI system (purpose, domain, users,
   data, autonomy, and screening questions for Art. 5/6/50 and GPAI).
2. **Rule-based EU AI Act classifier** that deterministically maps the answers to
   a risk tier — **prohibited / high / limited / minimal** — with the reasoning
   and the relevant articles/annexes, including the Art. 6(3) derogation nuance.
3. **Document generation** from the result:
   - AI risk assessment report
   - DPIA skeleton (GDPR Art. 35, linked to the AI Act)
   - bias audit checklist
   all mapped to EU AI Act + NIST AI RMF, exportable to **Markdown** and **PDF**
   (via browser print-to-PDF).
4. **Optional AI layer** (human-in-the-loop): turn a free-text system description
   into draft answers and draft narrative sections — output is always a draft you
   review; it is never classified, submitted or stored automatically.

## Stack

- **Backend:** Python + FastAPI (rule-based core, no AI required)
- **Frontend:** vanilla HTML/CSS/JS (no build step)
- **Storage:** JSON files in `data/`
- **PDF:** browser print-to-PDF (zero dependencies)

## Quickstart

```bash
# 1. Virtual environment + dependencies
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"            # or: pip install -r requirements.txt

# 2. Run the server
uvicorn app.main:app --reload

# 3. Open http://127.0.0.1:8000
```

Click **"Load example"** for a synthetic high-risk example, or load one of the
files in `examples/`.

### Docker

```bash
docker build -t ai-act-companion .
docker run --rm -p 8000:8000 -v "$PWD/data:/app/data" ai-act-companion
```

## Use inside Claude Code

AI Act Companion is also a **Claude Code plugin**. An MCP server
(`mcp_server.py`) exposes the deterministic engine as tools
(`classify_ai_system`, `generate_report`, `get_questionnaire`, …), and the
`ai-act-assessment` skill drives a full, human-in-the-loop assessment — Claude
runs the intake and writes the narrative, but the **risk tier and citations come
only from the engine**, and nothing is saved without your confirmation.

```bash
pip install -e ".[mcp]"            # install the MCP dependency
```

**Option A — just open the repo.** The project-scoped `.mcp.json` registers the
server automatically; approve it when Claude Code prompts, then ask:
*"Run an EU AI Act assessment for my CV-screening system."*

**Option B — install as a plugin** (works in any project):

```text
/plugin marketplace add USERNAME/ai-act-companion
/plugin install ai-act-companion@ai-act-companion
```

Then invoke the skill with `/ai-act-companion:ai-act-assessment` or just
describe a system and let Claude pick it up.

> The MCP server runs `python mcp_server.py`; make sure the `python` on your
> PATH has the dependencies installed (`pip install -e ".[mcp]"`).

## CLI

A scriptable entry point over the same engine (used by the MCP server and handy
on its own):

```bash
ai-act questionnaire                                   # print the intake schema
ai-act classify --answers examples/hiring_cv_screening.json
cat answers.json | ai-act classify --answers -         # read from stdin
ai-act classify --answers a.json --save                # persist + print id
ai-act report --answers a.json --type dpia --out dpia.md
ai-act list
```

(`ai-act` is installed via `pip install -e .`; or run `python -m app.cli …`.)

## Tests

```bash
pytest                              # or: python tests/test_classifier.py
ruff check .                        # lint
```

## Project structure

```
ai-act-companion/
├── app/
│   ├── main.py            FastAPI app + endpoints
│   ├── cli.py             scriptable CLI over the engine
│   ├── questionnaire.py   intake definition (single source of truth)
│   ├── classifier.py      rule-based EU AI Act classifier
│   ├── reports.py         risk assessment / DPIA / bias generators
│   ├── storage.py         JSON persistence
│   ├── models.py          pydantic models
│   ├── knowledge/         EU AI Act + NIST AI RMF as data
│   └── llm/               optional local/manual AI assist (web app)
├── mcp_server.py          MCP server (Claude Code tools over the engine)
├── skills/                Claude Code skill (ai-act-assessment playbook)
├── .claude-plugin/        plugin.json + marketplace.json
├── .mcp.json              project-scoped MCP registration
├── static/                frontend (index.html, app.js, style.css, print.css)
├── examples/              synthetic example assessments
├── data/                  saved assessments (JSON, gitignored)
└── tests/                 classifier tests
```

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/questionnaire` | questionnaire definition |
| POST | `/api/assess` | classify + store |
| GET | `/api/assessments` | list stored assessments |
| GET | `/api/assessments/{id}` | full assessment |
| GET | `/api/assessments/{id}/report?type=risk\|dpia\|bias` | report (markdown) |
| GET | `/api/ai/status` | AI layer status (provider, model, reachability) |
| POST | `/api/ai/prefill` | free text → draft answers (or a prompt for manual mode) |
| POST | `/api/ai/parse` | pasted-back LLM answer → validated draft |
| POST | `/api/ai/narrative` | draft text for a single narrative field |

## AI layer (optional)

The AI layer is **optional** and **provider-pluggable** (`app/llm/`). Configure
via `.env` (see `.env.example`):

| `LLM_PROVIDER` | Behaviour |
|---|---|
| `ollama` *(default)* | Local model via Ollama. Private, free. |
| `manual` | The app generates a prompt you paste into your **own** LLM session (e.g. Claude); you paste the JSON answer back. No API key needed. |
| `none` | AI layer off (rule-based only). |

**Hard guarantee (human-in-the-loop):** all AI output is a *draft*. It only
pre-fills the questionnaire and is never classified, submitted or stored
automatically. Answers are validated against the schema — unknown fields and
invalid options are visibly ignored.

> **Note (local model & GPU):** `qwen3:32b` gives the best quality but needs
> ~20 GB VRAM. If other GPU work runs at the same time, the model may offload to
> CPU and become slow — pick a lighter model (`OLLAMA_MODEL=qwen3:1.7b`) or use
> the `manual` provider. The frontend has a timeout and degrades to a clear
> error message.

## Legal grounding

References are modelled as data in `app/knowledge/`. The classifier cites the
concrete article/annex per conclusion:

- **Art. 5** — prohibited practices
- **Art. 6 + Annex I/III** — high-risk (incl. the Art. 6(3) derogation)
- **Art. 50** — transparency obligations
- **Chapter V (Art. 51–55)** — general-purpose AI (GPAI)
- **NIST AI RMF 1.0** — GOVERN / MAP / MEASURE / MANAGE crosswalk

## Roadmap

- [x] Rule-based, cited EU AI Act classifier (prohibited / high / limited / minimal)
- [x] Risk assessment + DPIA skeleton + bias-audit checklist, mapped to NIST AI RMF
- [x] Optional AI layer (Ollama + manual-prompt provider) with mandatory human-in-the-loop
- [x] Unit tests + CI + Docker
- [x] **Claude Code plugin** — MCP server + skill + CLI (Claude as interface, engine as ground truth)
- [ ] **AI security lens** — map findings to OWASP LLM Top 10 + MITRE ATLAS
- [ ] Threat model of the tool itself (`THREAT_MODEL.md`) + `pip-audit`/`bandit` in CI
- [ ] Article text + EUR-Lex deep links + phased applicability timeline
- [ ] Fundamental Rights Impact Assessment (FRIA, Art. 27) generator
- [ ] ISO/IEC 42001 mapping

## License

MIT — see [LICENSE](LICENSE).
