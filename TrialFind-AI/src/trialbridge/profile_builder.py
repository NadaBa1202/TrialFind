"""
Turns the PERSISTED conversation (patient record + message turns) into the text views
the rest of the pipeline needs. Everything here is recomputed from persisted data on every
call, so the "state is re-derivable" principle from the spec still holds.

Why several text views instead of one?
  The old code concatenated caregiver messages only. That lost the question a short answer
  belongs to ("No" alone means nothing). But simply pasting the assistant's questions into
  the profile would poison the deterministic layers: the drug scanner would "find" a blood
  thinner in OUR question, and the test-name matcher would "find" an MMSE mention in OUR
  question. So each consumer gets the view it can safely use:

    llm_text         Q/A transcript + registration background (for the LLM judge)
    rules_text       background + caregiver lines, with a tiny " [re: MMSE]" tag on bare-number
                     answers (for numeric_extraction)
    scan_text        background + caregiver statements, no questions (for drug scan)
    statements_text  caregiver statements only (for RAG test-name ambiguity check)

It also derives which criteria must NOT be asked again (`unaskable_ids`):
  * the caregiver answered "I don't know" / "not sure" to a question about it, or
  * it has already been asked MAX_ASKS_PER_CRITERION times.
Both facts come from the persisted assistant turns (which carry the criterion id they asked
about), so no extra state is stored anywhere.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional

from .numeric_extraction import CONTEXT_MARK, find_measure

MAX_ASKS_PER_CRITERION = 2
_DONT_KNOW_MAX_WORDS = 15  # long answers that merely contain "don't know" usually carry other info

_APOS = "[’']"
_DONT_KNOW_RE = re.compile(
    "|".join(
        [
            rf"\b(?:do\s?not|don{_APOS}?t|dont|cannot|can{_APOS}?t)\s+(?:really\s+)?(?:know|remember|recall)\b",
            r"\bno\s+idea\b",
            r"\bnot\s+(?:really\s+)?sure\b",
            r"\bunsure\b",
            r"\bunknown\b",
            r"\bskip\b",
            r"\bje\s+ne\s+sais\s+pas\b",
            r"\bsais\s+pas\b",
            r"\bpas\s+s[uû]r\b",
            r"\bje\s+ne\s+me\s+souviens\s+pas\b",
        ]
    ),
    re.IGNORECASE,
)


def is_dont_know(answer: str) -> bool:
    return len(answer.split()) <= _DONT_KNOW_MAX_WORDS and bool(_DONT_KNOW_RE.search(answer))


@dataclass
class Turn:
    role: str  # "assistant" | "caregiver" (case-insensitive)
    content: str
    criterion_id: Optional[str] = None  # set on assistant turns that target one criterion


@dataclass
class ProfileBundle:
    llm_text: str
    rules_text: str
    scan_text: str
    statements_text: str
    unaskable_ids: set[str] = field(default_factory=set)

    @classmethod
    def from_plain_text(cls, text: str) -> "ProfileBundle":
        """Backwards-compatible path: one blob of free text used everywhere, as before."""
        return cls(llm_text=text, rules_text=text, scan_text=text, statements_text=text)


def build_profile(
    patient_context: str,
    turns: list[Turn],
    criteria: Optional[list[dict]] = None,
) -> ProfileBundle:
    by_id = {c["id"]: c for c in (criteria or [])}
    background = [ln.strip() for ln in (patient_context or "").splitlines() if ln.strip()]

    llm_blocks: list[str] = []
    rules_lines: list[str] = []
    statements: list[str] = []
    ask_counts: dict[str, int] = {}
    unaskable: set[str] = set()

    target_id: Optional[str] = None  # criterion the NEXT caregiver message is answering
    target_question: Optional[str] = None

    for turn in turns:
        if turn.role.lower() == "assistant":
            target_id = turn.criterion_id
            target_question = turn.content if turn.criterion_id else None
            if turn.criterion_id:
                ask_counts[turn.criterion_id] = ask_counts.get(turn.criterion_id, 0) + 1
            continue

        answer = turn.content.strip()
        if not answer:
            continue

        measure: Optional[str] = None
        if target_id:
            llm_blocks.append(f"Q: {target_question}\nA: {answer}")
            if is_dont_know(answer):
                unaskable.add(target_id)
            if target_id in by_id:
                measure = find_measure(by_id[target_id]["text"])
        else:
            llm_blocks.append(f"Caregiver: {answer}")

        statements.append(answer)
        for line in answer.splitlines():
            line = line.strip()
            if not line:
                continue
            # Tag a bare-number answer with the measure the question was about, so
            # "22" (answer to an MMSE question) can be recognised as MMSE = 22.
            # Never tag a line that already names a measure itself.
            if measure and re.search(r"\d", line) and find_measure(line) is None:
                line = f"{line}{CONTEXT_MARK}{measure.upper()}]"
            rules_lines.append(line)

        target_id, target_question = None, None

    for criterion_id, n in ask_counts.items():
        if n >= MAX_ASKS_PER_CRITERION:
            unaskable.add(criterion_id)

    parts = []
    if background:
        parts.append("Patient background (from registration):\n" + "\n".join(background))
    if llm_blocks:
        parts.append(
            "Conversation with the caregiver (lines starting with 'Q:' are questions asked by "
            "the screening tool — they are NOT facts about the patient; only the caregiver's "
            "answers and statements are facts):\n" + "\n\n".join(llm_blocks)
        )

    return ProfileBundle(
        llm_text="\n\n".join(parts),
        rules_text="\n".join(background + rules_lines),
        scan_text="\n".join(background + statements),
        statements_text="\n".join(statements),
        unaskable_ids=unaskable,
    )
