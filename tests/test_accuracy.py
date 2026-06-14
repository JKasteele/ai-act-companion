"""Golden-set accuracy evaluation for the rule-based classifier.

Validates the classifier against a curated set of synthetic AI systems whose
expected EU AI Act tier was derived by independent reading of the regulation
(Art. 5 / 6 / 50), NOT by running the classifier. This turns "it works" into a
measurable, reproducible accuracy figure instead of vibes.

Runs with pytest (`pytest`) or standalone (`python tests/test_accuracy.py`).
"""

import json
import sys
from pathlib import Path

# Make the project root importable when run standalone.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.classifier import classify  # noqa: E402

GOLDEN_SET = ROOT / "examples" / "golden_set.json"
VALID_TIERS = {"prohibited", "high", "limited", "minimal"}


def _load_cases():
    cases = json.loads(GOLDEN_SET.read_text(encoding="utf-8"))
    assert isinstance(cases, list) and cases, "golden_set.json must be a non-empty array"
    return cases


def _evaluate():
    """Return (results, passed, total) where results is a list of dicts."""
    results = []
    passed = 0
    for case in _load_cases():
        expected = case["expected_tier"]
        got = classify(case["answers"])["tier"]
        ok = got == expected
        passed += ok
        results.append({"name": case["name"], "expected": expected,
                        "got": got, "ok": ok})
    return results, passed, len(results)


def test_golden_set_is_well_formed():
    cases = _load_cases()
    names = [c["name"] for c in cases]
    assert len(names) == len(set(names)), "golden-set names must be unique"
    for c in cases:
        assert set(c) >= {"name", "expected_tier", "rationale", "answers"}, \
            f"{c.get('name')!r} is missing required keys"
        assert c["expected_tier"] in VALID_TIERS, \
            f"{c['name']}: invalid expected_tier {c['expected_tier']!r}"
        assert isinstance(c["answers"], dict) and c["answers"], \
            f"{c['name']}: answers must be a non-empty dict"


def test_each_golden_case_matches():
    results, _, _ = _evaluate()
    mismatches = [
        f"{r['name']}: expected {r['expected']!r}, got {r['got']!r}"
        for r in results if not r["ok"]
    ]
    assert not mismatches, "Classifier mismatches:\n  " + "\n  ".join(mismatches)


def test_overall_accuracy_is_100_percent():
    _, passed, total = _evaluate()
    accuracy = passed / total
    assert accuracy == 1.0, f"Accuracy {accuracy:.1%} ({passed}/{total}); expected 100%"


def test_golden_set_covers_all_tiers():
    tiers = {c["expected_tier"] for c in _load_cases()}
    assert tiers == VALID_TIERS, f"Golden set must cover every tier; missing {VALID_TIERS - tiers}"


def _run_standalone():
    results, passed, total = _evaluate()
    width = max(len(r["name"]) for r in results)
    print("Golden-set accuracy evaluation")
    print("=" * (width + 30))
    print(f"  {'SYSTEM'.ljust(width)}  {'EXPECTED':<10} {'GOT':<10} OK")
    print("  " + "-" * (width + 24))
    for r in results:
        mark = "PASS" if r["ok"] else "FAIL"
        print(f"  {r['name'].ljust(width)}  {r['expected']:<10} {r['got']:<10} {mark}")

    dist = {}
    for r in results:
        dist[r["expected"]] = dist.get(r["expected"], 0) + 1
    print("\n  Tier distribution (expected): " +
          ", ".join(f"{t}={dist.get(t, 0)}" for t in
                    ("prohibited", "high", "limited", "minimal")))

    mismatches = [r for r in results if not r["ok"]]
    if mismatches:
        print("\n  Mismatches:")
        for r in mismatches:
            print(f"    {r['name']}: expected {r['expected']}, got {r['got']}")

    print(f"\n  {passed}/{total} passed ({passed / total:.0%} accuracy).")
    return passed == total


if __name__ == "__main__":
    ok = _run_standalone()
    sys.exit(0 if ok else 1)
