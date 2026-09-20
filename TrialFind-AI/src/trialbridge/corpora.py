"""
Small, deliberately curated reference corpora for RAG lookups.

Each corpus is a finite, human-maintained set of *concepts* (not phrasings).
Growing these lists is expected maintenance (a new drug approval, a newly
relevant diagnostic instrument) — it is not the same problem as trying to
enumerate every way a patient might phrase a reference to a concept that's
already here. See retrieval.py for why that distinction is the whole point.
"""

# --- Cognitive/clinical test names -----------------------------------------
KNOWN_MEASURES_CORPUS = {
    "mmse": "MMSE, Mini-Mental State Examination, a cognitive memory test scored 0 to 30",
    "moca": "MoCA, Montreal Cognitive Assessment, a cognitive memory test scored 0 to 30",
    "cdr": "CDR, Clinical Dementia Rating, a dementia staging score from 0 to 3",
}

# --- Drug class reference (used for both extraction and concept answers) ---
DRUG_CLASS_CORPUS = {
    "anticoagulant": "Anticoagulant / blood thinner medications, e.g. warfarin, apixaban "
                      "(Eliquis), rivaroxaban (Xarelto), dabigatran, heparin, enoxaparin",
    "anti_amyloid_mab": "Anti-amyloid monoclonal antibody drugs for Alzheimer's disease, "
                         "e.g. lecanemab (Leqembi), donanemab (Kisunla), aducanumab (Aduhelm)",
    "oral_hypoglycemic": "Oral hypoglycemic / diabetes medications, e.g. metformin, "
                          "glipizide, glyburide, sitagliptin",
}

# --- Concept-question corpus, for the "what is X" router bucket ------------
# Plain-English answers a patient/caregiver can be given directly, with no LLM call.
CONCEPT_ANSWERS_CORPUS = {
    "mmse_explainer": (
        "MMSE (Mini-Mental State Examination) is a cognitive screening test scored 0-30, "
        "usually given by a doctor or nurse during a memory evaluation. Lower scores "
        "suggest more cognitive impairment."
    ),
    "moca_explainer": (
        "MoCA (Montreal Cognitive Assessment) is a cognitive screening test scored 0-30, "
        "similar in purpose to the MMSE but a different test with its own scoring — the two "
        "aren't interchangeable. It's typically given by a neurologist or geriatrician."
    ),
    "cdr_explainer": (
        "CDR (Clinical Dementia Rating) is a staging scale from 0 (no impairment) to 3 "
        "(severe dementia), based on a structured interview with the patient and a "
        "caregiver/family member, usually done by a specialist."
    ),
    "study_partner_explainer": (
        "A 'study partner' is someone (often a spouse, adult child, or close caregiver) who "
        "attends trial visits with the participant and can report on day-to-day functioning. "
        "Many memory/dementia trials require one."
    ),
    "nia_aa_explainer": (
        "NIA-AA criteria are a standardized set of clinical guidelines (from the National "
        "Institute on Aging and Alzheimer's Association) used by doctors to formally diagnose "
        "probable Alzheimer's disease — a formal diagnosis using these criteria is different "
        "from a general memory complaint."
    ),
}
