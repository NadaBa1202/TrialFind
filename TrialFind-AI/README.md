# TrialBridge

Hybrid NLP + RAG + LLM pipeline for criterion-level clinical trial eligibility
assessment from free-text patient/caregiver input.

## Folder structure

```
trialbridge/
├── src/trialbridge/
│   ├── __init__.py          # public API surface
│   ├── llm.py                # GPU-only: model loading, call_llm, parse_llm_json
│   ├── prompts.py             # V7 judgment prompt (locked) + build_prompt()
│   ├── numeric_extraction.py  # Tier 1 deterministic: age/MMSE/CDR/MoCA regex parsing
│   ├── drug_extraction.py     # Tier 1 deterministic + Tier 2 RAG: drug/negation scan
│   ├── measure_matching.py    # Tier 1 exact + Tier 2 RAG: test-name resolution
│   ├── retrieval.py           # generic small-corpus embedding retriever (shared)
│   ├── corpora.py             # the 3 small reference corpora (data, not logic)
│   ├── intent_router.py       # 3-bucket free-text router (profile/concept/out-of-scope)
│   ├── rollup.py              # deterministic aggregate_trial_verdict()
│   ├── followup.py            # generate_followup_questions() from unresolved criteria
│   └── pipeline.py            # assess_eligibility() — wires everything together
├── eval/
│   ├── eval_dev.json          # 30 examples, iterated against
│   ├── eval_heldout.json      # 10 examples, run once, untouched during iteration
│   └── run_eval.py            # Kaggle-only harness (needs the real model)
├── tests/
│   └── test_pipeline.py       # runs on a laptop, NO GPU, uses a fake LLM
├── notebooks/
│   └── trialbridge_kaggle.ipynb  # thin runner: load_model() + demo + eval
└── requirements.txt
```

## Which old notebook cells map to which file

| Old cell content | New file |
|---|---|
| Model load, `call_llm`, `parse_llm_json` | `src/trialbridge/llm.py` |
| `LLM_PROMPT` (V7), `VARIANTS`, `build_prompt` | `src/trialbridge/prompts.py` |
| `numeric_extraction.py` cell | `src/trialbridge/numeric_extraction.py` |
| `DRUG_CLASS_KEYWORDS`, `NEGATION_CUES`, `scan_drug_mentions`, `build_augmented_profile` | `src/trialbridge/drug_extraction.py` (extended with RAG tier 2) |
| `KNOWN_MEASURES_CORPUS`, `suggest_matching_test` | `src/trialbridge/corpora.py` + `measure_matching.py` |
| `check_measure_mention` | `src/trialbridge/measure_matching.py` |
| `aggregate_trial_verdict` | `src/trialbridge/rollup.py` |
| `assess_eligibility` | `src/trialbridge/pipeline.py` |
| `generate_followup_question(s)` | `src/trialbridge/followup.py` |
| eval loop, `CATEGORY_MAP`, metrics cells | `eval/run_eval.py` (kept minimal; extend as needed) |
| eval_dev/eval_heldout split cell | done once, now static files in `eval/` |

Everything **except `llm.py`** is plain Python with no GPU, no `transformers`,
no `torch` import. That split is deliberate — it's what makes local testing
possible at all.

## How to test without a GPU

`pipeline.assess_eligibility()` takes `call_llm` and `parse_llm_json` as **parameters**,
not as hardcoded imports:

```python
def assess_eligibility(free_text_profile, trial_criteria, call_llm, parse_llm_json):
    ...
```

This is a standard technique called **dependency injection**: instead of the function
reaching out and importing the real GPU-backed `call_llm` itself, the caller hands it
in. On Kaggle, you hand in the real one from `llm.py`. On your laptop, you hand in a
fake function that returns a canned JSON string instantly — no model, no GPU, no
download beyond the ~80MB sentence-embedding model used for the RAG tiers.

Run:
```bash
pip install -r requirements.txt
python tests/test_pipeline.py
```

What this actually tests, and what it doesn't:
- **Tests**: your Python plumbing — does the right criterion reach the LLM step, does
  an ambiguous measure mention correctly short-circuit *before* the LLM step (proven
  by using a fake `call_llm` that raises an error if it's ever called), does the
  numeric parser handle conversational phrasing, does negation/temporal detection work,
  does rollup combine verdicts correctly.
- **Does NOT test**: whether gemma-2-9b-it reasons correctly about a given criterion.
  That's a model-quality question, not a code-correctness question — it can only be
  answered by `eval/run_eval.py` on Kaggle, against the real model.

This separation matters for how you present the project: your architecture and
deterministic/RAG layers are unit-testable and CI-able in a normal GitHub Actions
setup with no GPU runner needed; only the final model-quality claim (93% dev /
80% held-out) requires the GPU environment.

## Academic grounding for the choices made

**Overall task framing — claim verification, not classification.** The
`eligible / not_eligible / insufficient_information` verdict set mirrors the
Supported / Refuted / Not Enough Info labels used in the FEVER fact-verification
benchmark (Thorne et al., 2018). Framing eligibility checking as claim verification
against evidence — rather than free-form generation — is what makes a bucketed,
rule-driven prompt (Bucket A/B/C) a principled design rather than an ad hoc one.

**Three-stage retrieval → per-criterion matching → aggregation architecture.**
Independently arrived at, then confirmed to match TrialGPT (Jin et al., 2023/2024,
*Nature Communications*), an NIH/NCI system with the same shape: a retrieval stage,
a criterion-level LLM matching stage that outputs an explanation alongside each
verdict, and an aggregation/ranking stage. TrialGPT reports ~0.86 accuracy on
exclusion criteria with GPT-4-class models; this project's 0.80 held-out accuracy
on a quantized 9B model is a reasonable result in that context, not directly
comparable (different model scale, different and much smaller eval set).

**Deterministic pre-processing before the LLM call.** Motivated by, and consistent
with, pre-LLM clinical NLP systems for criteria structuring — e.g. Criteria2Query
and EliIE — which used named entity recognition and negation detection (the NegEx
algorithm, Chapman et al., 2001) to convert free-text eligibility criteria into
structured, queryable form before any downstream reasoning. `drug_extraction.py`'s
negation-window check is an informal instance of NegEx's trigger-word approach;
citing the original algorithm is the more rigorous way to describe and defend it
than "regex I wrote."

**RAG scope: bridging phrasing to a fixed, small, known concept set.** This project's
RAG usage deliberately does NOT retrieve over the patient profile (too small a
document to benefit from retrieval) and does NOT use RAG as a general-purpose
answer generator. It is used narrowly, in the classic Lewis et al. (2020) RAG sense
of grounding a generation step in retrieved reference text — except here, retrieval
output is never handed to a generation step at all; it's used directly as a matched
label (a test name, a drug class) with an explicit uncertainty flag, precisely to
avoid the hallucination risk RAG is meant to reduce in the first place.

**Prompt length vs. instruction-following reliability.** The empirical finding that
a more heavily-ruled prompt (V6, with nested bucket sub-rules) performed *worse*
than a shorter one (V5/V7) on this model is consistent with documented instruction-
following degradation in smaller instruction-tuned models under long, dense,
multi-constraint prompts — worth citing generally as "smaller models show reduced
adherence to individual instructions as instruction count/density increases" rather
than claiming this is a novel finding; it's a reproduction of a known effect at a
small scale, which is itself a legitimate and reportable result for a learning
project.

**Evaluation methodology — dev/held-out split.** Standard practice to detect
overfitting to a fixed evaluation set during iterative prompt engineering; applied
here at small scale (30/10) specifically because early iterations (V1→V6) showed
prompt rules that mirrored the eval set's own failure categories too closely to
trust the resulting accuracy number without a held-out check.
