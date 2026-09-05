# Contributing

Thanks for your interest! This is a personal portfolio project, but issues and
pull requests are welcome.

## Development setup

- Python 3.10+
- `python -m venv .venv` then `pip install -e ".[dev,mcp]"`
- Run the app: `uvicorn app.main:app --reload` → http://127.0.0.1:8000

## Before opening a PR

- Follow the shared instructions in [AGENTS.md](AGENTS.md).
- For workspace changes, run `node --test tests/frontend/*.test.mjs` and
  `npm ci`, `python scripts/build_workspace.py`, and `npm run test:engine`.
  Generated case assets must match their sources; browser and native engines must agree.

- `ruff check .` is clean.
- `pytest` passes — including the golden-set accuracy eval
  (`tests/test_accuracy.py`) and the red-team suite (`tests/test_red_team.py`).
- If you change classification logic, add or adjust a labelled case in
  `examples/golden_set.json` (label the expected tier by reasoning from the
  regulation, not by running the classifier).
- Keep the knowledge base honest: cite a source for any article/standard
  reference, and label cross-framework mappings as *analytical alignments* where
  they are not official crosswalks.

## Scope

This is a structured **self-assessment aid, not legal advice**. Please don't add
features that present the output as a definitive legal determination, or that
let the AI layer decide a risk tier (the deterministic engine is the ground
truth — see [DESIGN.md](docs/DESIGN.md)).

## Security

See [SECURITY.md](SECURITY.md) to report a vulnerability, and
[THREAT_MODEL.md](docs/THREAT_MODEL.md) for the tool's own threat model.
