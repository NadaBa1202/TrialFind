"""
Deterministic aggregation of per-criterion verdicts into one trial-level verdict.
Any single not_eligible vetoes the trial, regardless of how many other criteria
passed — matches the "a false eligible is the worst error" principle from the
judgment prompt.
"""

from __future__ import annotations


def aggregate_trial_verdict(criterion_results: list[dict]) -> dict:
    verdicts = [r["verdict"] for r in criterion_results]

    if "not_eligible" in verdicts:
        overall = "not_eligible"
    elif "insufficient_information" in verdicts:
        overall = "unknown"
    else:
        overall = "eligible"

    return {
        "overall_verdict": overall,
        "criteria_evaluated": len(criterion_results),
        "blocking_criteria": [r for r in criterion_results if r["verdict"] == "not_eligible"],
        "unclear_criteria": [r for r in criterion_results if r["verdict"] == "insufficient_information"],
        "details": criterion_results,
    }
