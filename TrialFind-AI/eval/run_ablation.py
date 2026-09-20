"""
Ablation test: same free-text inputs, run through TWO paths:

  A) "raw" — build_prompt(V7) directly on the raw free text, no deterministic
     extraction, no RAG. This simulates what your pipeline looked like BEFORE
     today's numeric_extraction / drug_extraction / measure_matching work.

  B) "pipeline" — the full assess_eligibility path (deterministic pre-processing
     + RAG tiers + V7).

Comparing A vs B on the SAME inputs is what actually measures whether today's
work improved anything — running the old templated eval_dev.json again would not,
since that data never exercises the RAG tiers at all (see conversation notes).

Run on Kaggle, after load_model().
"""

import json
import sys

with open("eval_dev_freetext.json") as f:
    cases = json.load(f)


def run_raw(call_llm, parse_llm_json, build_prompt, VARIANTS, cases):
    results = []
    for c in cases:
        prompt = build_prompt(VARIANTS["LLM_PROMPT"], c["patient"], [c["criterion"]])
        raw = call_llm(prompt)
        pred = parse_llm_json(raw)
        results.append({
            "id": c["id"],
            "expected": c["expected_verdict"],
            "got": pred["verdict"] if pred else "UNPARSEABLE",
        })
    return results


def run_pipeline(call_llm, parse_llm_json, assess_eligibility, cases):
    results = []
    for c in cases:
        result = assess_eligibility(c["patient"], [c["criterion"]], call_llm=call_llm, parse_llm_json=parse_llm_json)
        got = result["details"][0]["verdict"]
        results.append({"id": c["id"], "expected": c["expected_verdict"], "got": got})
    return results


def score(results):
    correct = sum(1 for r in results if r["got"] == r["expected"])
    return correct, len(results)


def print_comparison(raw_results, pipeline_results):
    print(f"{'ID':<10} {'expected':<25} {'RAW':<25} {'PIPELINE':<25}")
    for r_raw, r_pipe in zip(raw_results, pipeline_results):
        assert r_raw["id"] == r_pipe["id"]
        flag = ""
        if r_raw["got"] != r_raw["expected"] and r_pipe["got"] == r_pipe["expected"]:
            flag = "  <- pipeline fixed this"
        elif r_raw["got"] == r_raw["expected"] and r_pipe["got"] != r_pipe["expected"]:
            flag = "  <- pipeline REGRESSED this"
        print(f"{r_raw['id']:<10} {r_raw['expected']:<25} {r_raw['got']:<25} {r_pipe['got']:<25}{flag}")

    raw_correct, total = score(raw_results)
    pipe_correct, _ = score(pipeline_results)
    print(f"\nRAW accuracy:      {raw_correct}/{total} = {raw_correct/total:.1%}")
    print(f"PIPELINE accuracy: {pipe_correct}/{total} = {pipe_correct/total:.1%}")


if __name__ == "__main__":
    # Expects these to already be imported in the notebook namespace before exec():
    # call_llm, parse_llm_json, build_prompt, VARIANTS, assess_eligibility
    raw_results = run_raw(call_llm, parse_llm_json, build_prompt, VARIANTS, cases)
    pipeline_results = run_pipeline(call_llm, parse_llm_json, assess_eligibility, cases)
    print_comparison(raw_results, pipeline_results)
