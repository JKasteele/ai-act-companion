# Security policy

AI Act Companion is a local-first, single-user self-assessment tool with a
stateless public showcase, intended for synthetic/example data (see
[THREAT_MODEL.md](docs/THREAT_MODEL.md)). It is not a persistent multi-user records
service and should not receive personal, confidential or production data.

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

Out of scope: a persistent public/multi-user assessment repository, deployments
that modify the documented demo isolation, and infrastructure operated by third
parties (hosting edge, TLS and provider accounts).

## Hardening already in place

- Path-traversal allowlist on assessment ids.
- HTML-escaping in the report renderer (no `innerHTML` of untrusted content).
- The AI layer cannot decide outcomes, act, or persist: the deterministic
  engine is authoritative and human-in-the-loop review is mandatory.
- Public-demo assessment submissions are stateless; its inventory exposes only
  curated synthetic examples.
- Hosted drafting has per-client and daily limits, a spend guard, cache and a
  labelled replay fallback; a provider-side hard spending limit is still
  required.
- The container runs as an unprivileged user.
- `ruff`, `mypy`, `bandit` (SAST) and `pip-audit` (dependency audit) are blocking
  CI gates.
