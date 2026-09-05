from scripts.evaluate_live_evidence import evaluate_target


def test_target_checks_distinguish_unknown_false_and_failed_extraction():
    case = {"field": "arch_api_write", "expected": False}
    assert evaluate_target(case, {"proposals": [{"field": "arch_api_write", "value": False}]})
    assert not evaluate_target(case, {"proposals": [{"field": "arch_api_write", "value": 0}]})
    assert not evaluate_target(case, {"proposals": []})
    assert evaluate_target({"field": "arch_api_write", "abstain": True}, {"proposals": []})
    assert not evaluate_target({"field": "arch_api_write", "abstain": True}, {"proposals": [{"field": "arch_api_write", "value": False}]})
