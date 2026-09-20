"""
Intent routing for free-text input, so an open text box doesn't behave like an
open-ended chatbot.

Every incoming message is classified into exactly one of three buckets, and each
bucket has a hard-bounded handler — none of them is "send it to an unconstrained
LLM call":

  PROFILE_INFO   -> goes to pipeline.assess_eligibility (the only path that reaches
                     the criterion-judgment LLM call).
  CONCEPT_QUESTION -> answered ONLY from corpora.CONCEPT_ANSWERS_CORPUS via RAG lookup.
                     No generation call. If nothing matches, say so honestly rather
                     than guessing.
  OUT_OF_SCOPE   -> a fixed, non-generative redirect message. No LLM call at all.

This mirrors the same principle used everywhere else in the project: reserve the
LLM for the one thing nothing else can do (per-criterion judgment), and make every
other decision deterministically wherever possible.
"""

from __future__ import annotations
from enum import Enum

from .corpora import CONCEPT_ANSWERS_CORPUS
from .retrieval import SmallCorpusRetriever

_concept_retriever = SmallCorpusRetriever(CONCEPT_ANSWERS_CORPUS)

# Small example sets used to classify intent via similarity — NOT an attempt to
# enumerate every phrasing, just reference anchors for each bucket.
_PROFILE_EXAMPLES = {
    "profile_1": "I'm 72 years old and was diagnosed with mild Alzheimer's last year",
    "profile_2": "My MMSE score was 22 and I don't take any blood thinners",
    "profile_3": "My mother has dementia, she's on donepezil and lives with me",
}
_CONCEPT_EXAMPLES = {
    "concept_1": "what is a MoCA score",
    "concept_2": "how do I find my MMSE result",
    "concept_3": "what does CDR mean",
    "concept_4": "who gives the study partner requirement",
}
_profile_retriever = SmallCorpusRetriever(_PROFILE_EXAMPLES)
_intent_concept_retriever = SmallCorpusRetriever(_CONCEPT_EXAMPLES)

OUT_OF_SCOPE_MESSAGE = (
    "I can help you check trial eligibility criteria against your own information, "
    "or explain terms used in this process (like MMSE or CDR) — I'm not able to "
    "answer general medical questions or give treatment advice. Please talk to your "
    "care team about anything outside that."
)


class Intent(str, Enum):
    PROFILE_INFO = "profile_info"
    CONCEPT_QUESTION = "concept_question"
    OUT_OF_SCOPE = "out_of_scope"


def classify_intent(message: str, threshold: float = 0.45) -> Intent:
    profile_match = _profile_retriever.best_match(message, threshold=threshold)
    concept_match = _intent_concept_retriever.best_match(message, threshold=threshold)

    # If both fire, prefer whichever scored higher; ties/uncertainty default to
    # the more restrictive bucket (out of scope), never to the LLM path by default.
    if profile_match and concept_match:
        return Intent.PROFILE_INFO if profile_match.score >= concept_match.score else Intent.CONCEPT_QUESTION
    if profile_match:
        return Intent.PROFILE_INFO
    if concept_match:
        return Intent.CONCEPT_QUESTION
    return Intent.OUT_OF_SCOPE


def answer_concept_question(message: str, threshold: float = 0.5) -> str:
    match = _concept_retriever.best_match(message, threshold=threshold)
    if match:
        return match.document
    return (
        "I don't have a plain-language explanation for that term yet — please ask "
        "your care team, or rephrase using the specific test/criterion name if you "
        "know it."
    )
