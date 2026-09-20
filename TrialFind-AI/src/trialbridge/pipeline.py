"""
The single entry point that wires every stage together:

  patient record + conversation --> build_profile (profile_builder: safe text views)
            --> drug/negation extraction (on caregiver statements only, never on our questions)
            --> per criterion: check_measure_mention (deterministic + RAG tier)
                  --> if ambiguous: stop here, no LLM call, flag for follow-up
                  --> else: build_prompt (section-aware, + numeric_context_line) --> call_llm --> parse
            --> aggregate_trial_verdict (deterministic rollup)

Only ONE step in this whole function calls the LLM: judging a criterion that survived
the deterministic + RAG pre-checks. Everything else is testable without a GPU.

Criteria are dicts {"id", "section", "text"}. Plain strings are still accepted (treated as
inclusion criteria with generated ids) so old callers/notebooks keep working.
"""

from __future__ import annotations
from typing import Callable, Union

from .drug_extraction import build_parsed_lines
from .measure_matching import check_measure_mention
from .profile_builder import ProfileBundle
from .prompts import build_prompt, VARIANTS
from .rollup import aggregate_trial_verdict

VALID_VERDICTS = {"eligible", "not_eligible", "insufficient_information"}


def normalize_criteria(trial_criteria: list) -> list[dict]:
    out = []
    for i, c in enumerate(trial_criteria, start=1):
        if isinstance(c, str):
            out.append({"id": f"criterion_{i}", "section": "inclusion", "text": c})
        else:
            out.append({
                "id": c.get("id") or f"criterion_{i}",
                "section": c.get("section", "inclusion"),
                "text": c["text"],
            })
    return out


def assess_eligibility(
    profile: Union[str, ProfileBundle],
    trial_criteria: list,
    call_llm: Callable[[str], str],
    parse_llm_json: Callable[[str], dict | None],
) -> dict:
    """
    call_llm / parse_llm_json are passed in rather than imported directly, so this
    function has zero hard dependency on the GPU-only llm.py module — it can be
    exercised in tests with a fake call_llm that returns canned JSON strings.
    """
    bundle = ProfileBundle.from_plain_text(profile) if isinstance(profile, str) else profile
    criteria = normalize_criteria(trial_criteria)

    # Drug scan reads caregiver statements + registration background only.
    parsed_lines = build_parsed_lines(bundle.scan_text)
    llm_profile = "\n".join([bundle.llm_text.strip()] + parsed_lines)

    criterion_results = []
    for c in criteria:
        base = {"criterion_id": c["id"], "section": c["section"], "criterion": c["text"]}

        tier, *rest = check_measure_mention(
            c["text"], bundle.rules_text, statements_text=bundle.statements_text
        )

        if tier == "ambiguous":
            phrase, suggested_test = rest
            criterion_results.append({
                **base,
                "verdict": "insufficient_information",
                "reasoning": f"Profile mentions \"{phrase}\", which may refer to "
                             f"{suggested_test.upper()}, but this isn't confirmed as the "
                             f"exact test the criterion requires.",
                "criterion_measure_required": c["text"],
                "ambiguous_mention_detected": [phrase],
                "suggested_test": suggested_test,
            })
            continue

        prompt = build_prompt(
            VARIANTS["LLM_PROMPT"],
            llm_profile,
            [c["text"]],
            section=c["section"],
            numeric_profile=bundle.rules_text,
        )
        prediction = parse_llm_json(call_llm(prompt))

        verdict = prediction.get("verdict") if isinstance(prediction, dict) else None
        if verdict not in VALID_VERDICTS:
            # unparseable / off-schema output must never crash the turn or become "eligible"
            criterion_results.append({
                **base,
                "verdict": "insufficient_information",
                "reasoning": "Could not parse model output.",
                "criterion_measure_required": None,
            })
            continue

        criterion_results.append({
            **base,
            "verdict": verdict,
            "reasoning": prediction.get("reasoning", ""),
            "criterion_measure_required": prediction.get("criterion_measure_required"),
        })

    return aggregate_trial_verdict(criterion_results)
