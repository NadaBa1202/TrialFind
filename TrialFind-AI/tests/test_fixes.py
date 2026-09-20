"""
Tests for the 6 fixes. No GPU, no model download: the LLM is a fake and the embedding
retriever is stubbed out (semantic matching is not what is being tested here).

Run from the folder that contains the `trialbridge/` package:
    pip install pytest fastapi httpx
    pytest tests -q
"""
import json
import os
import pathlib
import sys

os.environ["TRIALFIND_FAKE_LLM"] = "1"  # must be set before trialbridge.api is imported
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from trialbridge import retrieval
from trialbridge.conversation import step_eligibility_conversation
from trialbridge.llm import parse_llm_json
from trialbridge.numeric_extraction import extract_profile_value
from trialbridge.pipeline import assess_eligibility
from trialbridge.profile_builder import Turn, build_profile


@pytest.fixture(autouse=True)
def no_embeddings(monkeypatch):
    monkeypatch.setattr(retrieval.SmallCorpusRetriever, "best_match",
                        lambda self, phrase, threshold=0.55: None)


class FakeLLM:
    def __init__(self, rule=None):
        self.prompts = []
        self.rule = rule

    def __call__(self, prompt):
        self.prompts.append(prompt)
        verdict = self.rule(prompt) if self.rule else "insufficient_information"
        return json.dumps({"verdict": verdict, "criterion_measure_required": "x", "reasoning": "r"})


def crit(id_, section, text):
    return {"id": id_, "section": section, "text": text}


# ---------------------------------------------------------------- fix 1: exclusion criteria
def test_exclusion_criterion_is_framed_and_flips_verdict():
    criteria = [crit("exclusion_1", "exclusion", "History of cerebral ischemia")]
    bundle = build_profile("Age: 72 years old.", [Turn("caregiver", "She had a stroke in 2019, cerebral ischemia")], criteria)

    def rule(prompt):
        assert "[EXCLUSION criterion]" in prompt
        return "not_eligible"

    llm = FakeLLM(rule)
    result = assess_eligibility(bundle, criteria, llm, parse_llm_json)
    assert result["overall_verdict"] == "not_eligible"
    assert "MEETS the condition" in llm.prompts[0]
    assert result["details"][0]["section"] == "exclusion"


def test_inclusion_prompt_is_untouched():
    criteria = [crit("inclusion_1", "inclusion", "Diagnosis of mild Alzheimer's disease")]
    bundle = build_profile("", [Turn("caregiver", "mild Alzheimer's")], criteria)
    llm = FakeLLM()
    assess_eligibility(bundle, criteria, llm, parse_llm_json)
    assert "[EXCLUSION criterion]" not in llm.prompts[0]
    assert "- Diagnosis of mild Alzheimer's disease" in llm.prompts[0]


def test_numeric_check_is_inverted_for_exclusion():
    criteria = [crit("exclusion_1", "exclusion", "MMSE score of 0-10")]
    for mmse, expected in [(22, "does NOT meet this exclusion"), (8, "MEETS this exclusion")]:
        bundle = build_profile("", [Turn("caregiver", f"MMSE is {mmse}")], criteria)
        llm = FakeLLM()
        assess_eligibility(bundle, criteria, llm, parse_llm_json)
        assert expected in llm.prompts[0], llm.prompts[0]


# ---------------------------------------------------------------- fix 2: follow-up question
def test_step_returns_a_followup_question():
    criteria = [crit("inclusion_1", "inclusion", "MoCA score between 18 and 26")]
    bundle = build_profile("", [Turn("caregiver", "She has memory problems")], criteria)
    step = step_eligibility_conversation(bundle, criteria, FakeLLM(), parse_llm_json)
    assert step["status"] == "need_more_info"
    assert step["next_question"]
    assert step["next_criterion_id"] == "inclusion_1"


def test_exclusion_question_reads_naturally():
    criteria = [crit("exclusion_1", "exclusion", "History of cerebral ischemia")]
    bundle = build_profile("", [Turn("caregiver", "She has memory problems")], criteria)
    step = step_eligibility_conversation(bundle, criteria, FakeLLM(), parse_llm_json)
    assert "does not accept patients" in step["next_question"]


def test_bad_llm_output_never_crashes_or_becomes_eligible():
    criteria = [crit("inclusion_1", "inclusion", "Diagnosis of Alzheimer's disease")]
    bundle = build_profile("", [Turn("caregiver", "Alzheimer's")], criteria)
    for raw in ["garbage", '{"verdict": "maybe"}', '{"reasoning": "no verdict key"}', "[]"]:
        result = assess_eligibility(bundle, criteria, lambda p, raw=raw: raw, parse_llm_json)
        assert result["overall_verdict"] == "unknown"


# ---------------------------------------------------------------- fix 4: question/answer pairs
def test_short_answer_keeps_its_question_for_the_llm():
    criteria = [crit("exclusion_1", "exclusion", "Current use of anticoagulants")]
    turns = [Turn("assistant", "Is the patient taking any blood thinners?", "exclusion_1"),
             Turn("caregiver", "No")]
    bundle = build_profile("", turns, criteria)
    assert "Q: Is the patient taking any blood thinners?\nA: No" in bundle.llm_text


def test_bare_number_answer_is_tied_to_its_measure():
    criteria = [crit("inclusion_1", "inclusion", "MMSE score between 18 and 26")]
    turns = [Turn("assistant", "Could you tell us the patient's MMSE score?", "inclusion_1"),
             Turn("caregiver", "22")]
    bundle = build_profile("", turns, criteria)
    assert "22 [re: MMSE]" in bundle.rules_text
    assert extract_profile_value(bundle.rules_text, "mmse").value == 22.0

    llm = FakeLLM()
    assess_eligibility(bundle, criteria, llm, parse_llm_json)
    assert "WITHIN RANGE" in llm.prompts[0]


def test_context_tag_never_leaks_a_number_from_the_question():
    criteria = [crit("inclusion_1", "inclusion", "MMSE score between 18 and 26")]
    turns = [Turn("assistant", "What is the MMSE score (range 18-26)?", "inclusion_1"),
             Turn("caregiver", "not sure, maybe 3 months ago")]
    bundle = build_profile("", turns, criteria)
    finding = extract_profile_value(bundle.rules_text, "mmse")
    assert finding is None or finding.value == 3.0  # never 18 or 26 (they only exist in the question)


def test_intro_question_does_not_create_fake_measures():
    criteria = [crit("inclusion_1", "inclusion", "MMSE score between 18 and 26")]
    turns = [Turn("assistant", "Tell me about diagnosis and scores (e.g. MMSE/MoCA/CDR)"),
             Turn("caregiver", "She is 72 years old")]
    bundle = build_profile("", turns, criteria)
    assert extract_profile_value(bundle.rules_text, "mmse") is None


def test_our_own_question_is_not_scanned_as_a_drug_mention():
    criteria = [crit("exclusion_1", "exclusion", "Current use of anticoagulants")]
    turns = [Turn("assistant", "Is the patient taking any blood thinners?", "exclusion_1"),
             Turn("caregiver", "No")]
    bundle = build_profile("", turns, criteria)
    llm = FakeLLM()
    assess_eligibility(bundle, criteria, llm, parse_llm_json)
    assert "[Parsed]" not in llm.prompts[0]


# ---------------------------------------------------------------- fix 5: no endless loop
def _ask(cid, text="q?"):
    return Turn("assistant", text, cid)


def test_dont_know_is_never_asked_again_and_conversation_can_end():
    criteria = [crit("inclusion_1", "inclusion", "CDR score of 0.5-1"),
                crit("inclusion_2", "inclusion", "MoCA score between 18 and 26")]
    turns = [Turn("caregiver", "She has Alzheimer's")]

    step = step_eligibility_conversation(build_profile("", turns, criteria), criteria, FakeLLM(), parse_llm_json)
    assert step["next_criterion_id"] == "inclusion_1"

    turns += [_ask("inclusion_1"), Turn("caregiver", "I don't know")]
    bundle = build_profile("", turns, criteria)
    assert bundle.unaskable_ids == {"inclusion_1"}
    step = step_eligibility_conversation(bundle, criteria, FakeLLM(), parse_llm_json, bundle.unaskable_ids)
    assert step["next_criterion_id"] == "inclusion_2"

    turns += [_ask("inclusion_2"), Turn("caregiver", "not sure")]
    bundle = build_profile("", turns, criteria)
    step = step_eligibility_conversation(bundle, criteria, FakeLLM(), parse_llm_json, bundle.unaskable_ids)
    assert step["status"] == "final" and step["verdict"] == "likely_eligible"
    assert len(step["pending_criteria"]) == 2


def test_criterion_is_asked_at_most_twice():
    criteria = [crit("inclusion_1", "inclusion", "CDR score of 0.5-1")]
    turns = [Turn("caregiver", "x"), _ask("inclusion_1"), Turn("caregiver", "hmm maybe"),
             _ask("inclusion_1"), Turn("caregiver", "hard to say, she is forgetful")]
    assert "inclusion_1" in build_profile("", turns, criteria).unaskable_ids


def test_long_answer_containing_dont_know_is_not_a_skip():
    criteria = [crit("inclusion_1", "inclusion", "CDR score of 0.5-1")]
    turns = [_ask("inclusion_1"),
             Turn("caregiver", "I don't know the CDR but the neurologist told us she has moderate "
                               "Alzheimer's and she scored 15 on the MMSE last spring at the clinic")]
    assert build_profile("", turns, criteria).unaskable_ids == set()


def test_likely_eligible_only_when_nothing_rules_the_patient_out():
    criteria = [crit("inclusion_1", "inclusion", "Diagnosis of Alzheimer's disease"),
                crit("inclusion_2", "inclusion", "Investigator judges the patient suitable")]

    def rule(prompt):
        return "eligible" if "Diagnosis of Alzheimer" in prompt else "insufficient_information"

    turns = [Turn("caregiver", "Alzheimer's"), _ask("inclusion_2"), Turn("caregiver", "no idea")]
    bundle = build_profile("", turns, criteria)
    step = step_eligibility_conversation(bundle, criteria, FakeLLM(rule), parse_llm_json, bundle.unaskable_ids)
    assert (step["status"], step["verdict"]) == ("final", "likely_eligible")

    step = step_eligibility_conversation(bundle, criteria, FakeLLM(lambda p: "not_eligible"), parse_llm_json, bundle.unaskable_ids)
    assert step["verdict"] == "not_eligible"  # a blocker always wins


# ---------------------------------------------------------------- fix 6: Phase 1 data reused
def test_registration_age_resolves_age_criterion():
    criteria = [crit("inclusion_1", "inclusion",
                     "All enrolled subjects must be aged between 40 and 80 years and have at least 5 years of education")]
    for age, expected in [(72, "WITHIN RANGE"), (85, "OUTSIDE RANGE")]:
        bundle = build_profile(f"Age: {age} years old.\nSex: female.", [Turn("caregiver", "mild Alzheimer's")], criteria)
        llm = FakeLLM()
        assess_eligibility(bundle, criteria, llm, parse_llm_json)
        assert expected in llm.prompts[0]
        assert f"AGE = {float(age)}" in llm.prompts[0]


def test_registration_background_reaches_the_llm():
    bundle = build_profile("Age: 72 years old.\nSex: female.", [Turn("caregiver", "x")], [])
    assert "Age: 72 years old." in bundle.llm_text


# ---------------------------------------------------------------- fix 3: HTTP service
def test_api_contract():
    from trialbridge.api import app
    body = {
        "patient_context": "Age: 72 years old.\nSex: female.",
        "turns": [{"role": "CAREGIVER", "content": "She has Alzheimer's"}],
        "criteria": [{"id": "inclusion_1", "section": "inclusion", "text": "MoCA score between 18 and 26"}],
    }
    with TestClient(app) as client:
        assert client.get("/health").json()["ok"] is True
        r = client.post("/eligibility/assess", json=body)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "need_more_info"
        assert data["followup_questions"] == [data["next_question"]]
        assert data["next_criterion_id"] == "inclusion_1"
        assert data["details"][0]["criterion_id"] == "inclusion_1"
        assert "unclear_criteria" in data and "overall_verdict" in data

        # ask it, get "I don't know" -> final likely_eligible, no question
        body["turns"] += [{"role": "ASSISTANT", "content": data["next_question"], "criterion_id": "inclusion_1"},
                          {"role": "CAREGIVER", "content": "I don't know"}]
        data = client.post("/eligibility/assess", json=body).json()
        assert data["status"] == "final" and data["verdict"] == "likely_eligible"
        assert data["next_question"] is None and data["followup_questions"] == []
        assert len(data["pending_criteria"]) == 1


def test_api_key_is_enforced_when_configured(monkeypatch):
    from trialbridge.api import app
    monkeypatch.setenv("AI_SERVICE_KEY", "s3cret")
    body = {"criteria": [{"id": "inclusion_1", "section": "inclusion", "text": "Alzheimer's"}]}
    with TestClient(app) as client:
        assert client.post("/eligibility/assess", json=body).status_code == 401
        assert client.post("/eligibility/assess", json=body, headers={"x-api-key": "nope"}).status_code == 401
        assert client.post("/eligibility/assess", json=body, headers={"x-api-key": "s3cret"}).status_code == 200


def test_api_rejects_bad_section():
    from trialbridge.api import app
    with TestClient(app) as client:
        r = client.post("/eligibility/assess", json={"criteria": [{"id": "a", "section": "other", "text": "x"}]})
        assert r.status_code == 422
