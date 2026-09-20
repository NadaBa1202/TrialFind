
import json
import requests

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
OUTPUT_FILE = "trials.json"
TARGET_COUNT = 50


def download_trials(condition: str = "Alzheimer Disease", target_count: int = TARGET_COUNT) -> list[dict]:
    studies: list[dict] = []
    page_token = None

    while len(studies) < target_count:
        params = {
            "query.cond": condition,
            "filter.overallStatus": "RECRUITING",
            "pageSize": min(100, target_count - len(studies)),
            "format": "json",
        }
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("studies", [])
        if not batch:
            print("No more results returned by the API.")
            break

        studies.extend(batch)
        print(f"Fetched {len(batch)} studies (total so far: {len(studies)})")

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return studies[:target_count]


if __name__ == "__main__":
    trials = download_trials()
    with open(OUTPUT_FILE, "w") as f:
        json.dump(trials, f, indent=2)
    print(f"\nSaved {len(trials)} trials to {OUTPUT_FILE}")

    # sanity check: how many actually mention Alzheimer's in their conditions?
    # (query.cond does a broad relevance-ranked search, not a strict filter,
    # so it's worth checking this yourself once you have real output —
    # you may see some loosely-related neurological/geriatric trials mixed in)
    on_topic = 0
    for t in trials:
        conditions = t.get("protocolSection", {}).get("conditionsModule", {}).get("conditions", [])
        if any("alzheimer" in c.lower() for c in conditions):
            on_topic += 1
    print(f"{on_topic}/{len(trials)} trials explicitly list 'Alzheimer' in their conditions list.")
    print("If that number looks low, tighten the query (e.g. add query.term for extra keywords) in Day 3.")