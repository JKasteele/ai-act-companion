# Review-Driven Roadmap

_Last reviewed: 2026-07-03_

> **Status (2026-07-03):** Milestones 1–4 are largely implemented — see the
> `[Unreleased]` section of [../CHANGELOG.md](../CHANGELOG.md) for what shipped.
> Still open by design: PyPI release automation (M2.8), the optional MCP
> surface changes (M3.8: `scan` tool, report-by-id, `confirmed` flag), and the
> deferred items at the bottom. This document is kept as the rationale/reference.

This document captures the findings of a full codebase + repository review and
organizes the follow-up work into milestones. It is meant to be picked up one
milestone at a time.

**What the review found working well:** the deterministic engine and its
`f(answers) -> dict` purity, the knowledge base's honesty (every cross-framework
map carries a `PROVENANCE` disclaimer, article tokens resolve to live deep links
via `ref_url()`), the adversarial red-team suite that proves prompt injection
cannot move the risk tier, and the README. The weaknesses below cluster in four
areas: regulatory-logic gaps that can produce incorrect guidance, under-tested
front-ends (the CLI, MCP server, and AI layer have no tests), peripheral
hardening, and presentation polish.

The architectural invariant in [CLAUDE.md](../CLAUDE.md) still holds and every
item below must preserve it: **a deterministic engine decides the tier; the LLM
is only an interface; human review is mandatory.**

---

## Milestone 1 — Regulatory-logic correctness

These change *what the tool tells a user to do*, so each item needs a labelled
golden-set case reasoned from the regulation (never from the classifier's
current output), per the working conventions in [CLAUDE.md](../CLAUDE.md).

1. **Provider vs. deployer obligations (collected data currently unused).**
   `provider_role` (`app/questionnaire.py`) is intake but never branches
   anything. `HIGH_RISK_OBLIGATIONS` (`app/knowledge/eu_ai_act.py`) mixes
   provider-only duties (Art. 11 tech docs, Art. 17 QMS, Art. 43 conformity
   assessment, Art. 47/48 DoC + CE marking, Art. 49 registration) with deployer
   duties (Art. 26, 27) and shows all of them to everyone — so a pure deployer
   is wrongly told to perform conformity assessment and CE marking. Split the
   obligation set into provider / deployer / shared, filter by `provider_role`
   in `app/classifier.py`, and reflect the split in the risk report and
   compliance tracker in `app/reports.py`.

2. **Art. 2 scope exemptions (over-triggering).** Scope is currently gated on
   `eu_market` only (`app/classifier.py`). Add questionnaire fields for the real
   carve-outs — Art. 2(3) military / national security / defence, Art. 2(6)
   scientific R&D, Art. 2(8) pre-market research and testing, Art. 2(10) purely
   personal non-professional use — and have the classifier return out-of-scope
   citing the specific paragraph in `refs` / `source_questions`. When a system
   is genuinely out of scope, the GPAI (Chapter V) findings must also stop
   firing (`app/classifier.py`) — today the out-of-scope path still emits them,
   which is internally inconsistent.

3. **GPAI open-source carve-out (Art. 53(2)).** Add a `gpai_open_source` field.
   When the model is released under a free/open licence and has no systemic
   risk, drop the Art. 53(1)(a)–(b) technical-documentation and
   downstream-information obligations (`app/classifier.py`,
   `app/knowledge/eu_ai_act.py`). The systemic-risk path keeps all obligations.

4. **GPAI applicability-date contradiction.** `applies_from`
   (`app/knowledge/eu_ai_act.py`) keys only off the risk *tier*, so a
   minimal-tier GPAI model's risk report headline reads "No mandatory deadline"
   while the compliance tracker (`app/reports.py`) correctly shows the 2 Aug 2025
   GPAI date. Make `applies_from` GPAI-aware so the two reports agree.

5. **Art. 4 AI literacy never surfaced as an obligation.** In force since Feb
   2025 for essentially all in-scope providers and deployers, but it appears
   only in the timeline (`app/knowledge/eu_ai_act.py`) and never lands in
   `recommended_artifacts` or the compliance tracker. Surface it as a baseline
   obligation for every in-scope tier.

6. **Missing high-risk obligations.** Art. 16 (provider obligations overview),
   Art. 20 (corrective actions / withdrawal), Art. 22 (authorised
   representatives for non-EU providers), and Art. 25 (value-chain
   responsibilities) are absent from `HIGH_RISK_OBLIGATIONS`.

7. **Coarser explainability on Annex III findings.** `_check_high_risk`
   (`app/classifier.py`) records `source_questions: ["hr_usecases"]` generically
   rather than the specific triggering option, so the high-risk trail is less
   precise than the prohibited/transparency trails (which record the exact qid).

8. **Golden-set coverage.** Add cases for: R&D exemption, military exemption,
   deployer-only high-risk, open-source GPAI (non-systemic), and open-source
   GPAI with systemic risk. `tests/test_accuracy.py` must stay at 100%; add a
   unit test per new branch in `tests/test_classifier.py`.

---

## Milestone 2 — Tests & CI

The engine is well covered; the three front-ends and the AI layer are the holes.

1. **`tests/test_cli.py` (new).** The `ai-act` CLI has no tests. Drive
   `app.cli.main([...])` for `questionnaire` / `classify` / `report` / `scan` /
   `list` against the `examples/` fixtures. While there, fix `_read_json` in
   `app/cli.py` to use a `with` block instead of a bare `open()`.

2. **`tests/test_mcp.py` (new).** None of the MCP tools in `mcp_server.py` are
   tested; they are plain functions — call them directly (classify,
   `generate_report` across all report types, save/get/list round-trip) so a
   change to a tool signature or the report-type `Literal` is caught.

3. **`tests/test_llm_service.py` (new).** Cover `app/llm/service.py`
   orchestration and the deterministic `manual` provider; mock the Ollama HTTP
   call in `app/llm/ollama.py`. Add API tests for
   `/api/ai/status|prefill|parse|narrative` (`app/main.py`) to
   `tests/test_api.py`.

4. **Storage round-trip tests.** Assert `save` / `load` / `list_all` / `new_id`
   and the malformed-JSON skip paths in `app/storage.py` directly (only the
   path-traversal guard is currently tested).

5. **Coverage in CI.** Add `pytest-cov` to the `dev` extra in `pyproject.toml`
   and a `pytest --cov=app --cov=mcp_server` step in
   `.github/workflows/ci.yml`.

6. **CI matrix & strictness.** Add `windows-latest` to the matrix — the project
   is Windows-developed but CI runs Linux-only. Consider promoting mypy and
   pip-audit from non-blocking (`|| true`) to blocking. Align `setup-python`
   versions between `.github/workflows/ci.yml` (v6) and `action.yml` (v5).

7. **Docker smoke test.** A `Dockerfile` exists but CI never builds it; add a
   build + `curl /` smoke job.

8. **Release / PyPI automation (needs a decision — this publishes publicly).**
   A tag-triggered `release.yml` using PyPI trusted publishing would let
   `action.yml` install `ai-act-companion==<tag>` instead of from git and give
   the README a real `pip install` story.

---

## Milestone 3 — Hardening & code quality

1. **DEMO_MODE server-side guard.** In demo mode the app is deliberately public
   with shared storage, and today the only protection is the UI banner — any
   visitor can `DELETE /api/assessments/{id}`. When `DEMO_MODE` is set, enforce
   read-only server-side (403 the delete and persistence) in `app/main.py`.

2. **Sanitize free-text in reports.** `sys_description`, `intended_purpose`,
   `human_oversight`, etc. are interpolated raw into Markdown in
   `app/reports.py`; crafted text (pipes, raw HTML) can corrupt tables or inject
   content into the rendered report. This does **not** affect classification or
   severity — that injection-proof guarantee holds — but the documents
   themselves should be escaped through one helper. Add a report-injection case
   to `tests/test_red_team.py`.

3. **De-duplicate normalization helpers.** `_truthy` is copied verbatim in seven
   modules (`app/classifier.py`, `app/security.py`, `app/redteam.py`,
   `app/stride.py`, `app/data_security.py`, `app/incident.py`,
   `app/knowledge/monitoring.py`) and `_select` in three. Extract a single
   `app/_normalize.py`. Reconcile `reports._bool()` in `app/reports.py`, which
   disagrees with `_truthy` on values like `"0"` and `"off"` — the DPIA gate can
   diverge from the classifier's own reading of `data_personal`.

4. **Single source of truth for report types.** The list is duplicated in four
   places (`reports.REPORT_TYPES`, the MCP `Literal` in `mcp_server.py`, the
   frontend tab buttons in `static/index.html`, and the README table). Serve
   `reports.REPORT_TYPES` via `/api/config`, render the tabs from it in
   `static/app.js`, and derive the MCP `Literal` from the same list.

5. **Atomic storage writes.** `app/storage.py` writes directly, so an
   interrupted write corrupts a record. Write to a temp file and `os.replace`.

6. **Frontend cleanup.** Remove the dead `fillExample()` in `static/app.js`
   (superseded by the `/api/examples` dropdown); route the two remaining raw
   `innerHTML` sinks through `escapeHtml`; self-host the Google Fonts referenced
   in `static/index.html` so the "fully local / private" claim is literally true
   (the page currently fetches from `fonts.googleapis.com` on every load).

7. **API robustness.** Sanitize the raw exception text echoed into 502 `detail`
   responses in `app/main.py`; add length caps on free-text fields
   (`app/llm/base.py` does `str(value)` with no bound) and a body-size limit on
   the AI endpoints; de-duplicate the double file read between
   `storage.list_all` and `_portfolio_rows` in `app/main.py`.

8. **Front-end contract consistency.** MCP has no `scan` tool (a headline
   feature) and no report-by-id path, and `get_assessment` returns
   `{"error": ...}` while the API returns 404 and the CLI exits 1 — three
   not-found contracts. Optionally add an explicit `confirmed: bool` parameter to
   the MCP `save_assessment` / classify path to turn the human-in-the-loop
   convention into a checkable contract (this is the single most fragile point
   in the "LLM only as interface" invariant on the MCP surface).

---

## Milestone 4 — README & repository presentation

1. **Install story.** State explicitly that the package is not on PyPI and show
   the git / Docker / Hugging Face paths near Quickstart; explain what the
   `.[dev]` / `.[mcp]` / `.[capture]` extras contain.

2. **AI-layer config table.** Show the env vars from `.env.example` inline
   instead of only referencing the file.

3. **Demo-vs-local comparison.** A short table separating what the public
   Hugging Face Space shows (deterministic engine, AI layer off, ephemeral
   storage) from what a local deployment unlocks.

4. **Link `CONTRIBUTING.md` and `CHANGELOG.md`** from the README body — both
   exist but are currently orphaned.

5. **Deep-link the Legal-grounding citations** to the AI Act Explorer / EUR-Lex,
   reusing the URLs the engine already produces via `ref_url()`.

6. **Action tag semantics.** The README example pins `@v0.7.0` but `action.yml`
   defaults its `ref` input to `main`; document which to use.

7. **MCP setup walkthrough.** A few numbered steps (or a screenshot) of the
   Claude Code approval prompt to lower the adoption barrier.

8. **Data-persistence note.** One paragraph on `data/`: plain JSON, gitignored,
   no encryption at rest, and how to purge old assessments.

---

## Deferred (need separate decisions)

- **New report types:** an EU Declaration of Conformity skeleton (Art. 47), an
  Art. 49 EU-database registration data sheet, and a dedicated GPAI obligations
  report (Art. 53/55 with a training-data-summary and copyright-policy
  template). GPAI is a first-class regime but currently produces only a couple
  of findings with no dedicated artifact.
- **JS test runner / eslint** for `static/` — a tooling decision for a project
  that intentionally has no build step.
- **Auth / rate limiting** beyond the DEMO_MODE guard — out of scope for a
  local-first tool.
