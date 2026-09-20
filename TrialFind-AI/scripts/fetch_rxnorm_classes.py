"""
Pulls real drug-class membership from RxNorm's RxClass API and caches it to a JSON
file. Run this ONCE (or occasionally, to refresh), not on every pipeline call — no
live API dependency during actual use, just a periodically-refreshed local cache.

This replaces the hand-typed DRUG_CLASS_KEYWORDS dict in drug_extraction.py with
something backed by NLM's maintained vocabulary instead of your own memory of drug
names.
"""

import json
import time
import requests

BASE = "https://rxnav.nlm.nih.gov/REST/rxclass"

# Map YOUR class keys -> a (className to search, classType, relaSource) to query.
# classType/relaSource pairs matter: ATC covers most common drug categories well;
# newer biologics (like anti-amyloid antibodies) are often only classified under
# EPC (FDA "Established Pharmacologic Class") via DailyMed, not ATC.
CLASS_QUERIES = {
    "anticoagulant": {
        "search_name": "Anticoagulants",
        "class_types": "ATC1-4",
        "rela_source": "ATC",
    },
    "oral_hypoglycemic": {
        "search_name": "Hypoglycemic Agents",
        "class_types": "ATC1-4",
        "rela_source": "ATC",
    },
    "anti_amyloid_mab": {
        "search_name": "Amyloid Beta-directed Antibody",
        "class_types": "EPC",
        "rela_source": "DAILYMED",
    },
}


def find_class_id(search_name: str, class_types: str) -> list[str]:
    resp = requests.get(
        f"{BASE}/class/byName.json",
        params={"className": search_name, "classTypes": class_types},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    concepts = data.get("rxclassMinConceptList", {}).get("rxclassMinConcept", [])
    return [c["classId"] for c in concepts]


def get_class_members(class_id: str, rela_source: str) -> list[dict]:
    resp = requests.get(
        f"{BASE}/classMembers.json",
        params={"classId": class_id, "relaSource": rela_source, "ttys": "IN"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    members = data.get("drugMemberGroup", {}).get("drugMember", [])
    return [
        {"rxcui": m["minConcept"]["rxcui"], "name": m["minConcept"]["name"]}
        for m in members
        if "minConcept" in m
    ]


def build_corpus() -> dict:
    result = {}
    for class_key, query in CLASS_QUERIES.items():
        print(f"Fetching: {class_key} ...")
        class_ids = find_class_id(query["search_name"], query["class_types"])
        if not class_ids:
            print(f"  WARNING: no classId found for '{query['search_name']}' — skipping. "
                  f"Check the name/classType manually on rxnav.nlm.nih.gov.")
            continue

        all_members = []
        for class_id in class_ids:
            members = get_class_members(class_id, query["rela_source"])
            all_members.extend(members)
            time.sleep(0.3)  # be polite to the free public API

        drug_names = sorted({m["name"].lower() for m in all_members})
        result[class_key] = {
            "drug_names": drug_names,
            "rxcui_map": {m["name"].lower(): m["rxcui"] for m in all_members},
        }
        print(f"  Found {len(drug_names)} drugs for {class_key}")

    return result


if __name__ == "__main__":
    corpus = build_corpus()
    with open("rxnorm_drug_classes.json", "w") as f:
        json.dump(corpus, f, indent=2)
    print("\nSaved to rxnorm_drug_classes.json")
    for k, v in corpus.items():
        print(f"{k}: {len(v['drug_names'])} drugs, e.g. {v['drug_names'][:5]}")
