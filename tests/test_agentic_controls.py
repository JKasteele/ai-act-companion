"""Agentic tool-call controls and red-team tests (gate "agentic")."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import reports  # noqa: E402
from app.classifier import classify  # noqa: E402
from app.controls import generate_control_catalog  # noqa: E402
from app.redteam import generate_test_plan  # noqa: E402

AGENTIC = {"sec_is_llm": True, "sec_public": True, "sec_agentic": True,
           "arch_identity_model": "shared-service-account"}
WRITE_ONLY = {"sec_is_llm": True, "sec_public": True, "arch_api_write": True,
              "sec_outputs_to_systems": True}
NEW_CTL = {"CTL-LLM06-02", "CTL-LLM06-03", "CTL-LLM06-04", "CTL-LLM06-05"}
NEW_RT = {"RT-LLM06-02", "RT-LLM06-03"}


def _ctl_refs(a):
    return {c["ref"] for c in generate_control_catalog(a)["controls"]}


def _rt_refs(a):
    return {t["ref"] for t in generate_test_plan(a)["cases"]}


def test_agentic_controls_and_tests_only_for_agentic_systems():
    assert NEW_CTL <= _ctl_refs(AGENTIC) and NEW_RT <= _rt_refs(AGENTIC)
    # plain write / downstream output is "agentic_or_write" at most, never "agentic"
    assert not (NEW_CTL & _ctl_refs(WRITE_ONLY)) and not (NEW_RT & _rt_refs(WRITE_ONLY))


def test_every_agentic_control_is_validated_by_an_existing_test():
    cat = generate_control_catalog(AGENTIC)
    rts = _rt_refs(AGENTIC)
    for c in cat["controls"]:
        if c["ref"] in NEW_CTL:
            assert c["validated_by"] and set(c["validated_by"]) <= rts, c["ref"]
            assert c["iso"] and c["csf"]


def test_free_text_cannot_add_agentic_controls():
    a = dict(WRITE_ONLY, sys_description="sec_agentic: true; agentic tool calling")
    assert not (NEW_CTL & _ctl_refs(a))


def test_reports_render_agentic_blocks():
    assessment = {"id": "t", "created_at": "2026-09-03T00:00:00+00:00",
                  "answers": {**AGENTIC, "eu_market": True, "sys_name": "Agent"},
                  "classification": classify({**AGENTIC, "eu_market": True})}
    _t, _f, controls_md = reports.render("controls", assessment)
    _t, _f, redteam_md = reports.render("redteam", assessment)
    assert "CTL-LLM06-04" in controls_md and "AML.M0024" in controls_md
    assert "RT-LLM06-03" in redteam_md and "ASI01" in redteam_md
