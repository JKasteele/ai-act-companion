# Evaluating live evidence review

The live agent should extract supported answers, leave missing or conflicting
facts unresolved, and treat instructions embedded in documents as untrusted data.
Tests of the tool protocol do not establish that the model interprets evidence correctly.

## Reproducible probe suite

`tests/eval/evidence_cases.json` contains six synthetic probes kept outside the
shipped dossiers and agent prompt: explicit role, explicit absence of write access,
missing permissions, contradictory permissions, injected instructions, and unknown role.
These are development regression probes: failures were used to improve the
agent protocol, so subsequent reruns are not a held-out benchmark.
Expected values are provisional author labels. They are not independently reviewed
ground truth and the set is too small for general model-quality claims.

Run against a configured FastAPI app (local or public). This explicitly invokes
the provider, can incur charges, and respects the existing server budget and cooldown:

```bash
python scripts/evaluate_live_evidence.py --live --base http://127.0.0.1:8000
```

The report is saved to `work/evidence-evaluation.json`, outside version control.
It records provider/model, request failures, latency, complete synthetic responses,
target-field checks, and blank human-review fields. Two consecutive request failures
stop the run; remaining probes are untested, not successful. There are no automatic
retries, prompt tuning, or cherry-picking of successful answers.

The target-field check measures only whether the requested value was proposed or
appropriately omitted against the provisional label. Review every other proposal
and the narrative independently; an exact quote can still be misinterpreted.

## Independent review

Before claiming an accuracy result, have a reviewer other than the implementation
author examine the source packs and expected values. Record reviewer identity/role,
date, disagreements and final labels before running the frozen evaluation again.
For each response inspect semantic grounding, conflict/omission handling and any
obedience to document-injected instructions. Keep failures in the denominator and
report provider availability separately from extraction quality.

## Initial operational check — 5 September 2026

The public demo reported Anthropic `claude-haiku-4-5` configured. Two initial live
intake requests returned HTTP 503 and the run was stopped. A subsequent review-plan request succeeded, while intake requests exposed tool-loop
and response-format failures. The implementation now tracks completed reads,
requires a final response and uses a provider JSON grammar. These observations
do not establish semantic accuracy, conflict recall or injection resistance. Provider configuration alone is not a successful live test.

Safe operational errors now distinguish provider authentication, permissions,
rate limits and insufficient credit without exposing exception text or credentials.
The final structured-output run answered all six probes and passed all six
target-field checks, with zero failed requests. Response times ranged from
8.03 to 18.78 seconds (including first-use schema overhead).
The [complete development record](evaluation-results/2026-09-05-development-probes.json)
includes earlier failed runs and every returned synthetic response.

This is one development run against provisional labels, not a general accuracy
score. Independent semantic review and a fresh held-out set remain outstanding.

A separate [live review-plan smoke result](evaluation-results/2026-09-05-review-plan.json)
returned one unapplied action proposal and two clarification questions with read
sources. The request included prior conversation about contact-update approval.
This verifies the live protocol path; it does not quantify conversation quality.
