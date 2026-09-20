"""
HTTP wrapper around the eligibility pipeline — this is what the NestJS backend calls
(`POST {TRIALBRIDGE_AI_URL}/eligibility/assess`).

Run locally with no GPU (LLM answers are stubbed, everything else is real):
    TRIALFIND_FAKE_LLM=1 uvicorn trialbridge.api:app --port 8000

Run on Kaggle (model loaded once, GPU): see README — load the model in a notebook cell,
then start uvicorn in a background thread and expose it with a tunnel.

Env vars:
    AI_SERVICE_KEY       shared secret; if set, requests must send it in the x-api-key header
    TRIALFIND_FAKE_LLM   "1" to skip loading Gemma and answer "insufficient_information"
"""

from __future__ import annotations
import hmac
import os
import threading
from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .conversation import step_eligibility_conversation
from .profile_builder import Turn, build_profile

_FAKE_LLM = os.environ.get("TRIALFIND_FAKE_LLM") == "1"
_llm_lock = threading.Lock()  # one GPU, one generate() at a time


def _fake_call_llm(prompt: str) -> str:
    return ('{"verdict": "insufficient_information", "criterion_measure_required": null, '
            '"criterion_measure_found_in_profile": null, "reasoning": "fake llm"}')


def _llm_callables():
    if _FAKE_LLM:
        from .llm import parse_llm_json
        return _fake_call_llm, parse_llm_json

    from . import llm

    def locked_call(prompt: str) -> str:
        with _llm_lock:
            return llm.call_llm(prompt)

    return locked_call, llm.parse_llm_json


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not _FAKE_LLM:
        from . import llm
        if llm._model is None:  # already loaded by the notebook cell? then don't reload
            llm.load_model()
    yield


app = FastAPI(title="TrialFind AI service", lifespan=lifespan)


class CriterionIn(BaseModel):
    id: str
    section: Literal["inclusion", "exclusion"]
    text: str


class TurnIn(BaseModel):
    role: str  # "assistant" | "caregiver" (any case)
    content: str
    criterion_id: Optional[str] = None


class AssessRequest(BaseModel):
    patient_context: str = ""
    turns: list[TurnIn] = []
    criteria: list[CriterionIn]


@app.get("/health")
def health():
    return {"ok": True, "fake_llm": _FAKE_LLM}


@app.post("/eligibility/assess")
def assess(req: AssessRequest, x_api_key: Optional[str] = Header(default=None)):
    expected = os.environ.get("AI_SERVICE_KEY")
    if expected and not hmac.compare_digest(x_api_key or "", expected):
        raise HTTPException(status_code=401, detail="Invalid API key")

    criteria = [c.model_dump() for c in req.criteria]
    turns = [Turn(role=t.role, content=t.content, criterion_id=t.criterion_id) for t in req.turns]
    bundle = build_profile(req.patient_context, turns, criteria)

    call_llm, parse_llm_json = _llm_callables()
    step = step_eligibility_conversation(
        bundle, criteria, call_llm, parse_llm_json, skipped_ids=bundle.unaskable_ids
    )

    question = step["next_question"]
    return {
        **step["result"],
        "status": step["status"],
        "verdict": step["verdict"],
        "next_question": question,
        "next_criterion_id": step["next_criterion_id"],
        "followup_questions": [question] if question else [],
        "pending_criteria": step.get("pending_criteria", []),
        "criteria_remaining": step.get("criteria_remaining", 0),
    }
