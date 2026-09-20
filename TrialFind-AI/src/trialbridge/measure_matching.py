"""
Resolves whether a profile reports the SPECIFIC measure a criterion requires.

Three tiers, cheapest/most-certain first:
  1. Exact regex match (numeric_extraction.extract_profile_value) — free, certain.
  2. RAG: no exact match, but a sentence is semantically close to a known test name
     (e.g. "scored a 22 on the memory test" ~ MMSE) — flagged as AMBIGUOUS, never
     silently substituted. This is the fix for the "MMSE != memory test" false-eligible
     bug: previously the LLM would guess the substitution itself; now it's caught here,
     deterministically, before the LLM ever sees the criterion.
  3. Nothing found — genuinely insufficient information.
"""

from __future__ import annotations
import re

from .corpora import KNOWN_MEASURES_CORPUS
from .numeric_extraction import extract_criterion_bound, extract_profile_value, find_measure
from .retrieval import SmallCorpusRetriever

_measure_retriever = SmallCorpusRetriever(KNOWN_MEASURES_CORPUS)

# Deterministic backstop for the embedding check. Embedding similarity is unpredictable: a
# caregiver saying "she scored 22 on the memory test" can land just under the threshold, and
# then the LLM is left to decide whether "memory test" is the MoCA the trial requires (it may
# guess "eligible" — the worst possible error). So: a sentence that has a number and talks about
# a test/score but names NO known test is treated as ambiguous, and we simply ask which test it was.
_TEST_TALK_RE = re.compile(
    r"\b(?:tests?|tested|scores?|scored|exams?|examination|assessments?|screening|evaluation)\b",
    re.IGNORECASE,
)


def suggest_matching_test(phrase: str, threshold: float = 0.55):
    match = _measure_retriever.best_match(phrase, threshold=threshold)
    return match.key if match else None


def check_measure_mention(
    criterion_text: str,
    profile_text: str,
    threshold: float = 0.55,
    statements_text: str | None = None,
):
    """
    profile_text     used for the exact regex lookup (may carry " [re: MMSE]" context tags)
    statements_text  caregiver-only text used for the semantic ambiguity check, so the
                     tool's own questions never count as "the caregiver mentioned a test".
                     Defaults to profile_text.

    Returns one of:
      ("exact", NumericFinding)
      ("ambiguous", phrase, suggested_test_key)
      ("none", None)
    """
    required = extract_criterion_bound(criterion_text)
    if required is None:
        return ("none", None)

    exact = extract_profile_value(profile_text, required.measure)
    if exact is not None:
        return ("exact", exact)

    rag_source = statements_text if statements_text is not None else profile_text
    for sentence in re.split(r'(?<=[.!?])\s+', rag_source):
        if not sentence.strip():
            continue
        match = suggest_matching_test(sentence, threshold=threshold)
        if match:
            return ("ambiguous", sentence.strip(), match)

    # Backstop (see comment at the top): a score-like statement that names no known test.
    # Age is excluded: it comes from registration / plain statements, not from a named test.
    if required.measure != "age":
        for sentence in re.split(r'(?<=[.!?])\s+', rag_source):
            if (re.search(r"\d", sentence)
                    and _TEST_TALK_RE.search(sentence)
                    and find_measure(sentence) is None):
                return ("ambiguous", sentence.strip(), required.measure)

    return ("none", None)