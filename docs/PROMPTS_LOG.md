# PROMPTS_LOG

A record of every prompt Samad gave Claude CLI while building TenderIQ, for the README "built with Claude CLI" note.

---

## Prompt 0 — Project Kickoff (2026-05-27)

> You are my pair-programmer building TenderIQ over 7 days for the OpenAI × Outskill AI Builders Hackathon. I'm Samad, a student in Hyderabad.
>
> Established the project (TenderIQ — AI-native two-sided govt bidding platform), resources (Vertex AI / Gemini 2.5 Pro + Flash in asia-south1, Supabase Mumbai, Vercel + Render), the locked stack (Next.js 15 + FastAPI + google-genai SDK + PyMuPDF + Supabase pgvector), the design language (Bloomberg × Linear × Stripe; obsidian + gold + cream), the non-negotiable Citation contract (Pydantic schema, orchestrator rejects page_number<=0 or empty quote), the Gemini usage pattern (interleaved page-labeled PIL images, responseSchema, BLOCK_NONE safety for harassment/hate, temp 0.1 for evaluators), and the work style.
>
> Asked: confirm read & ready for PHASE 1; DESIGN_SYSTEM.md to be pasted next.

---

## Prompt 1 — PHASE 1: Monorepo scaffold + design tokens + Gemini Vertex wiring (2026-05-27)

> Goal: working Next.js + FastAPI monorepo running locally with the design system loaded, env wired, and Gemini Vertex reachable.
>
> 1. Monorepo: /web (Next.js 15 App Router + TS + Tailwind + shadcn), /api (FastAPI 3.12, uv), /shared (Pydantic + matching TS types), /docs.
> 2. /web: install tailwind, shadcn (init), lucide-react, react-pdf, @supabase/ssr, @supabase/supabase-js, sse.js. tailwind.config.ts loads tokens/fonts/spacing from DESIGN_SYSTEM.md EXACTLY; lock borderRadius. next/font for Cormorant Garamond + DM Sans + JetBrains Mono (Latin+Devanagari subset for the first two). Layout shell: 240px obsidian sidebar w/ gold active strip, 56px topbar w/ smoke border-bottom, max-w-1440 content. /design-test page rendering one of every component (buttons, input, card, table row, citation pill, verdict pills, agent card w/ pulsing gold dot, mono numeric cell, Cormorant hero).
> 3. /api: uv init + pyproject. Install fastapi, uvicorn, python-dotenv, pydantic v2, google-genai, pymupdf, supabase, sse-starlette, reportlab, pypdf, pillow. main.py with GET /health + POST /test-gemini (Flash, JSON schema, proves Vertex auth). services/gemini.py GeminiService.generate_pro/generate_flash (vertexai=True, retries w/ exp backoff for 503). services/pdf_pages.py pdf_to_page_images() -> List[Tuple[int, PIL.Image]] at 2x DPI.
> 4. /shared/citation.py (Citation Pydantic per Phase 0) + /shared/citation.ts matching interface.
> 5. Root: README.md run commands, .env.example (names only), .gitignore (node_modules, .venv, __pycache__, .env.local, gcp-key.json — CRITICAL), CONTEXT_CARRY.md.
>
> Run both servers. Show: visual description of /design-test (describe, don't render); curl output of POST /api/test-gemini proving Gemini works. No agent logic — foundation only.

---

## Prompt 2 — PHASE 2: Database schema, two-role auth, and RLS (2026-05-27)

> Goal: Supabase has all tables, RLS enforced; Next.js has working signup/login for bidder + officer.
>
> 1. Migration /supabase/migrations/001_initial.sql: profiles, tenders, bids, agent_runs, recommendations + tender_documents, bid_documents, citations (denormalized claims for the audit grid).
> 2. RLS: bidders see own profile/bids + published tenders; officers see tenders they own + bids on them + those citations; service role bypasses (FastAPI).
> 3. /web auth: /signup (role selector Bidder/Officer → email+password → profile completion: GST/PAN for bidders, ministry/department for officers), /login, protected /bidder/* and /officer/* with role guard via Supabase session, post-login redirect to /bidder/tenders or /officer/dashboard.
> 4. Style strictly to DESIGN_SYSTEM.md. Signup like Linear: two-pane, left obsidian with gold Cormorant "TenderIQ" wordmark + tagline, right pane the form.
> 5. Test: sign up 1 officer + 2 bidders, verify RLS blocks cross-access in SQL; update CONTEXT_CARRY. Stop after auth works — no tender pages yet.

---

## Prompt 3 — Fix the three Phase-2 flags (2026-05-27)

> "fix them but we cant do anything with tokyo because we are using free supabase tier"
>
> 1. Recursion bug — already fixed (migrations 003/004); confirmed all 4 migrations recorded.
> 2. Tokyo region — accepted constraint (free tier can't relocate a project); docs updated, no longer flagged as an issue.
> 3. Email-confirm gotcha — RESOLVED in code: added Next route handler POST /api/auth/signup that creates an email-confirmed user via the service role, so UI signup flows to onboarding regardless of the dashboard "Confirm email" setting. Verified (200 / 409 / 400 / auto-confirmed sign-in).

---

## Prompt 4 — PHASE 3: PDF ingestion + Tender schema extraction (2026-05-27)

> Goal: officer uploads a tender PDF; extract structured tender_schema (eligibility, technical matrix, financial format, deadlines, evaluation method) with each field carrying its source page.
>
> 1. /api ingestion: POST /api/tenders/upload (PDF -> Supabase Storage tender-docs/, return path); POST /api/tenders/{id}/parse (async: download, send to Azure Document Intelligence prebuilt-layout, persist raw to tenders.parsed_layout jsonb).
> 2. Tender Parser Agent: input = Doc Intel layout; Azure OpenAI gpt-4o structured outputs; extract title/ref/ministry/value/evaluation_method (L1/QCBS/LCS)/QCBS weights/eligibility_criteria[]/technical_criteria[]/financial_format/EMD+page/PBG%+page/integrity_pact+page/ppp_mii_class+page/submission_deadline; persist to tenders.parsed_schema.
> 3. /web /officer/tenders/new: Stripe-style drag-drop upload, live progress, then split PDF (react-pdf) + extracted fields with click-to-jump-to-source-page.
> 4. Test with a real CPPP tender PDF (IT services/consultancy, 20-60pp); show parsed_schema JSON. Update CONTEXT_CARRY.
>
> NOTE: This contradicts the Phase 0 locked stack (Gemini/Vertex + PyMuPDF, "do not substitute") and requires Azure DI + Azure OpenAI credentials that don't exist in the project. Raised with Samad before building.
>
> DECISION (Samad): **Gemini/Vertex, in-stack.** Built with PyMuPDF (per-page text -> parsed_layout) + Gemini 2.5 Pro response_schema=TenderSchema (-> parsed_schema, every field page-cited). No Azure. Pro runs on the `global` endpoint (not served in asia-south1). Verified E2E on a synthetic CPPP fixture.

---

## Prompt 5 — PHASE 4: Bidder side end-to-end (2026-05-27)

> Goal: bidder browses published tenders, opens detail, applies with live eligibility pre-check, uploads bid docs, gets a pre-submission compliance check, and submits.
>
> 1. /bidder/tenders — table (Title, Ministry, ₹ Indian-format value, deadline days-left gold if <7, evaluation-method pill).
> 2. /bidder/tenders/[id] — split: PDF left, tender_schema collapsible sections right, Apply button.
> 3. /bidder/tenders/[id]/apply — Section A SSE eligibility pre-check (profile vs criteria, verdict + page citation; FAIL -> apply-anyway), Section B two dropzones (technical+financial), Section C SSE pre-submission compliance check on bid docs with bidder's own page numbers, Submit (disabled until both uploaded).
> 4. /bidder/submissions — submitted bids with status.
> Bidder portal = warmer variant, carbon #14110D. Show screenshot description.
>
> ADAPTATIONS (consistent with prior decisions): Section C "Azure Doc Intel" -> Gemini (same as Phase 3, no Azure creds). Added bidder capability profile fields (turnover/years/MSE/certs) since eligibility pre-check needs them; seeded test bidders.

---

## Prompt 6 — PHASE 5: The agent pipeline — the heart of the product (2026-05-28)

> Goal: when an officer clicks "Review Bids" on a tender, all 7 agents run on every submitted bid, stream progress live, and emit citation-grounded claims.
>
> 1. /api/agents/ — one file per agent, uniform `async run(tender_schema, bid_id, bid_doc_intel) -> AgentResult` (agent_name, status, verdict, claims[], elapsed_ms).
> 2. Implement all 7 per the Citation contract: reuse ingestion_agent + tender_parser_agent from Phase 3; build eligibility_agent, technical_agent, compliance_agent (PPP-MII Class-I, Integrity Pact, EMD, OEM auths, BIS/ISO currency), financial_agent (L1 + abnormally-low: >20% below estimate per CVC), risk_agent (seeded blacklist JSON; cartel suspicion if 3+ within 2% per CVC Circular 4/3/07), reasoning_agent (orchestrator).
> 3. Azure OpenAI gpt-4o with response_format JSON schema; EVERY claim MUST have page_number filled — reasoning_agent rejects + reruns any agent emitting a claim missing page_number.
> 4. POST /api/tenders/{id}/review as SSE: bids 3-7 in parallel where possible; events agent_start, claim_emitted, agent_complete, disagreement_detected, orchestrator_complete; persist every claim to citations, every run to agent_runs.
> 5. reasoning_agent: aggregate 6 specialist outputs per bid; apply L1 / QCBS; DETECT DISAGREEMENTS (Technical PASS + Compliance FAIL → disagreement event, mark "human_review_required", refuse to recommend); output ranking + reasoning text + conflicting claims.
>
> Test trigger on 3 seeded bids (provided in Phase 6); show the SSE event log.
>
> ADAPTATIONS / NOTES:
> - **Stack: Gemini 2.5 Pro via Vertex, not Azure OpenAI gpt-4o** — consistent with the Phase-3/4 decision; no Azure creds in the project. Structured output is the same mechanism (`response_schema` + the Citation contract). Flagged before building.
> - **Migration `007_agent_review`** added `human_review_required` to the `bids.status` check (applied via Supabase MCP). All other tables (`agent_runs`, `citations`, `recommendations`) already existed from `001_initial`.
> - Built `agents/base.py` with the citation gate + `run_structured_citation_agent` that **rejects + RERUNS** (bounded) any claim missing page+quote and collects `rejections` for `agent_runs.rejections`. financial_agent does deterministic abnormally-low (>20% below estimate) grounded on the bid's price-line page+quote; risk_agent is deterministic against `agents/blacklist.json`; cartel detection lives in reasoning_agent (cross-bid).
> - **SSE log demonstrated hermetically** via `scripts/mock_review_log.py` (FakeGemini + NullPersist drives the REAL orchestration) across 3 scenarios × 3 bids: (A) QCBS ranking + blacklist reject + citation-gate rerun (`rej=1`); (B) Technical-vs-Compliance disagreement + abnormally-low → human review; (C) L1 cartel → all human review, no award. `scripts/e2e_review.py` is the live trigger, **deferred to Phase 6** with the real 3 bids (Samad chose "Wait for Phase 6" over a live dry run on the existing Orbit bid — no Vertex cost / no DB writes this phase).
