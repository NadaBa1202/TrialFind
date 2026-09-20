# TrialFind

**TrialFind** helps caregivers of people with Alzheimer's disease find clinical trials the patient might qualify for, and run a first, informal eligibility check through a short conversation.

> **Not medical advice.** TrialFind is an informational screening aid. It does not diagnose, recommend treatments, or replace a doctor or a trial's study team. Only the study team can confirm eligibility, and meeting the listed criteria does not guarantee enrolment.

**Status: work in progress.** The backend and the AI eligibility pipeline work end to end (see [What works and what doesn't yet](#what-works-and-what-doesnt-yet)). The web frontend is not built yet.

---

## Why this exists

Trial eligibility criteria are long, technical, and written for clinicians: often 20 to 40 inclusion and exclusion rules covering age, diagnosis, test scores, medications and medical history. A caregiver can't easily tell whether a trial is worth a phone call.

TrialFind splits the problem in two:

1. **Discovery.** The caregiver enters basic patient information and gets a list of trials that are not clearly incompatible. This step uses plain filtering, with no AI.
2. **Screening.** The caregiver picks a trial and chats about the patient. The system checks the trial's criteria against what was said, asks a follow-up question when something is missing, and stops when it can already tell.

## How the AI part is designed

The main design rule is that **the language model does not decide everything**.

| Job | Done by | Why |
|---|---|---|
| Number checks ("MMSE 22 within 18–26?", age ranges) | Python rules | LLMs are unreliable at arithmetic |
| Spotting drug names and "stopped / never / currently" wording | Python rules | cheap, deterministic, testable |
| "Is 'the memory test' the MoCA this trial requires?" | Embedding similarity **plus** a plain-rule backstop | never let the model guess a test name |
| Judging one criterion against the conversation | Gemma 2 9B (4-bit) | the only step that needs language understanding |
| Combining criteria into one verdict | Python rules | any single `not_eligible` vetoes the trial |

Safety choices:

- **A false "eligible" is treated as the worst error.** When unsure, the system says "insufficient information" and asks.
- **Exclusion criteria are judged as exclusions.** "History of stroke" means the patient is *excluded* if they have it. The criterion's section is kept end to end.
- **"I don't know" can't loop.** A criterion is never asked again after that answer, or after two asks. If only unanswerable criteria remain, the result is `likely_eligible` (nothing rules the patient out; the study team must confirm the rest).
- **State is re-derived, never trusted.** The full conversation is stored and everything is recomputed from it on each message, so a session can resume after a crash.
- **Patient names and contact details are never sent to the AI service.** It only receives age, sex, a condition summary and the conversation.

## Architecture

```
 Caregiver (React frontend, not built yet)
        │  HTTPS + JWT
        ▼
 ┌──────────────────────────┐         ┌───────────────────────────────┐
 │  Backend  (TrialFind-BE) │  HTTP   │  AI service (TrialFind-AI)    │
 │  NestJS · Prisma         │ ──────▶ │  FastAPI · Python             │
 │  auth · patients ·       │         │  rules → embeddings → Gemma   │
 │  trial search · sessions │ ◀────── │  POST /eligibility/assess     │
 └────────────┬─────────────┘         └───────────────┬───────────────┘
              ▼                                        ▼
        PostgreSQL                          Gemma 2 9B (4-bit, GPU)
   trials · patients · sessions            currently served from a Kaggle notebook
```

### One message, step by step

1. The caregiver sends a message. The backend saves it.
2. The backend sends the AI service the patient's registration data, the **whole** conversation (each assistant question remembers which criterion it asked about) and the trial's criteria (with their section: inclusion or exclusion).
3. For each criterion the AI service runs the cheap checks first. Only what the rules cannot settle goes to Gemma.
4. The verdicts are combined. The response is either one follow-up question or a final outcome: `not_eligible`, `eligible`, or `likely_eligible`.
5. The backend saves the answer and returns it.

## Repositories

| Repo | Contents |
|---|---|
| **TrialFind-BE** (this one) | NestJS API, Prisma schema, seed script, smoke test |
| **TrialFind-AI** | FastAPI service, eligibility pipeline (Python package `trialbridge`), trial download/parsing scripts, tests |

The Python package and the `TRIALBRIDGE_AI_*` environment variables use the earlier internal name *TrialBridge*.

## Tech stack

- **Backend:** NestJS (TypeScript), PostgreSQL, Prisma, JWT (short-lived access token + refresh token in an httpOnly cookie), bcrypt, rate limiting (`@nestjs/throttler`), Helmet, Swagger (non-production only at `/api/docs`).
- **AI:** Python, FastAPI, Gemma 2 9B instruct (4-bit, `bitsandbytes`), `sentence-transformers` (`all-MiniLM-L6-v2`).
- **Data:** real recruiting Alzheimer's trials from the [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api).

The backend follows a layered layout: `domain` (entities and abstract interfaces), `application` (use cases, DTOs, factories), `infrastructure` (Prisma repositories, JWT, bcrypt, the AI client), `presentation` (controllers, guards, filters).

## Getting started

### Prerequisites

Node 20+, pnpm, PostgreSQL, Python 3.10+. A GPU is only needed for the real model (see the Kaggle section); everything else runs without one.

### 1. Trial data (from TrialFind-AI)

```bash
cd TrialFind-AI
pip install requests
python src/trialbridge/scripts/download_trials.py    # writes trials.json in the current folder
mkdir -p data && mv trials.json data/
python src/trialbridge/scripts/parse_trials.py       # writes data/trial_summary.json
```

### 2. Backend

```bash
cd TrialFind-BE
pnpm install
cp .env.example .env                 # then fill in the values (see below)
pnpm prisma migrate dev
TRIALS_JSON=/path/to/trial_summary.json pnpm prisma db seed
pnpm start:dev                       # http://localhost:5555
```

PowerShell: `$env:TRIALS_JSON="C:\path\to\trial_summary.json"; pnpm prisma db seed`.
The seed needs `"prisma": { "seed": "ts-node --transpile-only prisma/seed.ts" }` in `package.json`.

Environment variables (`.env`):

```
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/trialfind
JWT_ACCESS_SECRET=            # long random strings, all different
JWT_REFRESH_SECRET=
JWT_RESET_SECRET=
COOKIE_SECRET=
CORS_ORIGIN=http://localhost:5173
TRIALBRIDGE_AI_URL=http://127.0.0.1:8000
TRIALBRIDGE_AI_KEY=           # must equal AI_SERVICE_KEY on the AI side; empty = no key
TRIALBRIDGE_AI_TIMEOUT_MS=120000
```

Generate a secret: `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"`.

### 3. AI service, locally, without a GPU

A fake model (it always answers "insufficient information") lets you exercise the whole flow without a GPU:

```bash
cd TrialFind-AI
pip install fastapi uvicorn pydantic numpy sentence-transformers
TRIALFIND_FAKE_LLM=1 python -m uvicorn trialbridge.api:app --app-dir src --port 8000
# PowerShell: $env:TRIALFIND_FAKE_LLM="1"; python -m uvicorn ...
```

Check it: `http://127.0.0.1:8000/health` returns `{"ok": true, "fake_llm": true}`.

### 4. AI service with the real model (Kaggle)

Gemma 2 9B needs a GPU, so during development the AI service runs in a Kaggle notebook and the backend reaches it through a tunnel.

Setup:

- Upload `TrialFind-AI` as a **private** Kaggle dataset (code only, never `.env` files).
- Notebook settings: **GPU on**, **Internet on**, notebook **private**.
- Accept the license for [`google/gemma-2-9b-it`](https://huggingface.co/google/gemma-2-9b-it) on Hugging Face.
- Add these under *Add-ons → Secrets*: `HF_TOKEN`, `NGROK_TOKEN`, `AI_SERVICE_KEY` (any long random string; the same value goes in the backend's `TRIALBRIDGE_AI_KEY`).

Never paste a token into a cell or print it. Restart the session after any `pip install` cell.

<details>
<summary>The notebook cells</summary>

```python
# 1. install (then RESTART the session; do not run this cell again)
!pip install -q fastapi uvicorn pyngrok sentence-transformers bitsandbytes accelerate
```

```python
# 2. Hugging Face login + access check (never prints the token)
from kaggle_secrets import UserSecretsClient
from huggingface_hub import login, hf_hub_download
secrets = UserSecretsClient()
login(token=secrets.get_secret("HF_TOKEN"))
hf_hub_download("google/gemma-2-9b-it", "config.json")
print("Gemma access OK")
```

```python
# 3. load the model (~18 GB download the first time, several minutes)
import sys
sys.path.insert(0, "/kaggle/input/<your-dataset>/TrialFind-AI/src")   # the folder that CONTAINS trialbridge/
from trialbridge import llm
llm.load_model()
```

```python
# 4. start the API (listens on localhost only; the tunnel exposes it)
import os, threading, time, urllib.request, uvicorn
os.environ["AI_SERVICE_KEY"] = secrets.get_secret("AI_SERVICE_KEY")
from trialbridge.api import app
server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning"))
threading.Thread(target=server.run, daemon=True).start()
time.sleep(3)
print(urllib.request.urlopen("http://127.0.0.1:8000/health").read())
```

```python
# 5. public tunnel; put the printed URL in the backend .env as TRIALBRIDGE_AI_URL
from pyngrok import ngrok
ngrok.set_auth_token(secrets.get_secret("NGROK_TOKEN"))
print(ngrok.connect(8000).public_url)
```

</details>

The tunnel URL changes every session. It is public, so the only thing protecting it is `AI_SERVICE_KEY`: keep the key set and use **fake patient data only**.

### 5. Try it

```bash
node scripts/smoke.mjs                         # register → patient → search → chat until a verdict
TARGET_CRITERIA=8 node scripts/smoke.mjs       # pick a trial with about 8 criteria
API_URL=http://localhost:5555 TRIAL_ID=<uuid> node scripts/smoke.mjs
```

By default the smoke test picks the trial with the fewest criteria and answers every follow-up with "I don't know", which also checks that a session always ends. With the real model each criterion costs about 10 seconds, so large trials can exceed the default timeout (raise `TRIALBRIDGE_AI_TIMEOUT_MS`).

## API overview

All backend responses are wrapped as `{ status, statusCode, message, data, timestamp }`.

| Method | Route | Purpose |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | create an account, sign in (returns an access token; sets the refresh cookie) |
| POST | `/auth/refresh`, `/auth/logout` | rotate the refresh token, sign out |
| POST · GET | `/patients`, `/patients/:id` | create and read the caregiver's patients |
| POST | `/trials/search` | phase 1: `{ age, sex, condition, stage?, locations? }` → matching trials |
| POST | `/eligibility/sessions` | phase 2: `{ patientId, trialId }` → `{ sessionId, assistantMessage }` |
| POST | `/eligibility/sessions/:id/messages` | `{ message }` → next question or final result |

A message response looks like:

```json
{
  "assistantMessage": "…",
  "status": "need_more_info",
  "verdict": "in_progress",
  "criteriaRemaining": 3,
  "pendingCriteria": [],
  "details": [ { "criterion": "…", "section": "exclusion", "verdict": "eligible", "reasoning": "…" } ]
}
```

`status` is `need_more_info` or `final`. A final `verdict` is `eligible`, `likely_eligible` or `not_eligible`.

The AI service exposes `POST /eligibility/assess` and `GET /health` (the assess call needs the `x-api-key` header when `AI_SERVICE_KEY` is set).

## Tests

```bash
cd TrialFind-AI
pip install pytest httpx
PYTHONPATH=src python -m pytest tests -q       # PowerShell: $env:PYTHONPATH="src"; python -m pytest tests -q
```

The tests use a fake model and never need a GPU. They cover section-aware judging of exclusion criteria, question/answer handling, the "I don't know" flow, registration data being used, vague test names, and the HTTP contract.

## What works and what doesn't yet

**Works**

- Accounts, patients, trial discovery over real ClinicalTrials.gov data, persisted eligibility sessions.
- The two-phase flow end to end, verified with the real model on a set of 14 hand-written cases (exclusions, numeric ranges, registration age, vague test names, "I don't know", fail-fast).

**Known limitations**

- **Question order is naive.** Follow-ups go to the first unresolved criterion in the trial's order. Smarter selection (grouping related criteria, prioritizing by how much a question can settle) is the main planned research component.
- **Slow.** One model call per criterion per message, about 10 seconds each on a free Kaggle GPU. Planned: stop after the first blocking criterion, cache verdicts, batch calls.
- **The model is cautious.** It sometimes answers "insufficient information" where a person would decide (for example, treating "stopped last year" as unclear). That is deliberate but costs extra questions.
- **Access control is incomplete.** Patients are scoped to their caregiver, but eligibility sessions are not yet checked against the logged-in caregiver.
- **Narrow rule coverage.** Numeric rules cover age, MMSE, CDR and MoCA; drug rules cover a few classes.
- **No formal evaluation yet**, and no frontend.
- **The AI service runs in a notebook.** Fine for development, not for production.

## Roadmap

- [ ] Ownership checks on sessions
- [ ] Faster judging (early exit, caching, batching)
- [ ] Structured criteria (type, category, split compound criteria), prepared offline
- [ ] LLM fact extraction: turn free text into facts once, decide from the facts
- [ ] Adaptive question selector
- [ ] Evaluation: synthetic patients, a simulated caregiver, questions-to-decision and error rates
- [ ] "Why are we asking this?" explanations and plain-language criterion explanations
- [ ] React frontend
- [ ] Stable hosting for the AI service

## Security notes

- Secrets live in `.env` and Kaggle Secrets only, never in code or notebooks.
- Login errors are identical for "unknown email" and "wrong password", accounts lock after repeated failures, and refresh tokens are stored hashed and rotated.
- Request bodies are validated with a whitelist; unknown fields are rejected.
- Use fake patient data during development.

## Author

Nada Ben Abdelhafidh

## License

<choose a license, or "All rights reserved" for now>
