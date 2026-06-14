# Security policy

AI Act Companion is a local-first, single-user self-assessment tool intended for
synthetic/example data (see [THREAT_MODEL.md](THREAT_MODEL.md)). It is not
hardened for multi-user or networked deployment.

## Reporting a vulnerability

Please report security issues privately rather than opening a public issue:

- Use GitHub's **"Report a vulnerability"** (Security Advisories) on the
  repository, or
- email the maintainer (see the repository profile).

Include reproduction steps and impact. I aim to acknowledge within a few days.
As a personal portfolio project there is no formal SLA, but credible reports are
very welcome.

## Scope

In scope: the code in this repository (engine, API, CLI, MCP server, frontend).

Out of scope: running it as a public/multi-user service without the additional
controls listed in the threat model (auth, isolation, rate limiting, TLS).

## Hardening already in place

- Path-traversal allowlist on assessment ids.
- HTML-escaping in the report renderer (no `innerHTML` of untrusted content).
- The AI layer cannot decide outcomes, act, or persist: the deterministic
  engine is authoritative and human-in-the-loop review is mandatory.
- `ruff`, `bandit` (SAST) and `pip-audit` (dependency audit) run in CI.
