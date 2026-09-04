# Portfolio Readiness Review — Closed

_Closed: 2026-09-04. This page records the outcome of the repository review;
the release history and implementation detail live in
[CHANGELOG.md](../CHANGELOG.md) and [README.md](../README.md)._

The review milestones are complete. The project now presents one coherent
portfolio story: a deterministic, explainable EU AI Act classifier connected to
evidence-ready governance and security artefacts. An LLM can help draft intake
answers, but cannot decide the legal tier, and every output requires human
review.

## Shipped

- Actor-aware and territorial-scope classification, Annex I/III routing,
  GPAI-provider versus integrator logic, Art. 4 support measures, and the
  relevant amendments from Regulation (EU) 2026/1744.
- A golden regression set plus API, CLI, MCP, storage, report, AI-service and
  adversarial tests. CI enforces linting, typing, generated-text drift, at least
  90% coverage, dependency auditing, Linux/Windows support and a Docker smoke
  test.
- One report catalogue shared by the API and frontend, with 21 governance,
  conformity, privacy, monitoring and AI-security artefacts.
- A stateless public demo that exposes synthetic examples only, rejects
  deletion, bounds input and hosted-provider spend, and labels replayed AI
  drafts explicitly.
- A local-first deployment path, non-root container, PyPI trusted publishing,
  MCP integration, repository scanner and GitHub Action.
- A hiring-manager-facing README with install choices, demo-versus-local
  boundaries, legal sources, limitations, screenshots, a reproducible animated
  walkthrough and links to generated example reports.

## Deliberate scope boundaries

- Persistent multi-user authentication is not offered. Persistent storage is a
  local-deployment feature; the public showcase is stateless.
- The static frontend intentionally has no bundler. A dedicated JavaScript test
  runner and linter remain optional future tooling; CI still performs a Node
  syntax check and the end-to-end capture script exercises the main UI flow.
- Generated guidance is a structured first pass, not legal advice or a
  substitute for counsel, notified bodies, supervisory authorities, official
  templates or organisation-specific evidence.

## Maintenance triggers

Re-open this review when the consolidated AI Act changes, the Commission or AI
Office publishes material guidance or templates, harmonised standards alter
the evidence model, or a new deployment mode changes the threat model. Update
`KNOWLEDGE_VERSION`, `LAST_REVIEWED`, the golden set and generated examples in
the same change.
