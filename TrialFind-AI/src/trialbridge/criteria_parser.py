"""
ClinicalTrials.gov's eligibilityCriteria field is one free-text blob, usually
shaped like:

    Inclusion Criteria:

    * criterion one
    * criterion two

    Exclusion Criteria:

    * criterion three

But it's inconsistent across trials: some use numbered lists (1. 2. 3.),
some have no bullet markers at all, some nest sub-bullets, some skip the
Exclusion section entirely. This parser handles the common cases and is
deliberately conservative — if it can't confidently split a line, it keeps
it as one block rather than guessing where to cut, since a bad split here
corrupts every downstream verdict.
"""

import re
from dataclasses import dataclass


@dataclass
class Criterion:
    id: str
    section: str  # "inclusion" | "exclusion"
    text: str


_BULLET_RE = re.compile(r"^\s*(?:[\*\-•]|\d+[\.\)])\s+", re.MULTILINE)
_INCLUSION_HEADER_RE = re.compile(r"inclusion\s+criteria\s*:?", re.IGNORECASE)
_EXCLUSION_HEADER_RE = re.compile(r"exclusion\s+criteria\s*:?", re.IGNORECASE)


def parse_eligibility_criteria(raw_text: str) -> list[Criterion]:
    if not raw_text or not raw_text.strip():
        return []

    excl_match = _EXCLUSION_HEADER_RE.search(raw_text)
    if excl_match:
        inclusion_block = raw_text[: excl_match.start()]
        exclusion_block = raw_text[excl_match.end():]
    else:
        inclusion_block = raw_text
        exclusion_block = ""

    inclusion_block = _INCLUSION_HEADER_RE.sub("", inclusion_block)

    criteria: list[Criterion] = []
    criteria.extend(_split_block(inclusion_block, "inclusion"))
    criteria.extend(_split_block(exclusion_block, "exclusion"))
    return criteria


def _split_block(block: str, section: str) -> list[Criterion]:
    block = block.strip()
    if not block:
        return []

    if _BULLET_RE.search(block):
        # split on bullet markers, drop empty fragments
        parts = _BULLET_RE.split(block)
        lines = [p.strip().replace("\n", " ") for p in parts if p.strip()]
    else:
        # no bullets found — fall back to splitting on blank lines/sentences
        lines = [l.strip() for l in block.split("\n") if l.strip()]

    # collapse multiple internal whitespace
    lines = [re.sub(r"\s+", " ", l) for l in lines]

    out = []
    for i, line in enumerate(lines, start=1):
        out.append(Criterion(id=f"{section}_{i}", section=section, text=line))
    return out


if __name__ == "__main__":
    # smoke test against the real eligibilityCriteria blob pulled from
    # ClinicalTrials.gov NCT06793735 (TeleVR study, includes Alzheimer's cohort)
    sample = """Inclusion Criteria:

* Subjects diagnosed with MCI (AD and PD) according to the criteria of the National Institute on Aging-Alzheimer's Association (NIA-AA, Albert et al., 2011)
* Subjects diagnosed with SCD according to diagnostic criteria proposed in research settings (Molinuevo et al., 2017)
* All enrolled subjects must be aged between 40 and 80 years and have at least 5 years of education

Exclusion Criteria:

* Presence of psychiatric disorders (major depression, psychosis, anxiety disorders)
* Presence of severe dementia
* History of cerebral ischemia
* Contraindications to brain MRI: pregnant women, pacemakers, non-latest-generation metal joint prostheses, electrodes, neurostimulators, or prostheses that may interfere with magnetic fields, unless there is a written statement of suitability from the specialist who performed the intervention"""

    parsed = parse_eligibility_criteria(sample)
    for c in parsed:
        print(f"[{c.id}] ({c.section}) {c.text}")