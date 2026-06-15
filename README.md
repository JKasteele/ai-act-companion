# AI Act Companion

> Local-first, explainable **EU AI Act** risk classifier + **AI risk assessment / DPIA / bias-audit** generator, mapped to the **NIST AI Risk Management Framework** — with an optional, human-in-the-loop AI assistant.

[![CI](https://github.com/JKasteele/ai-act-companion/actions/workflows/ci.yml/badge.svg)](https://github.com/JKasteele/ai-act-companion/actions/workflows/ci.yml)
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

![AI Act Companion — load an example, classify, and review the result, security lens and report](docs/img/demo.gif)

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
- **A security lens, not just compliance.** Maps the system to the **OWASP Top
  10 for LLM Applications (2025)** and **MITRE ATLAS**, linked to EU AI Act
  Art. 15 and NIST AI RMF — the governance × security intersection that
  otherwise lives only in commercial tools. See [AI security lens](#ai-security-lens).

## Two ways to use it

One deterministic engine (the audited rule classifier + report generators) sits
underneath two interchangeable front-ends — pick whichever fits your workflow:

```mermaid
flowchart TB
    A["🔒 Local web app<br/>(privacy-first)"]
    B["⚡ Claude Code plugin<br/>(MCP)"]
    E["<b>Deterministic engine</b><br/>classifier · reports · knowledge<br/>= ground truth"]
    O["Risk tier + cited articles<br/>risk · DPIA · bias · security · FRIA<br/>techdoc · compliance · monitoring · framework-matrix"]
    A -->|"optional local AI:<br/>Ollama or paste-into-your-own-LLM"| E
    B -->|"Claude is the interface<br/>& narrative author"| E
    E --> O
```

| | 🔒 Local web app | ⚡ Claude Code plugin |
|---|---|---|
| **Interface** | Browser UI on your machine | Claude Code (chat) |
| **AI assist** | Local Ollama, or paste-into-your-own-LLM | Claude Code itself, via MCP tools |
| **Privacy** | Fully local — data never leaves your device | Uses your existing Claude Code session |
| **Best for** | Privacy-sensitive / offline / no subscription | If you already live in Claude Code |
| **Set-up** | [Quickstart](#quickstart) | [Use inside Claude Code](#use-inside-claude-code) |

Either way, the **risk tier and citations come only from the deterministic
engine** — the AI never decides the outcome, and a human-in-the-loop review is
required. The engine can also be driven headless via the [CLI](#cli).

## Screenshots

| Classification result | AI security lens | Generated report |
|---|---|---|
| ![Classification](docs/img/result.png) | ![Security lens](docs/img/security.png) | ![Report](docs/img/report.png) |

| AI assist (human-in-the-loop) | AI system inventory |
|---|---|
| ![AI assist](docs/img/ai-assist.png) | ![Inventory](docs/img/inventory.png) |

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
   - AI security assessment (OWASP LLM Top 10 + MITRE ATLAS, with
     architecture-aware severity and a NIST CSF 2.0 / ISO 27001 matrix)
   - FRIA skeleton (fundamental rights impact assessment, Art. 27)
   - Annex IV technical documentation skeleton (Art. 11)
   - obligations & conformity tracker with the Art. 99 penalty exposure
   - post-market monitoring plan (Art. 72)
   - framework integration matrix (NIST CSF 2.0 / ISO 27001:2022)
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
/plugin marketplace add JKasteele/ai-act-companion
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

## Tests & validation

```bash
pytest                              # or: python tests/test_classifier.py
ruff check .                        # lint
```

The suite includes a **25-case golden-set accuracy evaluation**
(`tests/test_accuracy.py` against `examples/golden_set.json`, 100% — expected
tiers labelled by independent regulatory reasoning) and an **adversarial
red-team suite** (`tests/test_red_team.py`) that proves prompt-injection /
jailbreak input cannot move the deterministic risk tier.

See **[DESIGN.md](DESIGN.md)** for the architecture and the design rationale
(the deterministic-engine + LLM-interface + human-in-the-loop safety pattern).

## Project structure

```
ai-act-companion/
├── app/
│   ├── main.py            FastAPI app + endpoints
│   ├── cli.py             scriptable CLI over the engine
│   ├── questionnaire.py   intake definition (single source of truth)
│   ├── classifier.py      rule-based EU AI Act classifier
│   ├── reports.py         report generators (risk/DPIA/bias/security/FRIA/techdoc/compliance/monitoring/framework-matrix)
│   ├── security.py        AI security lens + architecture-aware severity
│   ├── storage.py         JSON persistence
│   ├── models.py          pydantic models
│   ├── knowledge/         EU AI Act, NIST AI RMF, ISO 42001, AI security, monitoring, CSF/ISO 27001 as data
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
| GET | `/api/assessments` | list stored assessments (inventory) |
| GET | `/api/assessments/{id}` | full assessment (JSON export) |
| DELETE | `/api/assessments/{id}` | delete an assessment |
| GET | `/api/export.csv` | inventory as a CSV register |
| GET | `/api/assessments/{id}/report?type=risk\|dpia\|bias\|security\|fria\|techdoc\|compliance\|monitoring\|framework-matrix` | report (markdown) |
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

## AI security lens

Governance and security are complementary, but free tools rarely connect them.
AI Act Companion adds a **security lens**: from the system's answers it derives
the applicable **OWASP Top 10 for LLM Applications (2025)** items and, for each,
the relevant **MITRE ATLAS** technique(s), the EU AI Act control (chiefly
Art. 15 — whose para. 5 explicitly names data/model poisoning, adversarial
examples, model evasion and confidentiality attacks), the NIST AI RMF
subcategory (anchored on **MEASURE 2.7**), and a mitigation.

It surfaces in the result view, as a `security` report
(`ai-act report --type security`), and via the `classify_ai_security` MCP tool.
The lens adapts: a non-generative ML system still maps to disclosure, poisoning
and supply-chain items, while an exposed LLM additionally maps to prompt
injection, system-prompt leakage and misinformation.

**Architecture-aware severity.** Each applicable item gets a deterministic
severity (Critical / High / Medium / Low) computed from a small set of
structured architecture-context fields — e.g. *prompt injection is Critical here
because the LLM is the only access-control boundary and the API is read-write* —
with a one-line rationale naming the deciding field(s). Severity is a pure
function of those fields, so crafted free-text cannot move it (covered by the
red-team suite).

**Framework bridge.** The security report (and a standalone `framework-matrix`
report) carries a **Framework Integration Matrix** that aligns the findings to
**NIST CSF 2.0** and **ISO/IEC 27001:2022** (public control titles only) — the
frameworks security reviewers and ISMS auditors actually use.

> Identifiers are verified against genai.owasp.org and the MITRE ATLAS data; the
> cross-mappings are a **Companion-derived analytical alignment** traceable to
> those identifiers, not an official published crosswalk.

The tool also has its own [THREAT_MODEL.md](THREAT_MODEL.md) — including the
OWASP LLM Top 10 applied to its *own* AI layer — and a
[SECURITY.md](SECURITY.md) policy; `bandit` and `pip-audit` run in CI.

## Legal grounding

References are modelled as data in `app/knowledge/`. The classifier cites the
concrete article/annex per conclusion:

- **Art. 5** — prohibited practices
- **Art. 6 + Annex I/III** — high-risk (incl. the Art. 6(3) derogation)
- **Art. 50** — transparency obligations
- **Chapter V (Art. 51–55)** — general-purpose AI (GPAI)
- **Art. 11 + Annex IV** — technical documentation
- **Art. 72** — post-market monitoring
- **Art. 99 / 101** — administrative fines (penalty-exposure block)
- **NIST AI RMF 1.0** — GOVERN / MAP / MEASURE / MANAGE crosswalk
- **ISO/IEC 42001:2023** — AI management system crosswalk (analytical alignment)
- **NIST CSF 2.0 + ISO/IEC 27001:2022** — security-framework integration matrix (analytical alignment)

## Roadmap

- [x] Rule-based, cited EU AI Act classifier (prohibited / high / limited / minimal)
- [x] Risk assessment + DPIA skeleton + bias-audit checklist, mapped to NIST AI RMF
- [x] Optional AI layer (Ollama + manual-prompt provider) with mandatory human-in-the-loop
- [x] Unit tests + CI + Docker
- [x] **Claude Code plugin** — MCP server + skill + CLI (Claude as interface, engine as ground truth)
- [x] **AI security lens** — findings mapped to OWASP LLM Top 10 (2025) + MITRE ATLAS
- [x] Threat model of the tool itself (`THREAT_MODEL.md`) + `bandit`/`pip-audit` in CI
- [x] EUR-Lex / AI Act Explorer deep links + phased applicability timeline (Art. 113)
- [x] Fundamental Rights Impact Assessment (FRIA, Art. 27) generator
- [x] AI system inventory (dashboard) + CSV register and JSON export/import
- [x] ISO/IEC 42001 crosswalk (in the risk assessment report)
- [x] Annex IV technical-documentation generator (Art. 11)
- [x] Obligations & conformity tracker with Art. 99 penalty exposure
- [x] **Architecture-aware severity** for the AI security lens (Critical/High/Medium/Low)
- [x] Post-market monitoring plan (Art. 72), structured on NIST AI 800-4
- [x] **NIST CSF 2.0 + ISO/IEC 27001:2022** framework integration matrix

## License

MIT — see [LICENSE](LICENSE).
