"""
Run on Kaggle, after `load_model()`. Imports the locked V7 prompt from the package
instead of redefining it — the package is the single source of truth now, the
notebook is just a runner.

Usage (in a Kaggle notebook cell):
    import sys; sys.path.insert(0, "/kaggle/working/trialbridge/src")
    from trialbridge.llm import load_model, call_llm, parse_llm_json
    from trialbridge.prompts import build_prompt, VARIANTS
    load_model()
    exec(open("/kaggle/working/trialbridge/eval/run_eval.py").read())
"""

import json
from collections import defaultdict

with open("eval_dev.json") as f:
    eval_dev = json.load(f)

results = []
for example in eval_dev:
    prompt = build_prompt(VARIANTS["LLM_PROMPT"], example["patient"], [example["criterion"]])
    raw = call_llm(prompt)
    prediction = parse_llm_json(raw)
    results.append({"id": example["id"], "expected": example, "prediction": prediction})

n_total = len(results)
n_parsed = sum(1 for r in results if r["prediction"] is not None)
n_correct = sum(
    1 for r in results
    if r["prediction"] and r["prediction"]["verdict"] == r["expected"]["expected_verdict"]
)

print(f"n_total={n_total} n_parsed={n_parsed} n_unparseable={n_total - n_parsed}")
print(f"verdict_accuracy (unparsed counted as wrong) = {n_correct / n_total:.2%}")

with open("evaluation_results.json", "w") as f:
    json.dump(results, f, indent=2)
