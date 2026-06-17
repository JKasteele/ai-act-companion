"""Tests for the repository AI-usage scanner (app/scan.py).

Asserts detection is deterministic, distinguishes genai vs ml, finds model
artifacts, and stays a relevance flag (never a classification).

Runs with pytest or standalone (`python tests/test_scan.py`).
"""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.scan import format_report, scan_repo  # noqa: E402


def _make(files):
    d = tempfile.mkdtemp()
    for rel, content in files.items():
        p = Path(d) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    return d


def test_detects_genai_ml_and_model_files():
    d = _make({
        "requirements.txt": "openai>=1.0\nfastapi\n",
        "src/train.py": "import torch\nfrom sklearn import metrics\n",
        "models/classifier.onnx": b"\x00\x00",
    })
    r = scan_repo(d)
    assert r["ai_detected"] is True
    names = {e["name"] for e in r["libraries"]}
    assert "openai" in names and "torch" in names
    assert "genai" in r["categories"] and "ml" in r["categories"]
    assert r["model_file_count"] == 1
    # genai -> Art. 50 consideration; ml/model -> Art. 10 consideration.
    joined = " ".join(r["considerations"])
    assert "Art. 50" in joined and "Art. 10" in joined
    # It is a relevance flag, never a classification (no risk tier anywhere).
    assert "tier" not in r


def test_clean_repo_is_not_flagged():
    d = _make({
        "requirements.txt": "requests\nflask\n",
        "app.py": "import json\nprint('hello')\n",
    })
    r = scan_repo(d)
    assert r["ai_detected"] is False
    assert r["libraries"] == [] and r["model_file_count"] == 0


def test_no_false_positive_on_substring():
    # 'openai' must not match inside an unrelated word like 'myopenaitools'.
    d = _make({"app.py": "import myopenaitools\nx = 1\n"})
    assert scan_repo(d)["ai_detected"] is False


def test_is_deterministic():
    files = {"requirements.txt": "anthropic\nlangchain\n", "m.gguf": b"\x00"}
    d1, d2 = _make(files), _make(files)
    a, b = scan_repo(d1), scan_repo(d2)
    assert a["libraries"] == b["libraries"]
    assert a["categories"] == b["categories"] and a["ai_detected"] == b["ai_detected"]


def test_format_report_is_markdown():
    md = format_report(scan_repo(_make({"requirements.txt": "openai\n"})))
    assert "EU AI Act relevance scan" in md
    assert "AI/ML usage detected" in md
    assert "not a classification" in md  # honest framing present


def _run_standalone():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR {fn.__name__}: {e!r}")
    print(f"\n{passed}/{len(fns)} tests passed.")
    return passed == len(fns)


if __name__ == "__main__":
    sys.exit(0 if _run_standalone() else 1)
