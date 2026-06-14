"""Command-line interface for AI Act Companion.

A thin, scriptable entry point over the deterministic toolkit. It lets you run
the classifier and report generators from a shell - and lets Claude Code (via
the MCP server or the skill) drive the engine. All I/O is JSON or Markdown.

Examples:
  python -m app.cli questionnaire
  python -m app.cli classify --answers examples/hiring_cv_screening.json
  cat answers.json | python -m app.cli classify --answers -
  python -m app.cli classify --answers a.json --save        # stores + prints id
  python -m app.cli report --assessment <id> --type risk
  python -m app.cli report --answers a.json --type dpia --out dpia.md
  python -m app.cli list
"""

import argparse
import json
import sys

from . import reports, storage
from .classifier import classify as classify_fn
from .questionnaire import QUESTIONNAIRE


def _read_json(path):
    """Read a JSON object from a file path, or from stdin when path == '-'."""
    raw = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    return json.loads(raw)


def _emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_questionnaire(_args):
    _emit(QUESTIONNAIRE)
    return 0


def cmd_classify(args):
    answers = _read_json(args.answers)
    classification = classify_fn(answers)
    if args.save:
        assessment = {
            "id": storage.new_id(answers.get("sys_name")),
            "created_at": storage.now_iso(),
            "answers": answers,
            "classification": classification,
        }
        storage.save(assessment)
        _emit({"id": assessment["id"], "classification": classification})
    else:
        _emit({"classification": classification})
    return 0


def cmd_report(args):
    if args.assessment:
        assessment = storage.load(args.assessment)
        if not assessment:
            print(f"Assessment not found: {args.assessment}", file=sys.stderr)
            return 1
    elif args.answers:
        answers = _read_json(args.answers)
        assessment = {
            "id": "(unsaved)",
            "created_at": storage.now_iso(),
            "answers": answers,
            "classification": classify_fn(answers),
        }
    else:
        print("Provide --assessment <id> or --answers <file>.", file=sys.stderr)
        return 2

    _rtype, filename, markdown = reports.render(args.type, assessment)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        print(f"Wrote {args.out} ({len(markdown)} chars; suggested name: {filename})")
    else:
        sys.stdout.write(markdown)
    return 0


def cmd_list(_args):
    _emit(storage.list_all())
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="ai-act", description="AI Act Companion - deterministic CLI."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("questionnaire", help="Print the intake questionnaire as JSON.")

    p_classify = sub.add_parser("classify", help="Classify answers under the EU AI Act.")
    p_classify.add_argument("--answers", required=True,
                            help="Path to answers JSON, or '-' for stdin.")
    p_classify.add_argument("--save", action="store_true",
                            help="Persist the assessment and print its id.")

    p_report = sub.add_parser("report", help="Generate a report (risk/dpia/bias).")
    src = p_report.add_mutually_exclusive_group(required=True)
    src.add_argument("--assessment", help="Id of a saved assessment.")
    src.add_argument("--answers", help="Path to answers JSON (classified on the fly).")
    p_report.add_argument("--type", choices=reports.REPORT_TYPES, default="risk")
    p_report.add_argument("--out", help="Write Markdown to this path (default: stdout).")

    sub.add_parser("list", help="List stored assessments as JSON.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "questionnaire": cmd_questionnaire,
        "classify": cmd_classify,
        "report": cmd_report,
        "list": cmd_list,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
