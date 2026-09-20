"""
Generic small-corpus embedding retriever.

This is the one piece of "real RAG" in the project: embed a small, deliberately
curated corpus once, embed an incoming phrase, and return the nearest entry if it
clears a similarity threshold. Used by three different consumers (measure/test
name matching, drug-class matching, and the concept-question router) so the
retrieval mechanism only needs to be written and tested once.

Design principle this file exists to protect: RAG bridges arbitrary PHRASING to a
FIXED, small, human-maintained set of known concepts. It is not a general-purpose
retrieval layer, and it never asserts a fact on its own — callers are expected to
treat a match as a suggestion (surfaced back to the user to confirm), not as
verified ground truth. See measure_matching.py and drug_extraction.py for how
that boundary is enforced downstream.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class RetrievalMatch:
    key: str
    score: float
    document: str


class SmallCorpusRetriever:
    """
    Wraps a small dict of {key: reference_text} with embedding-based lookup.
    Lazy-loads the embedding model on first use so importing this module doesn't
    require a GPU / sentence-transformers to be installed unless retrieval is
    actually called.
    """

    def __init__(self, corpus: dict[str, str], model_name: str = "all-MiniLM-L6-v2"):
        self.corpus = corpus
        self._model_name = model_name
        self._embedder = None
        self._keys = list(corpus.keys())
        self._embeds = None

    def _ensure_loaded(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(self._model_name)
            self._embeds = self._embedder.encode(
                list(self.corpus.values()), normalize_embeddings=True
            )

    def best_match(self, phrase: str, threshold: float = 0.55) -> Optional[RetrievalMatch]:
        self._ensure_loaded()
        phrase_embed = self._embedder.encode([phrase], normalize_embeddings=True)[0]
        sims = self._embeds @ phrase_embed
        best_idx = int(np.argmax(sims))
        score = float(sims[best_idx])
        if score >= threshold:
            key = self._keys[best_idx]
            return RetrievalMatch(key=key, score=score, document=self.corpus[key])
        return None

    def top_k(self, phrase: str, k: int = 3) -> list[RetrievalMatch]:
        self._ensure_loaded()
        phrase_embed = self._embedder.encode([phrase], normalize_embeddings=True)[0]
        sims = self._embeds @ phrase_embed
        order = np.argsort(-sims)[:k]
        return [
            RetrievalMatch(key=self._keys[i], score=float(sims[i]), document=self.corpus[self._keys[i]])
            for i in order
        ]
