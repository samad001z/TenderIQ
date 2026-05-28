# CONTEXT_CARRY.md

> Living handoff doc. Update at the end of every phase.

## Current state — end of PHASE 7 (2026-05-28)

Three things landed in this pass: a **duplicate-bidder detector** for the
"same documents, only the name differs" case, an **end-to-end gov-portal UI
restyle** of the officer area, and a sweep that **strips every model-name
reference** from user-facing surfaces (the brief asked for a portal that doesn't
name any LLM in the chrome).

### Duplicate / proxy submission detection
- `reasoning_agent.detect_duplicate_bidders(intels)` — character-shingle Jaccard
  (k=15) on the substantive technical pages (3–12) with bidder/contact names
  normalised out. Threshold 0.85 catches both exact clones and near-duplicates
  (e.g. a swapped paragraph or two).
- `reasoning_agent.duplicate_citation(intel, others, score)` — emits a page-
  grounded FLAG citation on the bidder-profile page of EACH bid in the cluster
  (real page + verbatim quote → passes the citation contract).
- `services/review_pipeline.stream_review` now collects the FULL ingested
  intels (`full_intels`) — the earlier wiring bug was that I passed the thin
  `{bid_id, tender_id, org_name}` arg list to the detector, which has no
  documents. Fixed: per-bid intel is appended after ingestion and the cross-bid
  detector runs on that.
- A `disagreement_detected[duplicate_bidders]` SSE event fires for each cluster
  with `{type, kind, match_score_pct, threshold_pct, note, bids[]}`. Persisted
  citations show up in `review-summary.bids[].agents['reasoning_agent']`.
- **Important policy decision:** duplicates do NOT override `bid_status` /
  `recommended_action` — the prior verdict (e.g. reject on eligibility) stands
  and the integrity flag is surfaced via banner + drawer + audit PDF. Cartel
  detection still DOES override (cluster of ≥3 within 2% goes to human review).

### 4th synthetic bid — ShadowBuild Co
- `api/scripts/generate_synthetic_bids.py` — ShadowBuild persona clones every
  BudgetBuild field except `slug / org_name / bidder_email`. Same contact name
  ("Suresh Patil"), same EMD UTR, same prose (so the technical narrative still
  reads "BudgetBuild will deliver…" inside ShadowBuild's PDF — a deliberately
  sloppy proxy submission, demo-perfect). The seed creates a 4th auth user.
- `seed_synthetic_bids.py` — switched the storage upload to `upsert: "true"`;
  the prior `remove + upload` pattern was silently no-op'ing on this bucket
  and the next upload was 409'ing on re-seed.

### Live verification (4-bid run on tender 24941876)
```
DISAGREEMENT [technical_vs_compliance] Velocity Systems
DISAGREEMENT [duplicate_bidders] ShadowBuild Co, BudgetBuild Co — 100.0% similarity
L1   award   StellarTech Pvt Ltd          ₹72,250,000 [evaluated]
L-   review  Velocity Systems             ₹68,000,000 [human_review_required]
L-   reject  ShadowBuild Co               ₹44,200,000 [rejected]
L-   reject  BudgetBuild Co               ₹44,200,000 [rejected]
```
Each duplicate bid carries a `reasoning_agent` FLAG citation grounded on its own
bidder-profile page. `audit-pdf` returns 142 KB; `review-summary` resolves all
four bids with their full agent claim grids.

### Government-portal UI restyle (officer area only)
- **Tokens (`tailwind.config.ts`)** — new `gov-*` palette (light institutional):
  bg `#F4F6F9`, surface `#FFFFFF`, ink `#0B2545` (navy), navy CTA `#003875`,
  saffron `#FF9933` (national + L1 accent), green `#138808` (national + PASS),
  maroon `#7A1B2E` (formal accent + FAIL). The original obsidian/carbon dark
  tokens are kept for the auth + bidder pages.
- **Shell** — new `components/shell/gov-{shell,header,nav,footer,emblem,logout-
  button}.tsx`:
  - Tricolor strip (saffron / white / green) at the top
  - Stylised circular emblem (concentric rings + 24 spokes + tricolor base) —
    institutional-looking but deliberately NOT the protected State Emblem
  - Header: emblem + "TenderIQ — Government Procurement Evaluation Portal" +
    "Officer Review Workspace · Central Public Procurement Cell"; right side
    shows the signed-in officer's name + ministry
  - Utility bar: skip-to-main link, date stamp, A-/A/A+ font-size buttons
  - Horizontal primary nav (Dashboard, Tenders, New Tender) in deep navy with
    saffron underline on the active tab
  - Multi-column footer: About, Quick Links, Statutory References, Contact;
    last-reviewed date + disclaimer/privacy/sitemap row
- **Officer pages restyled** to gov-light: `dashboard` (stat tiles + recent
  tenders), `tenders` (institutional table with alternating-row tint), `tenders/
  new` (gov dropzone + progress steps; SchemaPreview also restyled), and the
  whole `tenders/[id]/review` flow (header, terminal log, agent grid, ranking
  header, comparison matrix, citation drawer, page-highlight modal, the
  disagreement banner).
- **Breadcrumbs** added (`GovBreadcrumb`) — Home › Tenders › Review.
- **DisagreementBanner** now recognises `duplicate_bidders` (Copy icon, "Possible
  duplicate submission" headline, bids shown as cards) and `abnormally_low_bid`.
- Auth + bidder pages **deliberately kept** on the obsidian/carbon dark theme —
  the gov skin is exclusively the officer review workspace, per "narrow scope".

### Model-name strip
- Removed "Gemini 2.5 Pro" from the SSE progress message in
  `routes/tenders.py::/parse` and "Gemini" from `routes/bids.py::/eligibility-
  check`. Removed the new-tender page's "extracts a schema with Gemini 2.5 Pro"
  copy. Removed "OpenAI × Outskill · Built with Claude CLI" from the auth
  brand pane (now reads "Government Procurement Evaluation Portal · Central
  Public Procurement Cell"). Internal code comments / module docstrings still
  reference Gemini for engineering clarity — those aren't user-facing.

### Verified
- `npx tsc --noEmit` clean across `/web`. All 3 officer routes compile in dev
  (315 modules each). Live review run produces both the tech-vs-compliance
  disagreement and the duplicate-bidders disagreement; audit PDF includes the
  integrity-flag citations.

### Phase-8 follow-ups (deferred)
- Public bidder + auth pages still use the obsidian/carbon dark theme. If the
  portal needs to read end-to-end as government, those would migrate too — but
  the user explicitly asked to keep this narrow to "the website" (interpreted as
  the officer review workspace, which is the demo focus).
- A cartel-overlap test (3+ priced bids within 2%) isn't part of the 4-bid demo
  — `scripts/mock_review_log.py` scenario C still covers it for the SSE log.

## Current state — end of PHASE 6 (2026-05-28)

Officer **Bid Review screen** is live end-to-end on the seeded demo tender
**24941876** (System Integrator — Package B, QCBS 70/30, MII-I, est ₹8.5 cr). All
three Phase-6 deliverables work against real data: synthetic bids → SSE pipeline
→ comparison matrix → citation drawer → server-rendered page-highlight PNG →
downloadable audit PDF.

### Demo narrative (deterministic by design)
- **A · StellarTech Pvt Ltd** → AWARD (QCBS L1, combined ~91, quoted ₹7.22 cr / 85% of estimate)
- **B · Velocity Systems** → HUMAN REVIEW (technical PASS/FLAG **conflicts** with compliance FAIL — OEM/MAF not enclosed; the orchestrator surfaces the disagreement event and refuses to recommend)
- **C · BudgetBuild Co** → REJECT (turnover ₹16.5 cr below ₹25 cr bar; CMMI Level 5 not held; BIS/ISO 27001 not held; quoted 52% — abnormally low; technical weak)

### Synthetic bids
- `tests/synthetic_bids/{stellartech,velocity,budgetbuild}_{technical,financial}.pdf` —
  reportlab, stable per-bid layout (p.5 = turnover & experience, p.10 = MII, p.11 =
  Integrity Pact, p.12 = EMD, p.13 = OEM, p.14 = BIS/ISO, p.15 = signatures). Arial
  TTF registered so ₹ glyph survives extraction.
- `api/scripts/generate_synthetic_bids.py` — hand-crafted prose templated per
  persona (gpt-4o-mini replaced by deterministic templates: no OpenAI creds, AND
  demo determinism matters more than LLM authorship of fixture content).
- `api/scripts/seed_synthetic_bids.py` — creates 3 bidder auth users via Supabase
  admin API, upserts profiles + bids, re-uploads to `bidder-docs/`, and CLEARS
  prior agent_runs/citations/recommendations + nulls bids.review_rank/scores so
  re-seeds are a true clean slate.

### Backend additions
- `services/page_highlight.py` — PyMuPDF renders the page at 2x with a gold rect
  over `page.search_for(quote)` rects. Progressive truncation falls back when the
  LLM-paraphrased quote isn't found verbatim; if no match, still returns the page
  (X-Highlight-Matched=0 header). Real bbox highlighting — no react-pdf bundler
  fight (the existing PdfViewer iframe is unchanged for the tender PDF preview).
- `services/audit_pdf.py` — CAG-style report (reportlab): cover + tender meta,
  exec summary with the recommendation / HUMAN-REVIEW callout, ranking table,
  disagreements section, per-bid sections with the full per-agent claim grid
  (verdict + severity + claim + citation + verbatim quote), then a sign-off page
  with officer name/designation/date.
- `routes/review.py` — three officer endpoints (own the tender):
  `GET /api/bids/{id}/page-highlight?source_doc&page&quote` → PNG;
  `GET /api/tenders/{id}/review-summary` → ranking + per-bid agent-grouped
  claims for the matrix (post-refresh restore); `GET /api/tenders/{id}/audit-pdf`.
- Migration `008_review_scores` — `bids.technical_score / financial_score /
  combined_score / review_rank` and `tenders.last_reviewed_at`. The orchestrator
  persists scores at orchestrator_complete and stamps the tender. `DbPersist`
  now passes `None` through (not filtered) so re-runs overwrite stale values.

### Prompt tuning (the part that took the most iteration)
- `eligibility_agent` — added numerical-comparison guidance (₹27 cr is ABOVE a
  ₹3 cr bar; default to PASS when the requirement is met) — Gemini was inverting
  the comparison on past-experience criteria.
- `technical_agent` — explicit scope: ignore the index, compliance, EMD, OEM and
  certification pages; a missing OEM is NEVER a technical failure (it kept
  leaking into a technical FAIL via the index page).
- `reasoning_agent.synthesize_bid` — disagreement rule broadened to
  `technical ∈ {PASS, FLAG} AND compliance == FAIL` (spec's "PASS-vs-FAIL"
  spirit; covers the case where technical correctly flags a real ambiguity but
  the hard compliance miss is the actual story).
- Bid PDFs — annotated past-project values with "(above the ₹3 crore tender
  minimum)" inline; OEM-missing page changed from "[PENDING — to be furnished]"
  (compliance read as FLAG: future commitment) to "NOT ENCLOSED with this bid"
  (unambiguous FAIL). Velocity certs corrected to CMMI L5 + ISO 27001:2013 to
  match the tender's exact wording so the disagreement gets its chance to fire.

### Frontend
- `/officer/tenders` — list of officer-owned tenders with status/method/estimate/
  bid-count + a gold "Run AI Review (N)" button per row (reviewed tenders show a
  ✓ "reviewed" badge and "View review" instead). Sidebar "Tenders" now live.
- `/officer/tenders/[id]/review` — the demo screen. Hydrates from
  `/review-summary`; if not yet reviewed, shows an empty-state with the **Run AI
  Review** button. While running, the page splits 60/40:
  - LEFT 60% — `AgentTerminal`: JetBrains-Mono SSE log with gold `+0.0s`
    timestamps and UPPERCASE agent names, auto-scrolling.
  - RIGHT 40% — `AgentGrid`: 7 agents × N bids; per-cell pulsing-gold loader →
    green check / verdict dot / red ✕ with elapsed time + running claim count.
  On `orchestrator_complete` it re-fetches the summary and flips to the
  comparison-matrix view:
  - `RankingHeader` — "Recommended: {bidder}" or "HUMAN REVIEW REQUIRED" in red;
    compact 3-up strip showing each bid's rank/action/quote/combined score.
  - `DisagreementBanner` — thick gold-bordered card per disagreement
    (tech-vs-compliance shows the conflicting claims side-by-side; cartel shows
    the clustered bids); clicking a citation pill jumps to the highlight modal.
  - `ComparisonMatrix` — bidders × [Eligibility | Technical | Compliance |
    Financial | Risk | Final]; each cell is a verdict pill + score (where
    relevant) + citation count, clickable.
  - `CitationDrawer` — 400px right slide-in with the agent's claims; each card
    has verdict pill, severity dot, quote in Cormorant italic, citation pill,
    confidence bar. Clicking a citation pill →
  - `PageHighlightModal` — centered modal showing the bid page rendered with the
    gold rectangle drawn over the quoted text (server-side PyMuPDF + Pillow);
    falls back gracefully if the quote isn't located on the page.
  - `Download Audit Report` button — fetches the audit PDF as a blob and opens it
    in a new tab.

### Verified
- Live SSE run on the 3 seeded bids (`scripts/e2e_review.py`) emits the
  `disagreement_detected [technical_vs_compliance]` event for Velocity Systems;
  final orchestrator_complete payload: award=StellarTech, human_review=[Velocity],
  reject=BudgetBuild.
- `review-summary` returns 5 agents × N claims per bid, with `review_rank=null`
  for the human-review bid (score-clear fix took effect).
- `page-highlight` returns `X-Highlight-Matched: 1` and a 61 KB PNG for the OEM
  FAIL claim on `velocity_technical.pdf` p.13.
- `audit-pdf` returns a 132 KB PDF.
- `npx tsc --noEmit` clean across `/web`.

### Notes / Phase-7 follow-ups
- The Gemini-vs-gpt-4o-mini substitution + hand-crafted bid prose are documented
  in PROMPTS_LOG.md alongside the same call from earlier phases.
- Re-running a review is supported (the score-clear fix + the seed's
  artifact-clear keep it idempotent in practice; a true in-pipeline purge would
  remove the requirement to re-seed before re-running).
- Cartel detection is implemented but the demo's 3 bids are spread too widely
  for the cluster (8.2/7.2/4.4 cr); the mock_review_log.py scenario C already
  exercises this path with synthetic prices.

## Current state — end of PHASE 5 (2026-05-28)

The officer-side **7-agent review pipeline** is built and streams live. `POST
/api/tenders/{id}/review` (officer, owns tender) runs the agents over every submitted
bid and emits SSE: `review_start, bid_start, agent_start, claim_emitted, agent_complete,
disagreement_detected, orchestrator_complete` (+ `review_error`). In-stack with **Gemini
2.5 Pro** (the Phase-3/4 decision — the Phase-5 brief said "Azure OpenAI gpt-4o" but no
Azure creds exist; structured output via `response_schema` + the `Citation` contract is
equivalent).

### Agents (`api/agents/`, one file each; uniform `async run(tender_schema, bid_id, bid_doc_intel, *, gemini=None) -> AgentResult`)
- `base.py` — `AgentResult`; the **citation gate** (`page_number>0` + non-empty `quote`)
  and `run_structured_citation_agent` which **rejects + RERUNS** (bounded) any claim
  missing page/quote, collecting `rejections` for `agent_runs.rejections`. Bid/tender
  context builders.
- `ingestion_agent` (reuse PyMuPDF) → builds `bid_doc_intel` (page-labeled text + org_name
  + quoted_amount). `tender_parser_agent` (reuse) → references the Phase-3 parsed schema.
- `eligibility_agent`, `technical_agent` (emits `technical_score` for QCBS),
  `compliance_agent` (PPP-MII Class-I, Integrity Pact, EMD, OEM MAF, BIS/ISO currency),
  `financial_agent` (extracts quoted total + **deterministic abnormally-low: >20% below
  estimate per CVC**), `risk_agent` (deterministic blacklist vs `agents/blacklist.json`).
- `reasoning_agent` (orchestrator — not run()-shaped): `synthesize_bid` rolls up the 5
  specialists + **detects the Technical-PASS/Compliance-FAIL disagreement → refuses to
  recommend, parks bid `human_review_required`, surfaces conflicting claims**;
  `detect_cartel` (3+ bids within 2%, CVC Circular 4/3/07 → human review + price-grounded
  FLAG citations); `rank_and_recommend` applies **L1** (lowest among eligibility-passed) or
  **QCBS** (weighted technical+financial).
- `services/review_pipeline.py` — `stream_review` async generator (5 specialists run
  concurrently per bid via `as_completed`, each offloading the blocking Gemini call to a
  thread). `DbPersist` writes `agent_runs` + `citations` + `recommendations` and updates
  `bids.status`; `NullPersist` for hermetic tests. `models/agent_io.py`
  (TechnicalAnalysis/FinancialAnalysis).

### DB
- Migration `007_agent_review` — added `human_review_required` to the `bids.status` check
  (applied via Supabase MCP). No other schema change needed (001 already had agent_runs /
  citations / recommendations).

### Verified
- `scripts/mock_review_log.py` (FakeGemini + NullPersist, **no Vertex/DB**) drives the REAL
  orchestration over 3 synthetic bids × 3 scenarios and prints the SSE log: (A) QCBS
  ranking L1/L2 + blacklist reject + **citation-gate rerun** (`rej=1`); (B) tech-vs-compliance
  **disagreement** + **abnormally-low** → human review, Meridian awarded; (C) L1 **cartel**
  → all human review, no award. App imports clean; `/review` route registered.
- `scripts/e2e_review.py` — live trigger (officer token → SSE) ready for the Phase-6 bids.
  Run the API WITHOUT `--reload` (per Phase 3 note).

### Open items for PHASE 6
- The **3 real synthetic bids** land here → run `e2e_review.py` live (real Gemini + persist).
- Officer review **UI**: consume the SSE, render the citation grid (page-jump chips), the
  disagreement/cartel banners, and the ranking. Bidder-result visibility decision still pending.
- Live run accumulates new `agent_runs`/`citations` each time (no auto-clear); add a
  pre-review purge if re-runs are expected.

## Current state — end of PHASE 4 (2026-05-27)

Bidder side is end-to-end: browse → detail → apply (eligibility pre-check + uploads + compliance
check) → submit → submissions. All AI in-stack with Gemini (Section C "Azure Doc Intel" → Gemini,
consistent with Phase 3).

### Bidder portal = warmer variant
- Added `carbon #14110D` (+ surface/elevated). Shell moved OUT of `(app)/layout` (now gate-only)
  INTO role layouts: `bidder/layout` renders `<AppShell tone="carbon">`, `officer/layout` obsidian.
- Migration `006_bidder_capability_fields`: profiles + annual_turnover, years_in_business,
  mse_status, certifications[]. Seeded Meridian (strong: 30cr/8y/CMMI5+ISO27001) and Orbit
  (weak: 12cr/3y/ISO9001). Published 2 parsed tenders (one closing in ~5 days → gold deadline).

### API
- `current_user` / `current_bidder` deps (in supabase_client). `GET /api/tenders/{id}/file-url`
  (any authed, published-or-owner → signed URL, so bidders can view the tender PDF).
- `routes/bids.py`: `POST /api/bids/ensure` (get-or-create draft bid), `/{id}/eligibility-check`
  (SSE), `/{id}/documents` (upload technical|financial to bidder-docs), `/{id}/compliance-check`
  (SSE), `/{id}/submit` (requires both docs).
- `services/bid_agents.py` (Gemini 2.5 Pro): `check_eligibility` (capability profile vs
  eligibility_criteria → verdict + tender-page citation per criterion) and `check_compliance`
  (bidder's OWN bid PDF vs tender requirements → findings citing the bid's pages; page 0 = MISSING).
  Models: `models/eligibility.py`, `models/compliance.py`. Added dep none new.

### Web (bidder, carbon)
- `/bidder/tenders` — table: Title, Ministry, ₹ Indian value, Deadline (gold if <7d), eval pill.
- `/bidder/tenders/[id]` — split: native PDF left, collapsible Eligibility/Technical/Financial/
  Compliance sections right (citation chips jump the PDF), gold "Apply to this Tender".
- `/bidder/tenders/[id]/apply` — Section A SSE eligibility (verdict + citation pills; FAIL →
  "Continue anyway"), Section B two dropzones (technical+financial), Section C SSE compliance
  ("AI-as-friend", page-cited / "missing" tags), Submit gated on both uploads → redirects to:
- `/bidder/submissions` — status pills (Submitted/Under Review/Award/Rejected).
- `lib/api.ts` extended (ensureBid, uploadBidDoc, submitBid, file-url, generic postSSE + eligibility/
  compliance streams). `lib/format.ts` (formatINR Indian grouping, daysUntil). Bidder nav updated.

### Verified E2E (`api/scripts/e2e_bid.py`)
- Orbit (weak): eligibility 3 FAIL + 2 FLAG (page-cited); uploads 200; compliance flagged **9 missing**
  items helpfully; submit → `submitted`. Meridian (strong): 3 PASS + 2 FLAG. `next build` passes
  (all bidder routes), unauth bidder routes 307 → /login.

### Notes
- E2E used the tender PDF as a stand-in technical/financial bid, so compliance flags everything as
  "missing" — which actually showcases the friend feature. Real bidders upload real bids via the UI.
- Compliance `page_number=0` means "required but absent" — intentionally NOT the strict page>0
  Citation gate (that gate is for the 7 evaluator agents in the officer review phase).

## What PHASE 5 likely needs
- Officer review workspace: run the **7 evaluator agents** over a submitted bid vs the tender_schema,
  emitting Citation rows (enforcing page>0 + non-empty quote, logging rejections to
  `agent_runs.rejections`), agent_runs, and a recommendation. Officer tender publish UI.
  Then Day-5 polish (and the real DESIGN_SYSTEM.md token swap).

---

## PHASE 3 (history) — (2026-05-27)

PDF ingestion + tender-schema extraction working end-to-end, **in-stack with Gemini** (Samad
chose Gemini over the Phase-3-specced Azure; no Azure/OpenAI creds exist anyway).

### Engine & key fix
- Pipeline: PyMuPDF per-page text (→ `tenders.parsed_layout`) → Gemini 2.5 Pro with
  `response_schema=TenderSchema` (→ `tenders.parsed_schema`), every field carrying
  `source_page` + verbatim `quote`. Born-digital CPPP PDFs ⇒ text extraction (fast, 60pp OK);
  image rendering (`pdf_pages`) stays for the evaluator agents / scanned docs.
- **Gemini 2.5 Pro is NOT served in asia-south1** (404); Flash is. Fixed: `GeminiService` now
  routes Pro to `GEMINI_PRO_LOCATION` (default `global`), Flash stays `asia-south1`. Two clients.
- **Storage buckets did not exist** on this project — created `tender-docs`, `bidder-docs`,
  `audit-reports` (private, PDF-only, 50 MB). PDFs served to the browser via signed URLs.

### API (`/api`, single-process uvicorn — note below)
- `models/tender_schema.py` — TenderSchema (Sourced fields + eligibility/technical lists,
  evaluation_method L1/QCBS/LCS, qcbs_weights, financial_format, EMD, PBG, integrity_pact, MII, deadline).
- `services/supabase_client.py` — service-role client, `current_officer` (verifies Supabase JWT via
  GoTrue `/auth/v1/user`), `signed_url`.
- `services/tender_parser.py` — `extract_layout` (PyMuPDF text+tables) + `parse_tender_from_layout` (Gemini Pro).
- `routes/tenders.py` — `POST /api/tenders/upload` (creates tender + stores PDF + tender_documents row),
  `POST /api/tenders/{id}/parse` (SSE progress, persists layout+schema), `GET /api/tenders/{id}`.
- Added dep `python-multipart`. Migration `005_tender_parsing` added the parse columns.
- ⚠ **Run the API without `--reload`** (`uv run uvicorn main:app --port 8000`). The WatchFiles
  reloader spawned orphan workers that held port 8000 (whack-a-mole). Single process is stable.

### Web
- `/officer/tenders/new` — Stripe-style drag-drop dropzone (dashed gold on hover), live SSE progress
  (Uploading → Downloading → Reading → Extracting → Detecting), then a split view: react-pdf on the
  left, the extracted schema on the right with clickable `p.N` chips that jump the PDF to the source
  page. Added to officer sidebar nav.
- `lib/api.ts` (token + upload + fetch-based SSE reader), `lib/tender-schema.ts` (TS mirror),
  `components/officer/pdf-viewer.tsx` (react-pdf, dynamic ssr:false, worker via unpkg CDN),
  `components/officer/schema-preview.tsx`.
- **`next build` passes** (all 13 routes; react-pdf code-split out of the initial bundle).

### Verified E2E (synthetic fixture `api/fixtures/sample_tender.pdf`, 11 pp)
officer token → upload → SSE parse → Gemini extracted: QCBS @ 70/30, 5 eligibility criteria,
4 weighted technical criteria, value ₹8.5cr, EMD ₹8.5L (p.1), PBG 10% (p.7), integrity pact
required (p.7), MII Class-I (p.8), deadline (p.2) — all page-cited. `parsed_schema` persisted.
Dev scripts: `scripts/e2e_parse.py`, `scripts/probe_models.py`, `fixtures/make_sample_tender.py`.

### Notes / decisions
- tender_schema fields use `source_page=0` / empty quote when a field is genuinely absent — this is
  schema extraction, distinct from the strict `page>0` + non-empty-quote Citation gate that the 7
  evaluator agents must satisfy (Phase 4+).
- Real CPPP PDFs: drop them into `/officer/tenders/new` (Samad to test 2 from eprocure.gov.in).
- Storage RLS for direct client reads not added (signed URLs cover Phase 3 needs).

## What PHASE 4 likely needs
- Bidder bid upload (bidder-docs) + the 7 evaluator agents comparing bid docs against the tender's
  `parsed_schema`, emitting Citation rows (enforcing the page>0/non-empty-quote gate, logging
  rejections to `agent_runs.rejections`) + agent_runs + recommendations.
- Tender publish flow (draft → published) so bidders can see/bid; officer review workspace.

---

## PHASE 2 (history) — (2026-05-27)

Database schema + RLS live on Supabase; two-role auth working in Next.js, verified end-to-end.

### Supabase (project `cngwlsnygpmapvmwagsa` — "BidScrutiny", region ap-northeast-1 / Tokyo)
> Region is Tokyo, not Mumbai. **Accepted constraint** — Supabase free tier can't relocate a project, and
> we're staying on free tier. Not an open issue; just a data-residency note for a future paid migration.

- **8 tables**, all RLS-enabled: `profiles`, `tenders`, `tender_documents`, `bids`, `bid_documents`,
  `agent_runs` (has `rejections jsonb` per the Citation contract), `citations` (denormalized audit grid,
  mirrors `shared/citation.py`), `recommendations`. pgvector extension enabled for Phase 3.
- **Migrations** (forward-only, in `supabase/migrations/`, applied via Supabase MCP):
  - `001_initial` — schema + RLS + `handle_new_user` trigger (auto-creates profile from signup metadata)
    + `set_updated_at` triggers + `is_officer()`/`is_bidder()` helpers.
  - `002_harden_functions` — pinned search_path; (mistakenly switched helpers to INVOKER — see 003).
  - `003_fix_role_helper_recursion` — **reverted helpers to SECURITY DEFINER.** INVOKER caused infinite
    recursion: helpers read `profiles`, and a `profiles` policy calls `is_officer()`. DEFINER bypasses
    that internal RLS. Revoked EXECUTE from public, granted to authenticated.
  - `004_revoke_anon_role_helpers` — revoked helper EXECUTE from `anon` explicitly (Supabase default
    privileges had granted it). Verified `anon` can no longer call them.
- **RLS model** (service_role bypasses all — used by FastAPI):
  - Bidders: own profile, own bids, own bid_documents, and `status='published'` tenders only.
  - Officers: tenders they own (any status), bids on those tenders, those bids' documents/agent_runs/
    citations/recommendations, and the profiles of bidders who bid on their tenders.
  - Only officers can INSERT tenders; only bidders can INSERT bids (enforced via helper in WITH CHECK).
- **Security advisors:** the only remaining lints are (a) `authenticated can execute is_officer/is_bidder`
  — REQUIRED for RLS, benign (returns only the caller's own role); (b) `leaked_password_protection`
  disabled — a Supabase Auth dashboard toggle, not code. No ERROR-level lints, no missing-RLS.

### RLS verified (SQL impersonation via `set local role authenticated` + jwt claims)
| Actor | tenders | draft visible | bids | other bidder's bids | profiles |
|------|--------:|-------------:|----:|--------------------:|---------:|
| Officer (Anita) | 2 | 1 | 2 | — | 3 |
| Bidder A (Meridian) | 1 | 0 | 1 | 0 | 1 |
| Bidder B (Orbit) | 1 | 0 | 1 | 0 | 1 |

Plus write-side: a bidder INSERT into `tenders` is rejected — `new row violates row-level security policy`.

### /web auth
- `@supabase/ssr` clients: `lib/supabase/client.ts` (browser, cookie-based), `lib/supabase/server.ts`
  (RSC/actions). `middleware.ts` refreshes the session + routes: unauth→/login, authed-on-auth-page→home,
  not-onboarded→/onboarding, role mismatch→own home. (Routing uses `user_metadata`; **DB RLS is the real
  boundary.**)
- Routes:
  - `(auth)` group, Linear-style two-pane shell (obsidian brand pane + form): `/login`, `/signup`
    (role selector Bidder/Officer → email/pw → metadata role), `/onboarding` (role-specific fields:
    GST/PAN for bidders, ministry/department for officers; sets profile + `onboarding_complete`).
  - `(app)` group = auth+onboarded gate + `AppShell`; nested `/bidder/*` and `/officer/*` each role-gated
    (DB role authoritative). Landings: `/bidder/tenders`, `/officer/dashboard` (placeholders).
  - Root `/` is a server redirector (login→onboarding→role home). `/design-test` is public (own AppShell layout).
- Sidebar is role-aware (officer vs bidder nav, future items marked "soon") + shows user + Sign out.
- **Verified:** all 3 seeded users sign in via the publishable key (session + correct role + onboarded);
  protected routes 307→/login when unauthenticated; auth/design pages 200.

### Test data (seeded via `web/scripts/seed_test_users.mjs`, service role, password `TenderIQ#2026`)
- Officer `officer@tenderiq.test` (Anita Deshpande, MoRTH) — owns 1 published + 1 draft tender.
- Bidder `bidder.meridian@tenderiq.test` (Meridian Infra) — 1 bid on the published tender.
- Bidder `bidder.orbit@tenderiq.test` (Orbit Engineering) — 1 bid on the published tender.
- Re-runnable: `node --env-file=../.env.local scripts/seed_test_users.mjs` (deletes & recreates).
- `web/scripts/verify_login.mjs` — E2E sign-in check.

### Email confirmation — RESOLVED in code
UI signup no longer depends on the dashboard "Confirm email" toggle. `POST /api/auth/signup`
(`web/app/api/auth/signup/route.ts`, Next route handler) creates an **email-confirmed** user via the
service role (`web/lib/supabase/admin.ts`, server-only), then the client signs in to set the session and
flows to `/onboarding`. Verified: 200 on create, 409 on duplicate, 400 on bad input, and the created user
signs in with `email_confirmed_at` set. Service-role key lives in `web/.env.local` (server-only, gitignored).
> Production note: this auto-confirms every signup — fine for the demo; real deployment would re-enable
> email verification (and officer invite/verify) instead.

### Decisions made (told, not asked)
- No table schema existed in the master spec → designed columns myself (statuses, FKs, indexes, uniques).
- Self-selected role at signup is BY DESIGN (public Bidder/Officer chooser) — `handle_new_user` trusts
  signup metadata for role. Real gov deployments would invite/verify officers (noted for later).
- Officers can also read bidder profiles for bids on their tenders (additive policy) — needed for the
  review UI later; doesn't widen bidder access.

## What PHASE 3 likely needs (confirm when pasted)
- Storage wiring: upload tender_documents (tender-docs bucket) + bid_documents (bidder-docs bucket) with
  Storage RLS mirroring table RLS. FastAPI service client for server-side writes.
- Tender create/publish (officer) + tender browse/bid submit (bidder) UI.
- Begin the 7-agent orchestrator: PDF→pages→Gemini→Citation rows, enforcing the page>0/non-empty-quote
  gate and logging rejections to `agent_runs.rejections`.

## Open items / watch-outs
- `react-pdf` still unused (pdf.js worker config deferred to the viewer phase).
- Hex design tokens still provisional — real DESIGN_SYSTEM.md not yet pasted.
- `agent_runs`/`citations`/`recommendations` are currently officer-readable only; bidders seeing results
  about their own bid (post-evaluation) is a deliberate later decision.
- Root & web `.env.local` are separate on purpose (API vs Next). Both gitignored.
