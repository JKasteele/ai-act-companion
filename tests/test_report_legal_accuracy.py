"""Regression tests for actor- and scope-sensitive legal report wording."""

from app import reports
from app.classifier import classify
from app.knowledge import data_governance as dg
from app.knowledge import forensics as fx
from app.knowledge import sector_frameworks as sfx
from app.questionnaire import QUESTIONNAIRE


def _assessment(answers):
    return {
        "id": "legal-regression",
        "created_at": "2026-09-04T00:00:00+00:00",
        "answers": answers,
        "classification": classify(answers),
    }


def test_deleted_article_10_5_is_absent_from_owned_knowledge_and_reports():
    owned_text = repr(dg.CROSSWALK) + repr(fx.EVIDENCE_ARTEFACTS) + repr(sfx.ALTAI)
    assert "Art. 10(5)" not in owned_text
    md = reports.render("datagov", _assessment({
        "eu_market": True,
        "provider_role": "deployer",
        "hr_usecases": ["essential_services"],
        "hr_essential_subarea": "insurance_life_health",
        "data_special_category": True,
    }))[2]
    assert "Art. 10(5)" not in md
    assert "Art. 4a" in md and "paragraph 2 covers deployers" in md
    assert "eur-lex.europa.eu/eli/reg/2026/1744" in md


def test_deployer_datagov_does_not_assign_provider_training_data_duty():
    a = {
        "eu_market": True,
        "provider_role": "deployer",
        "hr_usecases": ["employment"],
        "hr_does_profiling": True,
    }
    md = reports.render("datagov", _assessment(a))[2]
    assert "provider remains responsible" in md
    assert "input data under its control" in md
    assert "No input-data inventory" in md
    assert "Art. 10(2)(a)" not in md


def test_fria_recommendation_is_actor_and_scope_sensitive():
    provider = {
        "eu_market": True,
        "provider_role": "provider",
        "hr_usecases": ["employment"],
        "hr_does_profiling": True,
    }
    provider_md = reports.render("risk", _assessment(provider))[2]
    assert "Fundamental rights impact assessment - FRIA" not in provider_md

    critical_public_deployer = {
        "eu_market": True,
        "provider_role": "deployer",
        "deployer_fria_status": "body_public_law",
        "hr_usecases": ["critical_infra"],
        "hr_does_profiling": True,
    }
    critical_md = reports.render("risk", _assessment(critical_public_deployer))[2]
    fria_md = reports.render("fria", _assessment(critical_public_deployer))[2]
    assert "Fundamental rights impact assessment - FRIA" not in critical_md
    assert "Annex III point 2 systems are expressly excluded" in fria_md

    credit_deployer = {
        "eu_market": True,
        "provider_role": "deployer",
        "hr_usecases": ["essential_services"],
        "hr_essential_subarea": "creditworthiness",
    }
    assert "Fundamental rights impact assessment - FRIA" in reports.render(
        "risk", _assessment(credit_deployer)
    )[2]


def test_provider_documents_are_not_assigned_to_a_pure_deployer():
    deployer = {
        "eu_market": True,
        "provider_role": "deployer",
        "hr_usecases": ["employment"],
        "hr_does_profiling": True,
    }
    assessment = _assessment(deployer)
    techdoc = reports.render("techdoc", assessment)[2]
    declaration = reports.render("doc", assessment)[2]
    monitoring = reports.render("monitoring", assessment)[2]
    assert "Art. 11 is a provider obligation" in techdoc
    assert "Drawing up the DoC is a **provider** obligation" in declaration
    assert "deployer monitoring route in Art. 26" in monitoring


def test_prohibited_report_does_not_recommend_high_risk_conformity_pack():
    a = {
        "eu_market": True,
        "provider_role": "provider",
        "p_social_scoring": True,
        "data_personal": True,
    }
    risk = reports.render("risk", _assessment(a))[2]
    tracker = reports.render("compliance", _assessment(a))[2]
    assert "normal high-risk conformity pack" in risk
    assert "Technical documentation (AI Act Art. 11" not in risk
    assert "not a conformity route" in tracker


def test_registration_uses_current_non_public_list_and_public_deployer_route():
    a = {
        "eu_market": True,
        "provider_role": "deployer",
        "deployer_registration_status": "qualifying",
        "hr_usecases": ["law_enforcement"],
        "hr_does_profiling": True,
    }
    md = reports.render("registration", _assessment(a))[2]
    assert "points **6 and 7**" in md
    assert "Annex III(6)–(8)" not in md
    assert "select the provider-registered system" in md
    assert "If the system is not registered, do not use it" in md
    assert "registered at national level under Art. 49(5)" in md


def test_sector_label_alone_does_not_establish_public_legal_status():
    a = {
        "eu_market": True,
        "provider_role": "deployer",
        "org_sector": "public_sector",
        "hr_usecases": ["employment"],
    }
    risk = reports.render("risk", _assessment(a))[2]
    fria = reports.render("fria", _assessment(a))[2]
    registration = reports.render("registration", _assessment(a))[2]
    assert "Fundamental rights impact assessment - FRIA" not in risk
    assert "Not established from the intake" in fria
    assert "status as **unknown**" in registration


def test_string_usecase_is_normalised_in_scope_sensitive_reports():
    a = {
        "eu_market": True,
        "provider_role": "deployer",
        "hr_usecases": "essential_services",
        "hr_essential_subarea": "creditworthiness",
    }
    risk = reports.render("risk", _assessment(a))[2]
    assert "Fundamental rights impact assessment - FRIA" in risk


def test_annex_i_section_b_does_not_receive_ordinary_high_risk_pack():
    a = {
        "eu_market": True,
        "provider_role": "provider",
        "hr_annex_i_relation": "ai_product",
        "hr_annex_i_section": "B",
        "hr_third_party_health_safety": True,
    }
    assessment = _assessment(a)
    cls = assessment["classification"]
    assert cls["tier"] == "high"
    assert "limited Annex I Section B regime" in cls["applicability"]["what"]
    assert cls["high_risk_obligations"] == []
    assert cls["recommended_artifacts"] == [
        "AI risk assessment report",
        "Annex I Section B applicability record (AI Act Art. 2(2))",
        "AI security assessment (OWASP LLM Top 10 + MITRE ATLAS)",
    ]
    risk = reports.render("risk", assessment)[2]
    datagov = reports.render("datagov", assessment)[2]
    registration = reports.render("registration", assessment)[2]
    dpia = reports.render("dpia", assessment)[2]
    techdoc = reports.render("techdoc", assessment)[2]
    declaration = reports.render("doc", assessment)[2]
    tracker = reports.render("compliance", assessment)[2]
    monitoring = reports.render("monitoring", assessment)[2]
    assert "Section B scope limitation" in risk
    assert "ordinary Chapter III high-risk requirements" in risk
    assert "Not applicable through the Annex I Section B route" in datagov
    assert "not an Annex I-only route" in registration
    assert "does not apply Arts. 10, 13, 27" in dpia
    assert "do not infer an AI Act FRIA" in dpia
    assert "does not apply Art. 11" in techdoc
    assert "does not apply Art. 47" in declaration
    assert "Art. 99 penalty table do not apply" in tracker
    assert "## Penalties (Art. 99)" not in tracker
    assert "does not apply Art. 72" in monitoring


def test_annex_i_section_b_excludes_art5_and_art50_system_duties():
    a = {
        "eu_market": True,
        "provider_role": "provider",
        "hr_annex_i_relation": "ai_product",
        "hr_annex_i_section": "B",
        "hr_third_party_health_safety": True,
        "p_social_scoring": True,
        "t_interacts_humans": True,
    }
    cls = classify(a)
    assert cls["tier"] == "high"
    assert all(f["tier"] == "high" for f in cls["findings"])
    assert cls["transparency_obligations"] == []
    assert "Art. 5" not in " | ".join(cls["recommended_artifacts"])


def test_scope_and_safety_questions_reflect_current_statutory_tests():
    questions = {
        q["id"]: q
        for section in QUESTIONNAIRE["sections"]
        for q in section["questions"]
    }
    assert "output is used in the Union" in questions["eu_market"]["help"]
    assert "Mere effects" in questions["eu_market"]["help"]
    assert "property" in questions["hr_safety_function"]["label"]
    assert "property" in questions["hr_failure_endangers_health_safety"]["label"]


def test_annex_i_section_a_surfaces_art2_13_delegated_act_check():
    a = {
        "eu_market": True,
        "provider_role": "both",
        "hr_annex_i_relation": "ai_product",
        "hr_annex_i_section": "A",
        "hr_third_party_health_safety": True,
    }
    cls = classify(a)
    assert cls["tier"] == "high"
    assert "Art. 2(13)" in cls["findings"][0]["rationale"]
    refs = {ref for ref, _desc in cls["high_risk_obligations"]}
    assert "Art. 27" not in refs
    assert "Art. 49" not in refs
