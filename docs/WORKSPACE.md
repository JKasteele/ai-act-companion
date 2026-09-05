# Evidence workspace

The primary interface is a synthetic health-insurer review demonstrating data
and AI governance with technical security depth. It is a working case, not a
claim of automated compliance.

## Journey and provenance

Compare the business proposal and architecture, record a clarification, investigate
approval enforcement and retention, assign actions, then download a draft record.
The organisation, documents, and three findings are authored fixtures in
`app/workspace/case.py`. Internal review criteria are distinguished from legal
requirements. Guided findings must not be presented as AI discoveries.

`ReviewState` has explicit unknowns. Reviewer statements do not change source
documents or engine inputs. Completion references can make an action ready for
evidence review, never verified or approved. The browser stores a versioned local
draft; API requests pass state explicitly. The server does not persist workspace
conversations or reviewer notes. Reset clears this case only. Synthetic data only.

## Guided and live modes

The guided walkthrough maps a small set of questions to authored explanations.
Unsupported questions receive an honest explanation of this boundary.

Live AI is opt-in in the local FastAPI app, reusing Ollama or Anthropic. Each
request contains the current question, review state, and evidence catalogue.
The model can call `read_evidence(source_id)` or `inspect_review()` through a
bounded JSON tool loop: at most four tools and five model calls per request.

Citation IDs must refer to sources actually read. Unknown tools, unread citations,
invalid responses, provider failures, and tool exhaustion stop the request
explicitly. No replay is silently presented as a live answer. There are no file
write, arbitrary path, external fetch, approval, or classification tools.

The existing spend guard runs before every model call. Per-client cooldown and
request caps apply once per bounded agent request. This is best-effort local
accounting, not an atomic multi-worker billing reservation; provider-side hard
spend limits remain necessary. Client cancellation may leave an in-flight model
call running until its existing timeout. Citation checks establish source access,
not semantic entailment. Generated prose still requires human review.

The model gets structured review state, not a durable conversation transcript.
The client displays the conversation for the session.

## Engine integration

The user confirms the supplied synthetic read-only profile before requesting the
engine result. `scenario_assessment()` reuses the existing health-insurer service
assistant example with a display-name change and exposes exact inputs and the
knowledge version. Proposed write access is a separate change. Reviewer notes
never silently become classifier inputs. Existing legal rules are preserved,
not independently revalidated by this UI overhaul.

Explicit unknowns apply to the new workspace. The original questionnaire defaults
and legacy API completeness checks are unchanged. General document-to-assessment
intake needs explicit completeness checks before automated classification.

## Build and deployment

FastAPI opens `static/workspace/index.html`; `/classic` serves the original UI.
Existing CLI, MCP, and API routes remain available.

`python scripts/build_workspace.py` exports the frontend, case, and an engine
result computed at build time to `dist/`. The static host runs no Python or live
model. It labels the result as a snapshot, disables Live AI, and keeps edits on
the visitor's device. The export copies only an explicit public-file allowlist;
no credentials, saved records, or backend source enter the public bundle.

## Next increments

- Document ingestion with passage provenance and an evaluation corpus.
- General case state beyond this authored scenario.
- An adapter for the selected deployment model after API access is established.
- Held-out evaluations for live evidence extraction and contradiction detection.
  Mock-provider tests validate orchestration, not model reasoning quality.
