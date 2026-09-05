# AI Act Companion

**An evidence-led workspace for AI governance and security.**

Investigate a fictional health insurer's AI assistant: compare documents, clarify
unknowns, prepare follow-up actions, and export a review record. The existing EU
AI Act classifier and security toolkit provide a reproducible assessment foundation.

Built by Jesse van de Kasteele as a portfolio project connecting AI governance,
data governance, security engineering, and practical agent design.

## Explore the case

Meridian Health wants to expand a member-service assistant. Its business proposal
says health data never reaches the model; its architecture describes sending
claim details. Proposed write access lacks demonstrated approval enforcement.

1. Compare conflicting passages and inspect their source documents.
2. Record a clarification without treating an assumption as verified evidence.
3. Assign an owner and completion-evidence requirement to each action.
4. Inspect the rule engine's result for the synthetic read-only pilot.
5. Export the evidence, findings, actions, and review history as a Markdown draft.

**Guided mode is a labelled, authored walkthrough, not live AI.** The local app
also supports optional live model investigation through read-only evidence tools
using the existing Ollama or Anthropic provider. Live responses are drafts; they
cannot change the risk tier, close findings, or approve launch.

## Run locally

Requires Python 3.10+. No frontend package installation is needed.

```bash
python -m venv .venv
# Activate: .venv\Scripts\Activate.ps1 (Windows)
#       or source .venv/bin/activate (macOS/Linux)
pip install -e ".[dev,mcp]"
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000** for the evidence workspace. The original intake,
inventory, and report toolkit remains at **http://127.0.0.1:8000/classic**.
On Windows, `scripts/serve-local.ps1` starts a loopback-only server from any directory.

The guided case requires no API key. To use live AI, configure an existing
provider in `.env` using [.env.example](.env.example), then explicitly select
**Live AI** in the workspace. Hosted requests can incur provider charges.

## Repository map

| Location | Responsibility |
| --- | --- |
| `static/workspace/` | Evidence UI, guided walkthrough, local review state, draft export |
| `app/workspace/` | Curated evidence, validated state, bounded live agent tools |
| `app/` and `app/knowledge/` | Rule engine, governance/security lenses, reports |
| `static/` | Original questionnaire and report interface |
| `mcp_server.py` and `skills/` | Agent access to the existing toolkit through MCP |
| `examples/` and `tests/` | Synthetic assessments and regression/evaluation cases |
| `docs/` | Architecture, reference, deployment, and generated reports |
| `scripts/` | Portable launcher and reproducible demo builds |

## Development checks

```bash
ruff check .
mypy app mcp_server.py
pytest
node --test tests/frontend/*.test.mjs
python scripts/build_workspace.py
```

The static build is a guided preview with an engine result computed at build time.
It does not run Python or a live model in the browser. Review state is stored on
the visitor's device; this is not a shared case-management service.

## Documentation

- [Documentation index](docs/README.md)
- [Workspace architecture and limitations](docs/WORKSPACE.md)
- [Existing toolkit reference](docs/TOOLKIT.md)
- [Engine design](docs/DESIGN.md)
- [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md)

All case materials are synthetic. This is a self-assessment aid, not legal advice
or automated compliance certification. [MIT licensed](LICENSE).
