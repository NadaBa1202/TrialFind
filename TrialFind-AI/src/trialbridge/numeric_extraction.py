"""
Lightweight symbolic pre-pass for numeric-range criteria (age, MMSE, CDR, MoCA, labs...).

Design goal: don't ask the LLM to parse "18-26 inclusive" and compare it to "MMSE: 22"
by eyeballing text — that's exactly the kind of arithmetic LLMs fumble. Instead, parse
both sides with regex, compute the comparison in Python, and hand the LLM the *result*
as a fact it can use. The LLM still issues the final verdict, so it can still catch
contradictions (e.g. a diagnosis label that conflicts with the number) — this module
only removes the "can it do range math correctly" failure mode, not the judgment step.

Important: if no value is found, this module says NOTHING rather than asserting a false
negative — silence lets the LLM read the raw profile text itself (which may phrase the
value in a way this regex doesn't catch), rather than being told "not found" when it may
just be unrecognized.

Changes in this version:
  * Section-aware: for an EXCLUSION criterion, "within range" means the patient MEETS the
    exclusion condition (=> would be excluded). Previously every criterion was treated as
    an inclusion range.
  * "aged 40 to 80" / "between 40 and 80" are now parsed (previously only "40-80"/"40 to 80"
    and only the exact word "age").
  * A profile line may carry a context tag " [re: MMSE]" (added by profile_builder when the
    caregiver answered a targeted question with a bare number, e.g. "22"). The tag is used
    to recognise WHICH measure the number belongs to, but the number itself is only ever
    read from the part of the line BEFORE the tag.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

# Separator between a caregiver's answer and the measure it answers. Shared with profile_builder.
CONTEXT_MARK = " [re: "

MEASURE_ALIASES = {
    "age": [r"\bages?\b", r"\baged\b"],
    "mmse": [r"\bmmse\b"],
    "cdr": [r"\bcdr\b", r"\bclinical dementia rating\b"],
    "moca": [r"\bmoca\b", r"\bmontreal cognitive assessment\b"],
}

_NUM = r"(\d+(?:\.\d+)?)"


@dataclass
class NumericBound:
    measure: str
    low: Optional[float]
    high: Optional[float]


@dataclass
class NumericFinding:
    measure: str
    value: float
    raw_line: str


def _find_measure(text: str) -> Optional[str]:
    text = text.lower()
    for measure, patterns in MEASURE_ALIASES.items():
        if any(re.search(p, text) for p in patterns):
            return measure
    return None


def find_measure(text: str) -> Optional[str]:
    """Public alias — which known measure (age/mmse/cdr/moca) does this text mention, if any."""
    return _find_measure(text)


def extract_criterion_bound(criterion_text: str) -> Optional[NumericBound]:
    measure = _find_measure(criterion_text)
    if measure is None:
        return None

    t = criterion_text.lower()

    # "between 40 and 80" — checked first so a later "at least 5 years of education"
    # in the same sentence can't hijack the bound.
    m = re.search(rf"between\s+{_NUM}\s*(?:and|to|-|–)\s*{_NUM}", t)
    if m:
        return NumericBound(measure, float(m.group(1)), float(m.group(2)))

    m = re.search(rf"{_NUM}\s*(?:-|to|–)\s*{_NUM}", t)
    if m:
        return NumericBound(measure, float(m.group(1)), float(m.group(2)))

    m = re.search(rf"(?:>=|greater than or equal to|at least|minimum(?: of)?)\s*{_NUM}", t)
    if m:
        return NumericBound(measure, float(m.group(1)), None)

    m = re.search(rf"(?:<=|less than or equal to|at most|maximum(?: of)?)\s*{_NUM}", t)
    if m:
        return NumericBound(measure, None, float(m.group(1)))

    return None


def extract_profile_value(profile_text: str, measure: str) -> Optional[NumericFinding]:
    patterns = MEASURE_ALIASES.get(measure, [])
    for line in profile_text.splitlines():
        low = line.lower()
        if any(re.search(p, low) for p in patterns):
            # Read the number only from the answer part, never from the context tag.
            answer_part = line.split(CONTEXT_MARK)[0]
            m = re.search(_NUM, answer_part)
            if m:
                return NumericFinding(measure, float(m.group(1)), answer_part.strip())

    # Conversational fallback for age specifically ("I'm 72 years old")
    if measure == "age":
        m = re.search(r"\b(\d{1,3})\s*(?:years?\s*old|y/?o\b)", profile_text.lower())
        if m:
            return NumericFinding("age", float(m.group(1)), m.group(0))

    return None


def numeric_context_line(
    criterion_text: str, profile_text: str, section: str = "inclusion"
) -> Optional[str]:
    bound = extract_criterion_bound(criterion_text)
    if bound is None:
        return None

    finding = extract_profile_value(profile_text, bound.measure)
    if finding is None:
        return None  # say nothing rather than assert a false "not found"

    in_range = True
    if bound.low is not None and finding.value < bound.low:
        in_range = False
    if bound.high is not None and finding.value > bound.high:
        in_range = False

    lo = bound.low if bound.low is not None else "-inf"
    hi = bound.high if bound.high is not None else "+inf"

    if section == "exclusion":
        # For an exclusion criterion the range describes who gets EXCLUDED.
        outcome = (
            "WITHIN the excluded range, i.e. the patient MEETS this exclusion condition"
            if in_range
            else "OUTSIDE the excluded range, i.e. the patient does NOT meet this exclusion condition"
        )
        range_label = "excluded range"
    else:
        outcome = "WITHIN RANGE" if in_range else "OUTSIDE RANGE"
        range_label = "required range"

    return (
        f"Parsed check (arithmetic only, not a verdict): {bound.measure.upper()} = {finding.value} "
        f"(from: \"{finding.raw_line}\"), {range_label} [{lo}, {hi}] -> {outcome}. "
        f"This number alone does NOT determine the verdict. You must still check the rest of "
        f"the profile for anything that contradicts this number before finalizing your verdict."
    )
