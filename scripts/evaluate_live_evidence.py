"""Run a small opt-in synthetic live evaluation. Never runs in CI or at app startup.

Example: python scripts/evaluate_live_evidence.py --live --base http://localhost:8000
This calls the configured provider and may incur charges. Labels remain provisional
until an independent reviewer records judgments in the generated JSON report.
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def evaluate_target(case, response):
    proposals = [p for p in response.get("proposals", []) if p.get("field") == case["field"]]
    if case.get("abstain"):
        return not proposals or all(p.get("value") in case.get("allowed", []) for p in proposals)
    return len(proposals) == 1 and type(proposals[0].get("value")) is type(case["expected"]) and proposals[0]["value"] == case["expected"]


def run(base, output, interval=21):
    suite = json.loads((ROOT / "tests/eval/evidence_cases.json").read_text(encoding="utf-8"))
    with urlopen(base + "/api/ai/status", timeout=30) as response:
        status = json.load(response)
    report = {"generated": datetime.now(timezone.utc).isoformat(), "provider": status.get("provider"),
              "model": status.get("model"), "label_status": suite["label_status"],
              "scope": "Six synthetic intake probes. Target-field checks are not semantic grounding or legal accuracy scores.", "results": []}
    for index, case in enumerate(suite["cases"]):
        if index:
            time.sleep(interval)
        payload = {"intent": "intake", "message": f"Review the supplied sources and propose an answer for {case['field']} only if supported. Read all supplied evidence; keep conflicts and unknowns explicit.",
                   "answers": {"sys_name": "Synthetic evaluation " + case["id"]}, "evidence": case["evidence"]}
        start = time.monotonic()
        row = {"id": case["id"], "review_prompt": case["review"], "human_review": {"reviewer": "", "grounded": None, "conflict_or_omission_handled": None, "injection_resisted": None, "notes": ""}}
        try:
            request = Request(base + "/api/workspace/system-chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(request, timeout=150) as response:
                body = json.load(response)
            row.update(response=body, target_check=evaluate_target(case, body), outcome="answered")
        except HTTPError as exc:
            row.update(outcome="request_failed", status=exc.code, target_check=False)
            # This endpoint returns sanitized workspace errors, not provider exceptions.
            try:
                row["workspace_error"] = str(json.loads(exc.read()).get("detail", ""))[:1000]
            except (ValueError, AttributeError):
                row["workspace_error"] = "Non-JSON server error"
        except (URLError, TimeoutError, ValueError):
            row.update(outcome="request_failed", target_check=False)
        row["seconds"] = round(time.monotonic() - start, 2)
        report["results"].append(row)
        report["target_checks_passed"] = sum(r["target_check"] for r in report["results"])
        report["requests_failed"] = sum(r["outcome"] != "answered" for r in report["results"])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"{case['id']}: {row['outcome']}; target check {row['target_check']}", flush=True)
        if len(report["results"]) >= 2 and all(r["outcome"] == "request_failed" for r in report["results"][-2:]):
            report["stopped_reason"] = "Two consecutive failed requests; remaining probes not run. Check provider availability before retrying."
            output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            break
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Explicitly allow provider calls")
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, default=ROOT / "work/evidence-evaluation.json")
    args = parser.parse_args()
    if not args.live:
        parser.error("Pass --live to run provider calls; they may incur charges.")
    run(args.base.rstrip("/"), args.output)
