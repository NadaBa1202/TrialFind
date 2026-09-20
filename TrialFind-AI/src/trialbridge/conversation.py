"""
Stateless conversational step function.

Design principle: this function has NO memory of previous calls. Given the patient
record + the full persisted conversation (see profile_builder.build_profile) plus the
trial's criteria, it recomputes the ENTIRE eligibility picture from scratch every time.

This is deliberate, not a missed optimization: the backend persists just the messages
(each assistant message remembers which criterion it asked about) and can resume from any
point — including after a crash or a cut-off session — by re-running this function.

Returns one of two statuses per call, matching a real conversation turn:

  status "need_more_info": one specific follow-up question, nothing more asked yet.

  status "final", with verdict:
    "not_eligible"     a single not_eligible criterion was found — fail-fast, no further
                       questions needed once the trial is already disqualified.
    "eligible"         every criterion resolved eligible.
    "likely_eligible"  nothing rules the patient out, but the remaining unresolved criteria
                       are ones the caregiver cannot answer ("I don't know", or already asked
                       twice). Without this outcome the conversation could never end for
                       trials with investigator-judgment or lab-value criteria.
"""

from __future__ import annotations
from typing import Callable, Iterable, Optional, Union

from .pipeline import assess_eligibility
from .followup import generate_followup_question
from .profile_builder import ProfileBundle


def step_eligibility_conversation(
    profile: Union[str, ProfileBundle],
    trial_criteria: list,
    call_llm: Callable[[str], str],
    parse_llm_json: Callable[[str], dict | None],
    skipped_ids: Optional[Iterable[str]] = None,
) -> dict:
    result = assess_eligibility(profile, trial_criteria, call_llm, parse_llm_json)
    skipped = set(skipped_ids or [])

    # Fail-fast: a hard violation ends the conversation immediately.
    if result["overall_verdict"] == "not_eligible":
        return {
            "status": "final",
            "verdict": "not_eligible",
            "result": result,
            "next_question": None,
            "next_criterion_id": None,
        }

    unclear = result["unclear_criteria"]

    if not unclear:
        return {
            "status": "final",
            "verdict": result["overall_verdict"],  # "eligible"
            "result": result,
            "next_question": None,
            "next_criterion_id": None,
        }

    # Never re-ask what the caregiver already said they can't answer (or that we asked twice).
    askable = [c for c in unclear if c.get("criterion_id") not in skipped]

    if not askable:
        return {
            "status": "final",
            "verdict": "likely_eligible",
            "result": result,
            "next_question": None,
            "next_criterion_id": None,
            "pending_criteria": unclear,
        }

    # Ask about exactly ONE criterion, in the trial's own order. This is a simple placeholder,
    # to be replaced by the adaptive question selector.
    next_item = askable[0]
    return {
        "status": "need_more_info",
        "verdict": "unknown",
        "result": result,
        "next_question": generate_followup_question(next_item),
        "next_criterion_id": next_item.get("criterion_id"),
        "criteria_remaining": len(askable),
        "criteria_unanswerable": len(unclear) - len(askable),
    }
