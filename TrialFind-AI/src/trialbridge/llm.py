"""
Model loading and raw generation call. This is the ONLY file in the package that
needs a GPU / the actual gemma-2-9b-it weights — everything else (numeric_extraction,
drug_extraction, measure_matching, intent_router, pipeline logic) is plain Python
and testable on a laptop with no GPU at all.

Keeping this isolated is deliberate: it means the entire deterministic layer, the
RAG retrieval layer, and the pipeline wiring can be unit-tested locally, and the
only thing that has to run on Kaggle is this one call.
"""

from __future__ import annotations
import json

_tokenizer = None
_model = None


def load_model(model_name: str = "google/gemma-2-9b-it"):
    """Call this once, in the Kaggle notebook, before using call_llm."""
    global _tokenizer, _model
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

    _tokenizer = AutoTokenizer.from_pretrained(model_name)
    _model = AutoModelForCausalLM.from_pretrained(
        model_name, quantization_config=bnb_config, device_map={"": 0}
    )
    _model.eval()


def call_llm(prompt: str, max_new_tokens: int = 256) -> str:
    if _model is None or _tokenizer is None:
        raise RuntimeError("Call load_model() first (GPU environment only).")

    messages = [{"role": "user", "content": prompt}]
    text = _tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = _tokenizer(text, return_tensors="pt").to(_model.device)

    output = _model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        temperature=None,
    )
    response = output[0][inputs["input_ids"].shape[1]:]
    return _tokenizer.decode(response, skip_special_tokens=True)


def parse_llm_json(raw_response: str):
    import re
    text = raw_response.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
