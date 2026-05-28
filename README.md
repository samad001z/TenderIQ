# TenderIQ

> Audit-grade AI bid-evaluation portal for Indian government procurement.
> Seven specialist AI agents review every submitted bid against your tender —
> every recommendation is grounded in a **page-cited verbatim quote** from the
> bidder's own documents.

Built for the **OpenAI × Outskill AI Builders Hackathon 2026** with Claude
CLI as the pair-programmer.

---

## Table of contents

1. [Live URLs](#live-urls)
2. [Test accounts](#test-accounts)
3. [60-second guided tour](#60-second-guided-tour)
4. [Officer flow — post a new tender](#officer-flow--post-a-new-tender)
5. [Vendor flow — submit a bid](#vendor-flow--submit-a-bid)
6. [Officer flow — run the AI review](#officer-flow--run-the-ai-review)
7. [Glossary — what every flag means](#glossary--what-every-flag-means)
8. [The Citation contract (non-negotiable)](#the-citation-contract-non-negotiable)
9. [Architecture & stack](#architecture--stack)
10. [Local development](#local-development)
11. [Production deployment](#production-deployment)
12. [Secrets policy — why nothing leaks](#secrets-policy--why-nothing-leaks)

---

## Live URLs

| Surface | URL |
| --- | --- |
| **Web app (Vercel)** | _populated after `pwsh ./deploy/deploy-web.ps1`_ — paste the printed URL here once it's published |
| **API (Google Cloud Run, Mumbai)** | https://tenderiq-api-258401798733.asia-south1.run.app — `/health` and `/test-gemini` are live |
| **Source** | https://github.com/samad001z/TenderIQ |

> If you're cloning this repo and want it running on your own infrastructure,
> jump to [Local development](#local-development) → [Production deployment](#production-deployment).

---

## Test accounts

All seeded accounts share the same password: **`TenderIQ#2026`**

### Officer (the demo driver — start here)

| Email | Password |
| --- | --- |
| `officer@tenderiq.test` | `TenderIQ#2026` |

The officer can: publish a tender, watch the AI parse it, see all submitted bids,
trigger the multi-agent review, and download the audit PDF.

### Vendors / bidders (7 personas pre-seeded against the demo tender)

| Email | Org | Demo outcome |
| --- | --- | --- |
| `bidder.stellartech@tenderiq.test` | StellarTech Pvt Ltd | **L1 · AWARD** — eligible, compliant, fair price |
| `bidder.velocity@tenderiq.test` | Velocity Systems | **HUMAN REVIEW** — disagreement (OEM/MAF missing) |
| `bidder.budgetbuild@tenderiq.test` | BudgetBuild Co | **REJECT** — abnormally low + MII Class-II + BIS missing |
| `bidder.shadowbuild@tenderiq.test` | ShadowBuild Co | **REJECT** + duplicate flag (shell of BudgetBuild) |
| `bidder.meridian@tenderiq.test` | MeridianTech Solutions | **HUMAN REVIEW** — cartel cluster member |
| `bidder.orbit@tenderiq.test` | Orbit Infra | **HUMAN REVIEW** — cartel cluster member |
| `bidder.nexus@tenderiq.test` | NexusBuild Technologies | **HUMAN REVIEW** — cartel cluster member |

Sign in with any of these to see the bidder workspace — your already-submitted
bid, the eligibility & compliance pre-checks, and the comparison once the
officer has run the review.

---

## 60-second guided tour

1. Open the **live URL** above. Hit **Sign in** in the top-right.
2. Use `officer@tenderiq.test` / `TenderIQ#2026`.
3. You land on **Tenders**. The seeded *System Integrator — Package B* tender
   is `published` and `parsed`. Click **View review**.
4. Watch the SSE stream: 7 bids × 7 agents fan out. After ~30 s, you see the
   ranked table:

   - **L1 · AWARD** badge on StellarTech.
   - **HUMAN REVIEW** badges on Velocity + the cartel cluster (Meridian, Orbit, Nexus).
   - **REJECT** badges on BudgetBuild and ShadowBuild.
   - A red **DUPLICATE** chip on ShadowBuild and BudgetBuild.

5. Click **Velocity Systems** to expand the disagreement: technical PASS but
   compliance FAIL because the OEM/MAF letters are missing.
6. Click **Download audit report** to get the CAG-style signed PDF.

That's it.

---

## Officer flow — post a new tender

This is the path you take with a **fresh** tender PDF from CPPP / GeM / a
ministry portal.

### 1. Sign in as officer

- Open `/login`.
- Email **`officer@tenderiq.test`**, password **`TenderIQ#2026`** → **Sign in**.

### 2. Open the upload workspace

- Top-nav → **Tenders** → **+ New tender** (button top-right).
- You land on `/officer/tenders/new`.

### 3. Drop the tender PDF

- **Drag & drop** the tender PDF onto the dropzone, or click the dropzone and pick a file.
- The browser uploads the PDF to Supabase Storage (Mumbai region) and then
  starts a Server-Sent Events stream to the API.
- The left pane shows the PDF page-by-page. The right pane streams the parse:

  | Stage | What you see |
  | --- | --- |
  | `extracting_text` | "Reading 24 pages of born-digital text…" |
  | `parsing_with_pro` | "Gemini 2.5 Pro extracting the QCBS schema…" |
  | `schema_ready` | The parsed schema appears in the right pane |
  | `persisted` | Schema saved against the tender row in Postgres |

- Every field the model extracts comes with a **page citation** — click any
  field (Estimated Value, Eligibility, Submission Deadline, MII class, etc.)
  and the PDF viewer jumps to that page with the matching text **highlighted**.

### 4. Publish

- Review the schema. If everything looks right, click **Publish tender**.
- The tender flips to `published` and becomes visible to all bidders.

> **Why every parse cites a page**: Indian procurement is auditable. If the
> AI says "estimated value is ₹8.5 crore", a CAG auditor must be able to see
> the exact sentence on the exact page that produced that number. No citation,
> no decision.

---

## Vendor flow — submit a bid

### 1. Sign in as a bidder

- Open `/login`.
- Email **`bidder.stellartech@tenderiq.test`**, password **`TenderIQ#2026`**.
- (Or use any of the other six bidder emails — see [Test accounts](#test-accounts).)
- New vendors can sign up at `/signup` and choose **Bidder** as their role.

### 2. Browse open tenders

- Top-nav → **Open tenders**.
- You see published tenders with their estimated value, submission deadline,
  and the MII class restriction. Click any row to open it.

### 3. Read the tender summary

- The summary page shows the AI-extracted schema in plain English:

  - Estimated value (and what 70% / 80% of it is — the "abnormally-low" floor)
  - Eligibility criteria (turnover, experience)
  - Technical criteria & weights (for QCBS)
  - Financial format (Item-wise BoQ etc.)
  - **EMD** amount and how to remit it
  - **Integrity Pact** requirement (yes/no)
  - **PPP-MII class** restriction (Class-I / Class-II)
  - Submission deadline

- Hit **Apply for this tender**.

### 4. Section A — Eligibility self-check (live AI)

- The page reads your **bidder profile** (turnover, years in business, certifications).
- It calls the Eligibility Agent against the parsed tender criteria.
- You see a PASS / FAIL / FLAG verdict for each criterion with the tender's
  exact quote that drives it.
- If anything is FAIL, you can still proceed (officer sees it later) — but
  the system tells you you're unlikely to qualify.
- Tick **"I have reviewed the eligibility findings"** to unlock Section B.

### 5. Section B — Upload your bid documents

- **Technical bid PDF** — usually 15–25 pages: cover, profile, GST/PAN, turnover,
  past performance, ISO/CMMI certificates, technical approach, MII certificate,
  Integrity Pact, EMD receipt, OEM/MAF letters, BIS licence, signatory
  declaration.
- **Financial bid PDF** — the priced BoQ.
- Both upload to Supabase Storage. The financial bid is encrypted at rest by
  Postgres column policy until the officer triggers the review.

### 6. Section C — Pre-submission Compliance self-check (live AI)

- Runs the Compliance Agent against your uploaded technical PDF.
- You see flags for: PPP-MII (Class-I vs Class-II), Integrity Pact signed/not
  signed, EMD evidence, OEM/MAF presence, BIS certificate presence.
- Each flag carries a verbatim quote from your bid PDF, with the page number,
  so you know exactly what the system saw.
- If you spot a problem, you can re-upload and re-run. If you accept the
  findings (PASS or otherwise), hit **Submit bid**.

### 7. Submitted

- Your bid status moves from `draft` → `submitted`.
- You can see it under **My submissions**. You cannot edit it after submission.
- Once the officer runs the multi-agent review, the verdict appears on your
  submission card with the per-agent breakdown.

---

## Officer flow — run the AI review

1. Sign in as the officer.
2. Go to **Tenders** → click your published tender → **View review**.
3. Click **Run review**.
4. The Server-Sent Events stream lights up. For each bid you'll see:

   - `ingestion` — PDF text extraction + page indexing.
   - `eligibility` — turnover / experience / blacklist check.
   - `technical` — architecture, methodology, team strength (scored 0–100).
   - `compliance` — MII, Integrity Pact, EMD, OEM/MAF, BIS.
   - `financial` — quoted total vs estimate, abnormally-low check.
   - `risk` — deterministic rules (blacklist registry, cartel cluster, duplicate detection).
   - `reasoning` — the orchestrator: applies QCBS / L1 + disagreement logic to produce a final verdict.

5. The page settles on the **comparison matrix**: every bid as a row, every
   agent as a column, every cell shows the verdict + the citation pill you
   can click to expand the verbatim quote.

6. Final outcomes for the demo dataset:

   - StellarTech → **L1 · AWARD**
   - Velocity → **HUMAN REVIEW** (banner explains: tech PASS but compliance FAIL on OEM)
   - BudgetBuild → **REJECT** (abnormally-low + MII Class-II + BIS missing)
   - ShadowBuild → **REJECT** + DUPLICATE FLAG against BudgetBuild
   - Meridian / Orbit / Nexus → **HUMAN REVIEW** (cartel cluster, all three quote within ~1.5%)

7. Click **Download Audit Report** to get the signed CAG-style PDF: the
   ranking, every claim, every citation, officer sign-off line.

---

## Glossary — what every flag means

These are the terms you'll see surfaced in the UI as **chips, banners, and
verdict pills**. Each one maps to a piece of Indian government procurement
law / CVC guidance.

### Verdicts

| Verdict | What it means |
| --- | --- |
| **PASS** | The bidder satisfies this requirement. The agent has a verbatim quote from the bidder's PDF that proves it. |
| **FAIL** | The bidder does NOT satisfy this requirement. A verbatim quote (or its absence) is logged. |
| **FLAG** | Something is unusual but not automatically disqualifying — a human officer must decide. |
| **INFO** | Context only — no verdict implied. |

### Final-recommendation badges (reasoning_agent output)

| Badge | What it means |
| --- | --- |
| **L1 · AWARD** | Lowest evaluated bid (or highest QCBS score) among the technically responsive + compliant bidders. The reasoning agent recommends award. |
| **HUMAN REVIEW** | Either (a) the specialist agents **disagree** about responsiveness, or (b) a risk-rule flag fired (cartel / duplicate / abnormally-low). The system refuses to recommend and hands it to the officer. |
| **REJECT** | The bidder fails one or more eligibility / compliance gates. |

### Per-criterion flags

| Flag | What it means | Where it comes from |
| --- | --- | --- |
| **Turnover floor** | Bidder's audited 3-year average turnover is below the tender's minimum (typically ₹15–25 crore). | Eligibility Agent — reads CA-certified turnover statement and the tender's eligibility clause. |
| **Experience floor** | Bidder has fewer years in business than the tender requires (typically 5 years). | Eligibility Agent. |
| **Blacklist hit** | Bidder appears on the deterministic blacklist registry (CVC / CBI / world bank). | Risk Agent — `agents/blacklist.json`. |
| **PPP-MII Class-I** | The **Public Procurement (Preference to Make in India) Order**, DPIIT P-45021/2/2017-PP, restricts certain tenders to **Class-I local suppliers** (≥ 50% local content). A Class-II bidder (20–50% local content) on a Class-I tender → FAIL. | Compliance Agent. |
| **Integrity Pact** | A standard CVC instrument the bidder must sign promising no bribery, no cartel, no false documents. Missing or unsigned → FAIL. | Compliance Agent. |
| **EMD** | Earnest Money Deposit — a refundable deposit (typically 1–3% of estimate) the bidder pays as a token of seriousness. Missing UTR / wrong amount → FAIL. | Compliance Agent. |
| **OEM / MAF** | **Manufacturer's Authorisation Form** — a letter from Dell / Cisco / Microsoft etc. authorising the bidder to quote their products in this specific tender. Missing → FAIL. | Compliance Agent. |
| **BIS licence** | Bureau of Indian Standards mark licence. Required for tenders that involve regulated goods/services. Missing → FAIL. | Compliance Agent. |
| **ISO / CMMI** | ISO 9001 (quality), ISO/IEC 27001 (security), CMMI-DEV Level 5 (process maturity). Missing on a tender that requires them → FAIL. | Eligibility / Compliance Agent. |
| **Abnormally low** | Quoted price is **> 20% below the tender's estimated value**. CVC guidance: investigate sustainability before award. | Financial + Risk Agent. |
| **Cartel cluster** | **3 or more bidders quote within a 2-percentage-point band**. Statistically improbable in honest competition — CVC integrity flag. | Risk Agent (deterministic — no LLM call). |
| **Duplicate bidder** | Two or more submissions have near-identical content after normalising for legal name + contact details — a shell / proxy / cover bid. | Risk Agent (deterministic — Jaccard similarity on extracted text). |
| **Disagreement** | The Technical Agent says PASS but the Compliance Agent says FAIL (or vice-versa). The reasoning agent refuses to award and asks for human review. | Reasoning Agent. |

### Procurement methods

| Method | What it means | Used in the demo? |
| --- | --- | --- |
| **L1** | "Lowest 1" — lowest financially evaluated bid wins among responsive bidders. | Available — supported in the parser. |
| **QCBS** | "Quality- and Cost-Based Selection" — combined score = `(technical_score × technical_weight) + (financial_score × financial_weight)`. The demo tender uses **QCBS 70/30**. | Yes — drives the StellarTech AWARD recommendation. |

### Citation pieces every claim carries

Click any chip in the UI and you see all of these:

- **claim** — what the agent is asserting ("PPP-MII Class-I self-certification enclosed").
- **verdict** — PASS / FAIL / FLAG / INFO.
- **source_doc** — which PDF (technical / financial).
- **page_number** — 1-indexed.
- **quote** — verbatim text from that page.
- **tender_clause** + **tender_clause_page** — the tender requirement this maps to.
- **severity** — low / medium / high / critical.
- **agent** — which of the seven agents produced it.

---

## The Citation contract (non-negotiable)

Every AI-emitted claim conforms to `shared/citation.py`:

```python
class Citation(BaseModel):
    claim: str                 # human-readable assertion
    verdict: Literal["PASS", "FAIL", "FLAG", "INFO"]
    source_doc: str            # bid filename
    page_number: int           # 1-indexed; > 0 enforced
    quote: str                 # verbatim text from that page
    confidence: float
    tender_clause: Optional[str]
    tender_clause_page: Optional[int]
    severity: Literal["low", "medium", "high", "critical"]
    agent: str
```

The schema is passed to Gemini as `response_schema`. The orchestrator
**rejects + reruns** any claim with `page_number <= 0` or an empty `quote`,
and logs every rejection to `agent_runs.rejections`.

This is the moat — without it, AI bid evaluation is not defensible before a
CAG audit.

---

## Architecture & stack

```
                ┌──────────────┐
                │   Vercel     │  Next.js 15 (App Router, TS, Tailwind v3, shadcn/ui)
                │   /web       │  Officer + Bidder workspaces; SSE viewer
                └──────┬───────┘
                       │  HTTPS (CORS-locked to Vercel domain)
                       │
                ┌──────▼──────────────────┐
                │   Cloud Run             │  FastAPI (Python 3.12, uv)
                │   tenderiq-api          │  7 specialist agents + reasoning orchestrator
                │   asia-south1 / Mumbai  │  SSE via sse-starlette
                │   Runtime SA → Vertex   │  PyMuPDF page render + bbox highlight
                └──────┬──────┬───────────┘
                       │      │
       ┌───────────────▼─┐  ┌─▼──────────────────┐
       │  Vertex AI       │  │  Supabase (Mumbai) │
       │  Gemini 2.5 Pro  │  │  Postgres + RLS    │
       │  Gemini 2.5 Flash│  │  Auth (GoTrue)     │
       │  asia-south1 +   │  │  Storage           │
       │  global          │  └────────────────────┘
       └──────────────────┘
```

- **AI:** Gemini 2.5 Pro + Flash on Vertex AI. Flash runs in `asia-south1`,
  Pro routes to `global`. All structured outputs use Pydantic `response_schema`.
- **PDF:** PyMuPDF for born-digital text extraction + 2x page rendering;
  Pillow overlays the bbox returned by `page.search_for` for highlighted previews.
- **API:** FastAPI, SSE via `sse-starlette`, agents run in parallel per bid
  with `asyncio.gather` + threaded Gemini calls.
- **Web:** Next.js 15 (App Router, TS), Tailwind v3, shadcn/ui, dynamic
  PDF.js viewer.
- **Data:** Supabase Postgres + pgvector + Auth (GoTrue) + Storage (Mumbai)
  with strict Row-Level Security. The API uses the service-role key.
- **Audit PDF:** reportlab (Arial-registered so the ₹ glyph survives PDF text
  extraction).

---

## Local development

### Prereqs

- Node 18+ and npm
- [uv](https://docs.astral.sh/uv/) (manages Python 3.12)
- `gcp-key.json` (Vertex service-account JSON) at the repo root — **gitignored**
- A Supabase project (URL + service-role key) — schema lives in `supabase/migrations/`

### Setup

```bash
# 1. Secrets
cp .env.example .env.local        # fill values
# Drop gcp-key.json at the repo root.

# 2. Apply Supabase migrations (one-time)
#    Use the Supabase CLI or the dashboard SQL editor.

# 3. Backend
cd api && uv sync
uv run uvicorn main:app --port 8000

# 4. Frontend (new terminal)
cd web && npm install && npm run dev   # http://localhost:3000

# 5. Seed the 7 synthetic bids on the demo tender
cd api
uv run python scripts/generate_synthetic_bids.py
uv run python scripts/seed_synthetic_bids.py
```

### Hermetic demo (no Vertex / no Supabase)

```bash
cd api && uv run python scripts/mock_review_log.py
```

Drives the real orchestration with a fake Gemini over three synthetic
scenarios (QCBS ranking + blacklist + citation-gate rerun · disagreement +
abnormally-low · cartel) and prints the SSE event stream.

---

## Production deployment

| Layer | Where | Region |
| --- | --- | --- |
| `/web` | **Vercel** | global edge |
| `/api` | **Google Cloud Run** | `asia-south1` (Mumbai) |
| Postgres / Auth / Storage | **Supabase** | Mumbai |
| LLM inference | **Vertex AI** | Flash `asia-south1` · Pro `global` |

### Step 1 — Deploy the API to Cloud Run

```pwsh
cd C:\bid
pwsh ./deploy/deploy-api.ps1
```

This script:

1. Creates the Artifact Registry repo `tenderiq` in `asia-south1` (idempotent).
2. Creates the runtime service account `tenderiq-api@bids-497610.iam.gserviceaccount.com`
   and grants `roles/aiplatform.user` + `roles/secretmanager.secretAccessor`.
3. Pushes `SUPABASE_SERVICE_ROLE_KEY` to Secret Manager as `supabase-service-role-key`.
4. Submits a Cloud Build of the repo root (Dockerfile at `/Dockerfile`) producing
   a linux/amd64 image.
5. Deploys the image to Cloud Run as `tenderiq-api` (1 GiB / 2 vCPU,
   concurrency 20, max 3 instances, 600 s timeout for the SSE review stream).
6. Prints the public `https://tenderiq-api-...run.app` URL.

### Step 2 — Deploy the web to Vercel (manual, dashboard)

This is the path that works every time. Five minutes, no CLI.

1. Open https://vercel.com/new and click **Import** next to
   **samad001z/TenderIQ**.
2. **Configure Project**:
   - **Framework Preset:** Next.js (auto-detected)
   - **Root Directory:** `web` (click *Edit* and pick the `web` folder)
   - **Build & Output Settings:** leave defaults
3. **Environment Variables** — click *Add* three times and paste:

   | Name | Value |
   | --- | --- |
   | `NEXT_PUBLIC_SUPABASE_URL` | from `.env.local` (your Supabase project URL) |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | from `.env.local` (the `sb_publishable_...` value) |
   | `NEXT_PUBLIC_API_BASE_URL` | `https://tenderiq-api-258401798733.asia-south1.run.app` |

   All three are safe for the browser bundle (Row-Level Security enforces
   access on the Supabase side).

4. Hit **Deploy**. First build takes ~90 seconds.

> The repo is already pre-fixed for Vercel:
> - `/shared/citation.ts` is duplicated into `/web/shared/citation.ts` so the
>   `@shared/*` path alias resolves inside the build root.
> - `app/layout.tsx` declares `export const dynamic = "force-dynamic"`, so
>   Next's static prerender step doesn't evaluate Supabase modules at build
>   time. (Without this, missing env vars would trip the prerender even
>   though every route is a client component.)

### Step 2 (alternative) — Deploy via the CLI

```pwsh
# One-time only — opens your browser for the Vercel login
npx vercel login

# Push env vars + deploy
pwsh ./deploy/deploy-web.ps1
```

In CI: set `$env:VERCEL_TOKEN` first (https://vercel.com/account/tokens) and
the script runs non-interactively.

### Step 3 — Tighten CORS on the API

After Vercel publishes (e.g. `https://tenderiq.vercel.app`), redeploy the API
with that exact origin allowlisted:

```pwsh
$env:CORS_ORIGINS = "https://tenderiq.vercel.app,http://localhost:3000"
pwsh ./deploy/deploy-api.ps1
```

### Smoke test

```pwsh
$api = (gcloud run services describe tenderiq-api --region=asia-south1 --format='value(status.url)')
curl "$api/health"
# {"status":"ok","service":"tenderiq-api","project":"bids-497610","location":"asia-south1"}

curl -X POST "$api/test-gemini"
# {"status":"ready","model":"gemini-2.5-flash"}   ← proves Vertex ADC works on Cloud Run
```

---

## Secrets policy — why nothing leaks

This repo is safe to push to public GitHub. Here's why:

1. **`.env.local` and `gcp-key.json` are gitignored** at the repo root. They
   contain the Supabase service-role key and the Vertex service-account
   private key. `git status` will never list them.

2. **`.dockerignore` at the repo root** strips `.env*`, `gcp-key.json`,
   `*-key.json`, `*.pem`, the entire `/web` tree, `tests/`, `docs/`,
   `supabase/`, and `.claude/` from the Cloud Build context. The Cloud Run
   image only ever contains `/api/` + `/shared/` + the runtime deps.

3. **`SUPABASE_SERVICE_ROLE_KEY` lives in Google Secret Manager**, not in an
   env var. The deploy script reads it once from `.env.local` (via a temp file
   that's deleted on every run) and uploads it as a new Secret Manager
   version. Cloud Run mounts it via `--set-secrets`, not `--set-env-vars`, so
   it never appears in revision metadata or container logs. Rotate by adding
   a new secret version — no redeploy needed.

4. **Vertex AI auth uses the Cloud Run runtime service account**
   (`tenderiq-api@bids-497610.iam.gserviceaccount.com` with
   `roles/aiplatform.user`). No JSON private key is ever shipped in the
   image. Local dev uses `gcp-key.json` via ADC; production uses workload
   identity.

5. **The Supabase publishable key** (`NEXT_PUBLIC_SUPABASE_ANON_KEY`) is the
   *only* Supabase key that goes to the browser. Row-Level Security
   (`supabase/migrations/`) enforces who can see what — bidders only see their
   own bids, officers see all bids on tenders they own.

6. **CORS on the API is allowlist-only.** After the first deploy, the
   `CORS_ORIGINS` env var on Cloud Run is set to your exact Vercel domain
   plus `http://localhost:3000`. Cross-origin requests from anywhere else
   are rejected at the middleware layer.

---

## Monorepo layout

```
/web         Next.js — landing, auth, bidder portal, officer review workspace
/api         FastAPI — agent pipeline, SSE review endpoint, audit-PDF + page-highlight
/shared      Citation contract: citation.py (Pydantic) + citation.ts (manual sync)
/supabase    Forward-only migrations (001 → 008)
/tests       Synthetic bid PDFs + Playwright screenshots
/docs        CONTEXT_CARRY.md · PROMPTS_LOG.md · PITCH_DECK.md · DESIGN_SYSTEM.md
/deploy      deploy-api.ps1 (Cloud Run) · deploy-web.ps1 (Vercel) · README.md
Dockerfile   API container (repo-root context — includes /api + /shared)
```

---

## Built-with disclosures

- **Pair-programmer:** Claude CLI (every prompt logged in `docs/PROMPTS_LOG.md`)
- **Evaluation engine:** Google Gemini 2.5 Pro + Flash on Vertex AI
- **Hackathon track:** OpenAI × Outskill AI Builders Hackathon 2026 — Codex Org ID in the Phase 1 submission form
- **Codex / OpenAI substitution note:** the original brief mentioned Azure / OpenAI for the evaluation engine; we substituted Gemini on Vertex throughout (no Azure / OpenAI inference credentials available, and Vertex's `response_schema` is the cleanest way to enforce the Citation contract). The hackathon Codex Org ID is supplied as part of submission.
