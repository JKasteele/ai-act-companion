# 1.0 release candidate

Version `1.0.0rc1` (Python) / `1.0.0-rc.1` (frontend) is a candidate for review,
not a claim that all acceptance work is complete. The existing PR remains draft
and unmerged. No final release tag is created by the candidate build.

## Product journey

1. Open Example systems and choose a realistic fictional dossier.
2. Read the brief and source documents; start a working copy.
3. Inspect the quoted evidence behind each intake proposal. Accept or skip each
   answer yourself. Conflicting and unsupported screening questions stay open.
4. Complete the remaining screening with an accountable reviewer and run the
   original rule engine. The supplied case documents do not answer every question.
5. Compare evidence-review findings with the separate engine findings.
6. Assign follow-up actions, required evidence and review dates. Add human notes.
7. Prepare a review pack. Incomplete profiles export a work-in-progress record;
   assessed profiles also attach the recommended engine reports.

## Realistic case scope

| Fictional organisation | Review decision | Evidence problem |
| --- | --- | --- |
| Meridian Health | Expand a member-service pilot to contact-detail updates? | Conflicting model-boundary data flows, approval enforcement, retention |
| Boreal Water Operations | Move an operations copilot beyond shadow mode? | Staging write permissions, hostile retrieval content, recovery and logging |
| Northstar Services | Proceed with a recruitment assistant procurement? | Candidate filtering, validation-population mismatch, deletion gaps |

These are authored exercises, not accounts of actual organisations or model
discoveries. Positive test results are included with their practical limits.
Internal review criteria are separated from legal requirements. No legal rule
changes are part of this release candidate.

## AI and deployment boundaries

The private static preview runs the original Python engine locally in a browser
worker and supplies authored case proposals. It makes no live model calls.
The local FastAPI app can use the existing configured Ollama/Anthropic provider
for evidence investigation and intake proposals. Proposals include exact quoted
passages, and a human must accept each one before it changes the profile.

Text/Markdown imports are supported; PDF/Word parsing and multi-user storage are
not included. Browser-local drafts should be exported for a portable copy. Action
status is reviewer-supplied; no status automatically verifies a control or grants
launch approval.

## Verification and remaining acceptance

The automated suite checks native/browser parity, report generation, authored
source resolution, typed proposal values, literal quote matching, bounded live
orchestration with mocked providers, persistence, exports, and human-review gates.
All three dossiers are exercised against the browser engine, alongside all nine
reference profiles and their 189 report combinations.

These checks are protocol and regression evaluations. They do not measure live
extraction accuracy, contradiction-detection recall, semantic grounding or legal
correctness. Fabricated/unread quotations are rejected, but a valid quotation can
still be interpreted incorrectly. No numerical live-model quality score is claimed.

Before promoting the candidate to final 1.0:

- Review the complete user journey in the browser, including mobile, keyboard
  interaction, file imports, source navigation and print/PDF output.
- Evaluate a configured live model against held-out, independently reviewed
  source/answer cases, including conflicts, omissions and injected instructions.
- Review the candidate's product scope and documented limitations, then merge
  and tag the final release explicitly.
