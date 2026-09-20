import json
import re
import sys

from pathlib import Path

# src/ needs to be on sys.path so "trialbridge" is importable as a package
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from trialbridge.criteria_parser import parse_eligibility_criteria

BASE_DIR = Path(__file__).resolve().parents[3]   # project root, where data/ lives

INPUT_FILE = BASE_DIR / "data" / "trials.json"
OUTPUT_FILE = BASE_DIR / "data" / "trial_summary.json"
MIN_CRITERION_LENGTH = 8
JUNK_PATTERNS = [
    r"^see\b", r"^below\.?$", r"^above\.?$", r"^\(?see additional",
    r"^n/?a$", r"^none\.?$",
]


def is_junk_criterion(text: str) -> bool:
    text = text.strip()
    if len(text) < MIN_CRITERION_LENGTH:
        return True
    low = text.lower()
    return any(re.match(p, low) for p in JUNK_PATTERNS)


def _parse_age(age_str: str | None) -> int | None:
    if not age_str:
        return None
    match = re.search(r"\d+", age_str)
    return int(match.group()) if match else None


def summarize_trial(study: dict) -> dict:
    protocol = study.get("protocolSection", {})
    ident = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    conditions = protocol.get("conditionsModule", {})
    eligibility = protocol.get("eligibilityModule", {})
    description = protocol.get("descriptionModule", {})
    design = protocol.get("designModule", {})
    contacts_locations = protocol.get("contactsLocationsModule", {})
    raw_criteria = eligibility.get("eligibilityCriteria", "")
    parsed_criteria = parse_eligibility_criteria(raw_criteria)

    return {
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "status": status.get("overallStatus"),
        "conditions": conditions.get("conditions", []),
        "min_age": _parse_age(eligibility.get("minimumAge")),
        "max_age": _parse_age(eligibility.get("maximumAge")),
        "sex": eligibility.get("sex"),
        "inclusion_criteria": [
            {"id": c.id, "text": c.text} for c in parsed_criteria
            if c.section == "inclusion" and not is_junk_criterion(c.text)
        ],
        "exclusion_criteria": [
            {"id": c.id, "text": c.text} for c in parsed_criteria
            if c.section == "exclusion" and not is_junk_criterion(c.text)
        ],
        "phases": design.get("phases", []),
        "brief_summary": description.get("briefSummary"),
        "study_url": f"https://clinicaltrials.gov/study/{ident.get('nctId')}",
        "locations": [
            {
                "facility": loc.get("facility"),
                "city": loc.get("city"),
                "state": loc.get("state"),
                "country": loc.get("country"),
                "status": loc.get("status"),
            }
            for loc in contacts_locations.get("locations", [])
        ],
    }


if __name__ == "__main__":
    with open(INPUT_FILE, "r") as f:
        trials = json.load(f)
    summaries = [summarize_trial(t) for t in trials]
    with open(OUTPUT_FILE, "w") as f:
        json.dump(summaries, f, indent=2)
    print(f"Summarized {len(summaries)} trials -> {OUTPUT_FILE}")

    no_min_age = sum(1 for s in summaries if s["min_age"] is None)
    no_exclusion = sum(1 for s in summaries if not s["exclusion_criteria"])
    no_criteria = sum(1 for s in summaries if not s["inclusion_criteria"] and not s["exclusion_criteria"])
    print(f"{no_min_age}/{len(summaries)} trials have no minimum age listed.")
    print(f"{no_exclusion}/{len(summaries)} trials have no exclusion criteria section.")
    print(f"{no_criteria}/{len(summaries)} trials have zero usable criteria after junk filtering.")