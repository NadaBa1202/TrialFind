"""
Turns unresolved (insufficient_information) criteria into specific, plain-English
follow-up questions — built entirely from data the judgment/matching layers already
produced. No additional LLM call.
"""

from __future__ import annotations

from .numeric_extraction import find_measure


def generate_followup_question(item: dict) -> str:
    measure = item.get("criterion_measure_required")
    criterion_text = item["criterion"]
    reasoning = item.get("reasoning", "")

    if item.get("ambiguous_mention_detected"):
        phrase = item["ambiguous_mention_detected"][0]
        suggested = item.get("suggested_test")
        if suggested:
            return (f"You mentioned \"{phrase}\" — this trial needs a "
                     f"{suggested.upper()} score specifically. Was that the test the patient "
                     f"took, and if so, what was the score?")
        return (f"You mentioned \"{phrase}\" — this trial needs a specific test result "
                 f"({measure or 'a named test'}). Could you confirm which test was used "
                 f"for the patient and the score?")

    if "contradict" in reasoning.lower() or "conflict" in reasoning.lower():
        return (f"There's something unclear in what you shared about \"{criterion_text}\" — "
                f"{reasoning} Could you clarify which is accurate?")

    # "Tell us the patient's <measure>" only makes sense for numeric tests. An exclusion like
    # "History of cerebral ischemia" is a yes/no question, whatever the LLM called its "measure".
    is_yes_no_exclusion = item.get("section") == "exclusion" and find_measure(criterion_text) is None

    if measure and not is_yes_no_exclusion:
        return (f"To check this trial's requirement — \"{criterion_text}\" — "
                f"could you tell us the patient's {measure}, if you know it?")

    if item.get("section") == "exclusion":
        return (f"This trial does not accept patients with the following: \"{criterion_text}\". "
                f"Does this apply to the patient?")

    return f"Can you tell me anything about this requirement: \"{criterion_text}\"?"


def generate_followup_questions(assess_result: dict) -> list[str]:
    return [generate_followup_question(item) for item in assess_result["unclear_criteria"]]
