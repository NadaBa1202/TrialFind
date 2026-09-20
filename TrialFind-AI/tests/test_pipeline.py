"""
Runs entirely on a laptop, no GPU, no model download.

Two kinds of tests:
1. Pure deterministic modules (numeric_extraction, drug_extraction, measure_matching,
   intent_router) — tested directly, no mocking needed.
2. pipeline.assess_eligibility — tested with a FAKE call_llm that returns a fixed,
   valid JSON string, so the wiring/rollup logic is checked without ever touching
   gemma-2-9b-it. This does NOT test whether the real model reasons correctly
   (that's what eval/run_eval.py on Kaggle is for) — it only tests that your Python
   plumbing is correct: does the right criterion reach the LLM step, does an
   ambiguous match correctly short-circuit before the LLM step, does rollup combine
   results correctly.

Run with: python -m pytest tests/ -v   (or just `python tests/test_pipeline.py`)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from trialbridge.numeric_extraction import extract_criterion_bound, extract_profile_value, numeric_context_line
from trialbridge.drug_extraction import scan_drug_mentions
from trialbridge.rollup import aggregate_trial_verdict
from trialbridge.pipeline import assess_eligibility


# ---------- deterministic module tests (no LLM involved at all) ----------

def test_numeric_range_in_bounds():
    bound = extract_criterion_bound("MMSE 18-26 inclusive")
    assert bound.low == 18 and bound.high == 26

def test_age_conversational_phrasing():
    finding = extract_profile_value("I'm 72 years old and tired.", "age")
    assert finding is not None and finding.value == 72

def test_numeric_context_line_silent_when_not_found():
    line = numeric_context_line("MMSE 18-26 inclusive", "Diagnosis: unclear")
    assert line is None  # must NOT assert a false "not found" claim

def test_negation_detected():
    findings = scan_drug_mentions("No blood thinners, doctor took me off warfarin a year ago.")
    assert findings[0]["status"] == "discontinued_or_denied"

def test_current_medication_detected():
    findings = scan_drug_mentions("Still taking my warfarin daily.")
    assert findings[0]["status"] == "current"

def test_rollup_any_not_eligible_vetoes():
    result = aggregate_trial_verdict([
        {"verdict": "eligible"}, {"verdict": "not_eligible"}, {"verdict": "eligible"},
    ])
    assert result["overall_verdict"] == "not_eligible"

def test_rollup_unknown_when_unresolved():
    result = aggregate_trial_verdict([{"verdict": "eligible"}, {"verdict": "insufficient_information"}])
    assert result["overall_verdict"] == "unknown"


# ---------- pipeline test with a FAKE LLM (no GPU needed) ----------

def fake_call_llm(prompt: str) -> str:
    # Always "answers eligible" — good enough to test wiring, not reasoning quality.
    return '{"verdict": "eligible", "criterion_measure_required": "test", "reasoning": "fake"}'

def fake_parse_llm_json(raw: str):
    import json
    return json.loads(raw)

def test_pipeline_wiring_reaches_llm_for_clean_criteria():
    result = assess_eligibility(
        "I'm 72 years old.",
        ["Age 50-85 years"],
        call_llm=fake_call_llm,
        parse_llm_json=fake_parse_llm_json,
    )
    assert result["overall_verdict"] == "eligible"

def test_pipeline_short_circuits_on_ambiguous_measure():
    # "memory test" should be caught by check_measure_mention BEFORE reaching fake_call_llm.
    # We confirm this by using a fake_call_llm that would raise if ever called.
    def call_llm_should_not_be_called(prompt):
        raise AssertionError("LLM should not be called for an ambiguous measure mention")

    result = assess_eligibility(
        "Scored a 22 on the memory test.",
        ["MMSE 18-26 inclusive"],
        call_llm=call_llm_should_not_be_called,
        parse_llm_json=fake_parse_llm_json,
    )
    assert result["overall_verdict"] == "unknown"
    assert result["unclear_criteria"][0]["ambiguous_mention_detected"] == ["Scored a 22 on the memory test."]


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"OK  {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed")
