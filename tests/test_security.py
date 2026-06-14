"""Tests for the AI security lens.

Runs with pytest or standalone (`python tests/test_security.py`).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import reports, storage  # noqa: E402
from app.security import assess_security  # noqa: E402


def _ids(profile):
    return {r["id"] for r in profile["risks"]}


def test_no_security_context_yields_no_risks():
    p = assess_security({"sys_name": "x", "eu_market": True})
    assert p["risks"] == []
    assert p["answered"] is False


def test_public_llm_triggers_core_llm_risks():
    p = assess_security({
        "sec_is_llm": True, "sec_public": True, "sec_external_data": True,
        "sec_third_party_models": True, "data_personal": True,
    })
    ids = _ids(p)
    # generative + exposed + RAG-ish + supply chain + PII
    for expected in ("LLM01:2025", "LLM02:2025", "LLM03:2025", "LLM07:2025", "LLM09:2025"):
        assert expected in ids, f"missing {expected} in {ids}"


def test_non_llm_still_maps_data_and_supply_chain():
    # An ML ranking system (not generative) with personal data + external data.
    p = assess_security({
        "sec_is_llm": False, "data_personal": True, "sec_external_data": True,
    })
    ids = _ids(p)
    assert "LLM02:2025" in ids   # sensitive info disclosure
    assert "LLM04:2025" in ids   # poisoning via external data
    assert "LLM01:2025" not in ids  # no prompt injection without an LLM


def test_each_risk_carries_atlas_and_refs():
    p = assess_security({"sec_is_llm": True, "sec_public": True})
    assert p["risks"]
    for r in p["risks"]:
        assert r["atlas"] or r.get("atlas_note")
        assert r["ai_act_refs"] and r["nist_refs"] and r["mitigation"]


def test_security_report_renders():
    answers = {"sys_name": "ChatBot", "sec_is_llm": True, "sec_public": True}
    assessment = {"id": "t", "created_at": "2026-01-01T00:00:00+00:00",
                  "answers": answers, "classification": {},
                  "security": assess_security(answers)}
    rtype, filename, md = reports.render("security", assessment)
    assert rtype == "security"
    assert filename.endswith(".md")
    assert "OWASP" in md and "ATLAS" in md and "LLM01:2025" in md


def test_storage_rejects_path_traversal_ids():
    # The id arrives from the API/MCP; reject traversal/abs paths.
    for bad in ("../secret", "..\\secret", "/etc/passwd", "a/b", "a.b", ""):
        assert storage.load(bad) is None
        assert storage.is_valid_id(bad) is False
    assert storage.is_valid_id("talentmatch-cv-screening-5ea377b9") is True


def test_storage_save_load_delete_roundtrip():
    aid = storage.new_id("Test Delete System")
    storage.save({"id": aid, "created_at": "2026-01-01T00:00:00+00:00",
                  "answers": {"sys_name": "Test Delete System"},
                  "classification": {}, "security": {"risks": []}})
    assert storage.load(aid) is not None
    assert storage.delete(aid) is True
    assert storage.load(aid) is None
    assert storage.delete("does-not-exist-xyz") is False


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
