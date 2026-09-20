"""
Loads rxnorm_drug_classes.json (produced by scripts/fetch_rxnorm_classes.py) and
converts it into the two shapes the rest of the codebase already expects:

  1. DRUG_CLASS_KEYWORDS_RXNORM — a flat {drug_name: class_key} lookup for tier 1
     exact matching (replaces/extends the hand-typed list in drug_extraction.py).
  2. DRUG_CLASS_CORPUS_RXNORM — a {class_key: description_text} corpus for tier 2
     RAG matching (same shape as the hand-typed DRUG_CLASS_CORPUS in corpora.py).

This is a separate loader, not a rewrite of corpora.py, so the hand-typed corpus
still works as a fallback if the RxNorm cache file is missing or a class fetch
failed (see the "WARNING: no classId found" case in the fetch script).
"""

from __future__ import annotations
import json
import os

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "rxnorm_drug_classes.json")


def load_rxnorm_corpus(path: str = _DEFAULT_PATH) -> tuple[dict[str, str], dict[str, str]]:
    """
    Returns (keyword_lookup, rag_corpus).
    keyword_lookup: {drug_name_lowercase: class_key}   -- for exact tier 1 matching
    rag_corpus:      {class_key: description_text}       -- for tier 2 embedding matching
    """
    if not os.path.exists(path):
        return {}, {}

    with open(path) as f:
        raw = json.load(f)

    keyword_lookup = {}
    rag_corpus = {}

    for class_key, entry in raw.items():
        drug_names = entry.get("drug_names", [])
        for name in drug_names:
            keyword_lookup[name] = class_key

        # Build a short description for the RAG corpus from a sample of real drug
        # names, so the embedding has real vocabulary to compare against — not
        # just an abstract description.
        sample = ", ".join(drug_names[:8])
        rag_corpus[class_key] = f"{class_key.replace('_', ' ')} medications, including {sample}"

    return keyword_lookup, rag_corpus
