# System workspace

The primary interface is an inventory of AI systems. Each system has Overview,
Assessment, Evidence, Findings, Documents, and Activity views. The insurer case
remains an optional introduction at `case.html` with its separate review state.

## Data and assessment boundaries

The intake renders every field in all 13 sections from `app/questionnaire.py`.
Draft answers autosave in a versioned browser inventory; changes invalidate the
previous assessment. Unknown boolean answers remain absent rather than becoming
false. `app/workspace/toolkit.py` validates types, choices, sizes, and table cells,
then requires baseline and applicable conditional screening before custom
classification or report generation. It calls the existing classifier, security,
governance, and report modules. It does not change their legal rules.

Nine shipped examples can be explored as labelled reference snapshots. Example
reports select allowlisted files by ID and ignore caller-supplied overrides.
Copying or importing a reference creates a draft requiring complete screening.
The original API, CLI, MCP, and `/classic` retain their existing contracts and
legacy completeness behavior; the new workspace gate does not rewrite them.

Browser drafts include evidence notes and a bounded activity history. JSON export
preserves these alongside answers; import deliberately discards any supplied
classification and identity. CSV exports cover the inventory. Local API records
appear separately as read-only saved assessments; copy one to edit a browser draft.
There is no shared database, cross-device sync, or automatic saving to the legacy
assessment store. Clearing browser data removes drafts; export keeps a portable copy.

## Documents

All 21 report types use `app/reports.py`, including governance, security, DPIA,
FRIA, controls, red-team plans, data governance, and forensic readiness. Outputs
are drafts for human review. The UI offers escaped Markdown previews, Markdown
downloads and browser print/PDF. Dutch output uses the original engine's language
support, which includes Dutch summaries rather than a full translation of every
report. Evidence notes stay separate; they are not silently inserted into engine
answers or presented as verified controls.

## Companion and the guided case

Workflow guidance routes a small set of intents to the selected system's tools.
It is labelled as guidance without a live model. It does not extract structured
answers from descriptions, discover contradictions, or perform autonomous writes.

Live AI is opt-in in the local FastAPI app through the existing Ollama or Anthropic
provider. `/api/workspace/system-chat` supplies only the selected system profile
and its evidence catalogue. The bounded tools are `read_evidence(source_id)` and
`inspect_review()`: at most four tool calls and five model calls per request.
Citation IDs must resolve to sources actually read. Unknown tools, unread sources,
invalid responses, provider errors, and tool exhaustion explicitly stop the request.
No tool can change answers, decide a risk tier, verify a control, or approve launch.
The structured assessment is computed for chat only when the user has already
requested classification; incomplete profiles still return no classification.

The original guided insurer case uses authored documents and three authored
findings in `app/workspace/case.py`. Guided explanations are never presented as
AI discoveries. Reviewer statements and action completion references cannot close
findings or grant approval. The case's `/chat`, `/review`, and `/assess` endpoints
remain compatible and isolated from general system evidence.

The existing spend guard runs before every live model call; client cooldown/caps
apply once per request. This is best-effort local accounting, not an atomic
multi-worker reservation. Cancellation can leave a provider call running until
its timeout. The model sees the current question and structured state, not durable
conversation history. Citation validation establishes source access, not semantic
entailment. Mock-provider tests check orchestration, not live reasoning quality.

## Native and browser execution

FastAPI serves the workspace and calls the shared dispatcher directly. No Node
installation is needed to run this local path. For static hosting:

```bash
npm ci
python scripts/build_workspace.py
npm run test:engine
```

The build copies a public frontend allowlist and packages only the pure Python
engine, knowledge modules, toolkit bridge, and synthetic examples into `engine.zip`.
It bundles the pinned Pyodide runtime locally; a module worker loads it on first
assessment/report request. No external runtime CDN, model, storage module, provider
module, API routes, secrets, or saved user records enter the bundle. The main UI
stays responsive while the worker executes. Errors are explicit and retryable.
The static host uses no Python server and offers no live AI. The legacy insurer
case result remains an explicitly labelled build-time snapshot.

`scripts/test_browser_engine.mjs` executes the shipped WebAssembly runtime in Node,
compares its nine-system catalogue against native Python, generates all 189
example/report combinations, and checks the unknown-input gate. It complements
Python regression tests and frontend state/export tests; it is not browser UI QA
or independent legal validation.

Runtime documentation: [Pyodide](https://pyodide.org/en/stable/usage/index.html).
The first operation downloads the runtime assets. Browser drafts stay on that
browser's origin. Use synthetic or generic data only.

## Next increments

- Model-assisted intake with passage provenance and explicit reviewer acceptance.
- Evaluation of live evidence extraction and contradiction detection on held-out cases.
- A deployed live provider and durable multi-user storage if the product needs them.
