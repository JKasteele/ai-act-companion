# Threat model — AI Act Companion

AI Act Companion assesses the governance and security of other AI systems, so
this document applies the same discipline to the tool itself.

_Scope: the local application, CLI/MCP integration, public Hugging Face demo and
optional Ollama/manual/replay/Anthropic drafting providers. Last reviewed
2026-09-04._

## 1. Deployment profiles and assumptions

The evidence workspace adds a guided static preview and optional local live-agent
endpoint. Its source documents are fixed synthetic fixtures. Review drafts stay
in browser storage; API requests are stateless. Live tools can read allowlisted
evidence and inspect supplied review state, but cannot write files, fetch external
URLs, classify, or approve launch. Citation checks verify source access, not that
every model claim follows from the source. See [WORKSPACE.md](WORKSPACE.md) for
tool limits, billing/cancellation limitations, and provenance boundaries.

- **Local profile:** single-user FastAPI app, CLI and MCP server. Assessments are
  plain JSON under `data/`; there is no authentication because the default bind
  address is loopback and the product is not a multi-user records service.
- **Public demo profile:** unauthenticated, multi-visitor showcase. In
  `DEMO_MODE`, submitted assessments are classified statelessly and are not
  added to shared inventory. Only shipped synthetic examples are retrievable.
- **Data rule:** synthetic/generic data only. The local JSON store is not
  encrypted. Public-demo input crosses the network and hosted-provider input is
  disclosed egress; neither path is suitable for personal or confidential data.
- **Optional AI:** local Ollama, manual paste, deterministic replay or hosted
  Anthropic. AI output is draft-only; the deterministic classifier remains the
  sole source of the risk tier and citations.

## 2. Trust boundaries and data flow

```text
Browser ──HTTP──► FastAPI ──► deterministic engine
                      │              │
                      │              └──► stateless result (public demo)
                      ├──► local JSON storage (local profile only)
                      └──► drafting provider
                            ├── Ollama on a configured host
                            ├── labelled replay data
                            └── Anthropic API (explicit egress)

Claude Code / other MCP client ──stdio──► mcp_server.py ──► engine + local store
```

Trust boundaries are browser↔API, API↔filesystem, MCP client↔server and
application↔drafting provider. Free text, imported answers and LLM output are
untrusted.

## 3. Threats and mitigations

| # | Threat | Main mitigation | Residual risk |
|---|---|---|---|
| T1 | Path traversal through an assessment id | `storage.is_valid_id` restricts ids to a small allowlist; invalid ids are rejected | Low |
| T2 | Stored XSS in results or Markdown previews | Untrusted content is HTML-escaped; result fields use text nodes | Low; keep frontend regression tests/manual checks |
| T3 | Cross-visitor disclosure in the public demo | `DEMO_MODE` is stateless for submissions and exposes only curated examples | Low for assessment content; no confidentiality promise for submitted network traffic |
| T4 | Oversized or malformed requests | Pydantic validation, bounded identifiers and free-text/request limits | Low/Medium; platform-level rate limiting is still recommended |
| T5 | Prompt injection or malicious model output | LLM never determines the tier; output is parsed without `eval`, schema-validated and shown for human review | Low for classification; draft quality can still be degraded |
| T6 | Secret leakage | Keys come from environment/secrets, are never returned or logged, and `.env` is ignored | Low; deployment operators remain responsible for secret controls |
| T7 | Hosted-AI cost abuse | Per-client cooldown/cap, daily cap, lifetime software budget, dedupe cache and replay fallback | Medium; ephemeral counters can reset, so a provider-side hard spend limit is required |
| T8 | Proxy-header spoofing bypassing per-client limits | Rate limiting uses the proxy-appended hop rather than trusting the first client-supplied value | Medium; deployment-specific proxy configuration must be verified |
| T9 | Supply-chain compromise | Small dependency set, blocking `pip-audit` over the resolved dev/MCP environment, Ruff/Bandit, and CI on Linux/Windows | Medium; lower-bound constraints are not a lockfile or provenance guarantee |
| T10 | Container privilege escalation | Container runs as an unprivileged application user | Low/Medium; hosting-platform isolation remains external |
| T11 | Tampering with local JSON assessments | Atomic writes prevent partial replacement; the local user controls the files | Accepted for the single-user profile; no integrity signature is claimed |
| T12 | External-provider outage or response drift | Deterministic engine has no model dependency; drafting degrades to labelled replay | Low for classification, Medium for hosted drafting availability |

## 4. AI-specific controls

- **Prompt injection:** free text cannot override the deterministic classifier.
  The assistant can only propose draft questionnaire values or narrative.
- **Improper output handling:** model JSON is parsed defensively, unknown fields
  and invalid enumerations are discarded, and nothing is executed.
- **Excessive agency:** the drafting layer has no action tools and cannot submit
  or persist an assessment by itself.
- **Data disclosure:** replay has no egress; Ollama uses the configured endpoint;
  Anthropic mode sends the disclosed drafting input to the Anthropic API.
- **MCP:** tools expose deterministic computation and explicit local persistence.
  They do not shell out and assessment-id reads use the same allowlist as HTTP.

## 5. Explicit limitations

- The public demo is a showcase, not a tenant-isolated compliance repository.
- There is no authentication/authorization for a persistent shared deployment.
- Application rate limits are best-effort controls, not a substitute for edge
  protection, TLS, monitoring or a provider-side spending cap.
- Dependency constraints express compatibility ranges; they are not fully
  reproducible locks. Release deployments should pin resolved images/digests and
  can add an SBOM/provenance attestation as the project matures.
- No legal, security or privacy guarantee is made. Review generated drafts and
  obtain qualified advice for real decisions.

See [SECURITY.md](../SECURITY.md) for private vulnerability reporting.
