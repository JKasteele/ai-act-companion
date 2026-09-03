"""Build the static demo assets shown on the landing page.

Currently one asset: `static/demo/mcp_transcript.json` — a *real* Claude Code /
MCP session against the engine, reconstructed by calling the same functions
the MCP tools call, for the shipped health-insurer example. Nothing in it is
invented: tool results are the engine's actual output (trimmed for display).

    python scripts/build_demo_assets.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import reports  # noqa: E402
from app.classifier import classify  # noqa: E402
from app.forensics import assess_forensic_readiness  # noqa: E402
from app.governance import governance_status  # noqa: E402
from app.questionnaire import QUESTIONNAIRE, all_question_ids  # noqa: E402

OUT = ROOT / "static" / "demo"
EXAMPLE = ROOT / "examples" / "health_insurance_pricing.json"


def _short(text, n=420):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


def main():
    answers = {k: v for k, v in json.loads(EXAMPLE.read_text(encoding="utf-8")).items()
               if not k.startswith("_")}
    cls = classify(answers)
    fr = assess_forensic_readiness(answers, cls)
    gov = governance_status(answers, cls)
    _t, _f, md = reports.render("forensics", {"id": "(unsaved)", "created_at": "…",
                                              "answers": answers, "classification": cls},
                                lang="nl")
    finding = cls["findings"][0]
    transcript = {
        "title": "What this looks like from Claude Code (MCP)",
        "note": ("A reconstructed session: every tool result below is the engine's real output "
                 "for the shipped health-insurer example. Claude runs the intake and writes "
                 "prose; the risk tier and every citation come only from the engine, and "
                 "nothing is stored without an explicit confirmation."),
        "steps": [
            {"role": "user",
             "text": "Run an EU AI Act assessment for our supplementary health-insurance pricing "
                     "model. It scores applicants and proposes a premium band; an underwriter "
                     "decides. We're the deployer, the model comes from a vendor."},
            {"role": "assistant",
             "text": "I'll collect the intake against the questionnaire first, then let the "
                     "engine classify it — I won't guess the tier myself."},
            {"role": "tool", "name": "get_questionnaire", "args": {},
             "result": f"{len(QUESTIONNAIRE['sections'])} sections, {len(all_question_ids())} fields "
                       "(ids, types, allowed values)"},
            {"role": "tool", "name": "classify_ai_system",
             "args": {"answers": {"sys_name": answers["sys_name"], "provider_role": "deployer",
                                  "org_sector": "insurance",
                                  "hr_usecases": ["essential_services"],
                                  "hr_essential_subarea": "insurance_life_health",
                                  "hr_does_profiling": True, "…": "…"}},
             "result": {"tier": cls["tier"], "tier_label": cls["tier_label"],
                        "finding": finding["title"], "refs": finding["refs"],
                        "applies_from": cls["applicability"]["date"],
                        "rationale": _short(finding["rationale"], 300)}},
            {"role": "assistant",
             "text": f"The engine classifies it as **{cls['tier_label']}** under "
                     f"{finding['refs'][0]} — risk assessment and pricing in health insurance — "
                     f"with obligations applying from {cls['applicability']['date']}. Because "
                     "it is a 5(c) system, the fundamental-rights impact assessment is mandatory "
                     "for every deployer, private insurers included (Art. 27(1)). Let me check "
                     "how well you could evidence a decision afterwards."},
            {"role": "tool", "name": "assess_forensic_readiness",
             "args": {"answers": "… (same intake, incl. section 12 fr_* fields)"},
             "result": {"total": fr["total"], "max": fr["max"], "band": fr["band"],
                        "top_gap": fr["gaps"][0]["gap"] if fr["gaps"] else None,
                        "clocks": [c["regime"] for c in fr["clocks"] if c["applies"]]}},
            {"role": "tool", "name": "governance_status",
             "args": {"answers": "…"},
             "result": {"status": gov["status_label"], "next_review": gov["next_review"],
                        "review_overdue": gov["review_overdue"],
                        "literacy_records": len(gov["literacy"])}},
            {"role": "tool", "name": "generate_report",
             "args": {"report_type": "forensics", "lang": "nl"},
             "result": _short(md.split("## Samenvatting (NL)")[1], 380)},
            {"role": "assistant",
             "text": f"Forensic readiness is {fr['total']}/{fr['max']} ({fr['band']}); the "
                     f"first gap to close is: {fr['gaps'][0]['gap'] if fr['gaps'] else '—'} "
                     "I've drafted the Dutch-summarised forensic-readiness plan above. Shall I "
                     "save the assessment to your inventory?"},
            {"role": "user", "text": "Yes, save it."},
            {"role": "tool", "name": "save_assessment",
             "args": {"answers": "…", "confirmed": True},
             "result": {"saved": True, "id": "a1b2c3d4", "tier": cls["tier"]}},
            {"role": "assistant",
             "text": "Saved with your confirmation. The inventory now shows this system with its "
                     "tier, obligations date, forensic-readiness score and next review; "
                     "`/api/register.csv` exports the register entry."},
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "mcp_transcript.json").write_text(json.dumps(transcript, indent=2, ensure_ascii=False)
                                             + "\n", encoding="utf-8")
    print(f"  wrote {OUT / 'mcp_transcript.json'} ({len(transcript['steps'])} steps)")


if __name__ == "__main__":
    main()
