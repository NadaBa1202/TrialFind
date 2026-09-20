"""
The V7 judgment prompt: locked, no few-shot examples (deliberately — see project
notes / README for why examples were removed and what that changed).

The template itself is untouched. Section awareness (inclusion vs exclusion) is added by
framing the CRITERION text passed into it, so the locked prompt does not need re-tuning.
"""

from __future__ import annotations
from .numeric_extraction import numeric_context_line

LLM_PROMPT = """You are evaluating whether a patient satisfies ONE specific clinical trial \
eligibility criterion. Return ONLY a single JSON object — no other text, no markdown, no \
code fences.

Patient profile:
{patient}

Criterion:
{criteria}

Rules — follow these strictly:

1. Only use facts explicitly stated in the patient profile. Never assume or infer a fact \
that isn't written down.

2. If the criterion names a specific test, score, or measurement (e.g. MoCA, CDR, a lab \
value) and the profile does not report a result for that EXACT test, the verdict is \
"insufficient_information" — a different, similar-sounding test is never substitutable \
(e.g. MMSE is not MoCA, they are different instruments with different scales).

3. If the criterion requires human judgment (e.g. "in the opinion of the investigator") and \
the profile doesn't already contain that judgment, the verdict is "insufficient_information" \
— you are not the investigator.

4. Classify the relationship between the profile and the criterion into exactly one of three \
buckets, and let the verdict follow directly from the bucket:

   BUCKET A — DIRECT, UNAMBIGUOUS EVIDENCE. The profile contains either (i) a number, \
diagnosis, or fact that plainly satisfies or violates the criterion, or (ii) a negation broad \
enough to cover the criterion (e.g. "no medications of any kind" covers any single drug \
class; "denies any neurological diagnoses" covers any specific neurological condition). A \
negation scoped more narrowly than the criterion (e.g. "no medications for condition X") does \
NOT count as bucket A for a criterion about a different condition. \
-> verdict is "eligible" or "not_eligible", whichever the evidence supports.

   BUCKET B — ABSENT, UNCONFIRMED, OR MERELY SUSPECTED. The profile never addresses the \
topic at all, OR addresses it only through a pending workup, a screening result, a family/ \
self-report without formal diagnosis, or similar signals that a determination has not yet \
been made. Undiagnosed is not the same as ruled out. \
-> verdict is "insufficient_information".

   BUCKET C — INTERNALLY CONTRADICTORY. Two or more facts in the profile relevant to this \
criterion conflict with each other (e.g. a diagnostic label says "no impairment" while a \
reported score indicates impairment; or a reported medication status conflicts with a \
separate statement about that medication). Do not silently pick one fact and ignore the \
other, and do not let a parsed numeric value alone override a contradiction — if any other \
statement in the profile conflicts with what a number would suggest, this is bucket C. \
-> verdict is "insufficient_information", and your reasoning must name both conflicting facts.

5. A false "eligible" is the worst possible error. A false "not_eligible" built from bucket B \
or C evidence (rather than genuine bucket A evidence) is also a serious error — do not \
manufacture certainty the profile doesn't contain.

Return exactly this JSON shape:
{{
  "verdict": "eligible" | "not_eligible" | "insufficient_information",
  "criterion_measure_required": "<short name of what the criterion asks for, e.g. 'MMSE score'>",
  "criterion_measure_found_in_profile": "<short quote/paraphrase of what the profile says about it, or null if nothing relevant is mentioned>",
  "reasoning": "<1-3 sentences, referencing specific facts from the profile and the criterion text, and naming the bucket (A/B/C) if relevant>"
}}"""

VARIANTS = {
    "LLM_PROMPT": LLM_PROMPT,
}


def frame_criterion(text: str, section: str) -> str:
    """
    The V7 prompt asks "does the patient satisfy this criterion?". That question only makes
    sense for INCLUSION criteria. For an EXCLUSION criterion ("History of cerebral ischemia")
    a patient who HAS the condition must come out not_eligible, so we state the direction
    explicitly instead of letting the model guess it.
    """
    if section == "exclusion":
        return (
            "[EXCLUSION criterion] Patients who meet the condition below must be excluded.\n"
            f"  Condition: \"{text}\"\n"
            "  For this criterion: if the profile shows the patient MEETS the condition, the "
            "verdict is \"not_eligible\"; if the profile clearly shows the patient does NOT meet "
            "it, the verdict is \"eligible\"; otherwise apply the rules above (buckets A/B/C)."
        )
    return text


def build_prompt(
    template: str,
    patient: str,
    criteria_list: list[str],
    section: str = "inclusion",
    numeric_profile: str | None = None,
) -> str:
    """
    patient          text shown to the LLM
    numeric_profile  text the regex arithmetic reads (defaults to `patient`); kept separate
                     because the LLM transcript contains questions, which regex must not read.
    """
    criteria_text = "\n".join(f"- {frame_criterion(c, section)}" for c in criteria_list)

    if len(criteria_list) == 1:
        source = numeric_profile if numeric_profile is not None else patient
        extra = numeric_context_line(criteria_list[0], source, section)
        if extra:
            patient = f"{patient}\n\n{extra}"

    return template.format(patient=patient, criteria=criteria_text)
