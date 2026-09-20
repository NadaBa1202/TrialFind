"""
Deterministic drug-mention and negation/temporal-status detection.

Tier 1 (this file's main path): keyword match against a small, explicitly maintained
drug list + a negation/temporal window check. Cheap, deterministic, no LLM.

Tier 2 (RAG, via retrieval.py + corpora.DRUG_CLASS_CORPUS): if NO keyword fires at all,
the sentence may still be naming a drug this project doesn't have listed by exact name.
Rather than silently missing it, we do a semantic lookup against the drug-class corpus.
Like measure_matching.py, a RAG hit here is surfaced as a "possible match" for the
follow-up-question layer to confirm — never injected as a verified fact.
"""

from __future__ import annotations
import re

from .corpora import DRUG_CLASS_CORPUS
from .retrieval import SmallCorpusRetriever
from .rxnorm_loader import load_rxnorm_corpus

# Hand-typed fallback — used only for drug names RxNorm's fetch didn't cover,
# or if the rxnorm_drug_classes.json cache is missing entirely (e.g. running
# somewhere without having run scripts/fetch_rxnorm_classes.py first).
_HAND_TYPED_KEYWORDS = {
    "anticoagulant": ["warfarin", "coumadin", "apixaban", "eliquis", "rivaroxaban",
                       "xarelto", "dabigatran", "heparin", "enoxaparin", "lovenox",
                       "blood thinner"],
    "anti_amyloid_mab": ["lecanemab", "leqembi", "donanemab", "kisunla",
                          "aducanumab", "aduhelm"],
    "oral_hypoglycemic": ["metformin", "glipizide", "glyburide", "sulfonylurea",
                           "sitagliptin"],
}

_rxnorm_keywords, _rxnorm_rag_corpus = load_rxnorm_corpus()

# Merge: RxNorm data (if available) plus hand-typed as a safety net for anything
# RxNorm's fetch missed or a class that failed to fetch (see fetch script warnings).
DRUG_CLASS_KEYWORDS = dict(_HAND_TYPED_KEYWORDS)
for drug_name, class_key in _rxnorm_keywords.items():
    DRUG_CLASS_KEYWORDS.setdefault(class_key, [])
    if drug_name not in DRUG_CLASS_KEYWORDS[class_key]:
        DRUG_CLASS_KEYWORDS[class_key].append(drug_name)

# Merge RAG corpus the same way — prefer RxNorm's real-drug-backed description
# when available, fall back to the hand-typed one otherwise.
_MERGED_DRUG_CLASS_CORPUS = dict(DRUG_CLASS_CORPUS)
_MERGED_DRUG_CLASS_CORPUS.update(_rxnorm_rag_corpus)

NEGATION_CUES = ["no ", "not on", "denies", "denied", "never", "none", "without",
                  "discontinued", "stopped taking", "stopped", "took me off",
                  "off of", "ruled out", "negative for", "no longer"]

TEMPORAL_PAST_CUES = ["ago", "used to", "previously", "prior to", "stopped", "discontinued",
                        "was on", "was taking", "before switching", "in the past"]
TEMPORAL_CURRENT_CUES = ["currently", "still taking", "still on", "right now", "at present"]

_drug_retriever = SmallCorpusRetriever(_MERGED_DRUG_CLASS_CORPUS)


def _classify_status(window_text: str) -> str:
    negated = any(cue in window_text for cue in NEGATION_CUES)
    has_past = any(cue in window_text for cue in TEMPORAL_PAST_CUES)
    has_current = any(cue in window_text for cue in TEMPORAL_CURRENT_CUES)

    if negated or (has_past and not has_current):
        return "discontinued_or_denied"
    if has_current:
        return "current"
    return "current_or_unclear"


def scan_drug_mentions(text: str) -> list[dict]:
    """Tier 1: exact keyword match + negation/temporal window."""
    text_lower = text.lower()
    findings = []
    matched_spans = []

    for drug_class, keywords in DRUG_CLASS_KEYWORDS.items():
        for kw in keywords:
            idx = text_lower.find(kw)
            if idx == -1:
                continue
            matched_spans.append((idx, idx + len(kw)))
            window_start = max(0, idx - 60)
            window = text_lower[window_start:idx + len(kw) + 20]
            findings.append({
                "drug_class": drug_class,
                "matched_term": kw,
                "status": _classify_status(window),
                "context": text[window_start:idx + len(kw) + 20].strip(),
                "source": "exact",
            })

    return findings


def scan_drug_mentions_with_rag_fallback(text: str, threshold: float = 0.55) -> list[dict]:
    """
    Tier 1 as above, plus Tier 2: for sentences that mention taking/stopping "something"
    without any keyword match, check candidate noun phrases against the drug-class corpus.
    This is intentionally conservative — it only fires on sentences that look like a
    medication statement (contain a trigger verb) but matched nothing in tier 1.
    """
    findings = scan_drug_mentions(text)
    if findings:
        return findings  # exact match found, don't bother with the fallback

    MED_STATEMENT_CUES = ["taking", "prescribed", "medication", "drug", "dose", "pill",
                            "infusion", "injection", "treatment", "regimen", "therapy"]
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sentence in sentences:
        low = sentence.lower()
        if not any(cue in low for cue in MED_STATEMENT_CUES):
            continue

        # Guard: a broad denial ("no medications of any kind") should NOT be sent
        # to the RAG fallback at all — there's no specific drug being described,
        # so a similarity match here is comparing generic negation language against
        # a drug-class description, not identifying an actual drug. That produced
        # a real false positive during testing (see project notes).
        has_negation = any(cue in low for cue in NEGATION_CUES)
        has_specific_drug_reference = any(
            word in low for word in ["this", "that", "it", "medication called", "drug called"]
        )
        if has_negation and not has_specific_drug_reference:
            continue

        match = _drug_retriever.best_match(sentence, threshold=threshold)
        if match:
            findings.append({
                "drug_class": match.key,
                "matched_term": sentence.strip(),
                "status": "current_or_unclear",  # RAG doesn't resolve status, just class
                "context": sentence.strip(),
                "source": "rag",
                "similarity": match.score,
            })
    return findings


def build_parsed_lines(free_text: str) -> list[str]:
    """The [Parsed] / [Parsed-uncertain] annotation lines, without the original text."""
    lines = []
    for finding in scan_drug_mentions_with_rag_fallback(free_text):
        if finding["source"] == "exact":
            lines.append(f"[Parsed] Mentions {finding['matched_term']} "
                          f"({finding['drug_class']}) — status: {finding['status']}.")
        else:
            lines.append(f"[Parsed-uncertain] Possible mention of a {finding['drug_class']} "
                          f"drug (not exactly matched, similarity {finding['similarity']:.2f}) — "
                          f"status unconfirmed, do not treat as certain.")
    return lines


def build_augmented_profile(free_text: str) -> str:
    return "\n".join([free_text.strip()] + build_parsed_lines(free_text))
