# TenderIQ — 4-slide pitch deck

Drop these straight into Google Slides / Keynote. Suggested aspect 16:9, dark
navy accents (`#003875`), saffron highlights (`#FF9933`), white surfaces.

---

## Slide 1 — The Problem

**Title:** Bid evaluation in Indian government procurement is broken.

**Body (sub-points):**

- Every CPSE / PSU evaluation committee opens **20–300 page bid PDFs** for
  every submitted bid, and is expected to find missing OEM letters, expired ISO
  certificates, abnormally-low quotes, and shell submissions — by hand.
- The CAG and CVC require every recommendation to be **defensible to the page**
  — but officers paste-and-pray, and errors compound into tender re-floats,
  court cases, and award delays.
- ~**₹40 lakh crore** of public procurement runs through GeM + CPPP each year.
  A 1% improvement in evaluator throughput is enormous.
- Existing portals (CPPP, GeM) are submission systems — none **evaluate** the
  bid against the tender.

**Footer:** A single bid review can take **40 hours**. The disagreement that
matters — Technical says PASS, Compliance says FAIL — almost never gets caught.

---

## Slide 2 — The Solution & user journey

**Title:** TenderIQ — every claim, cited to the page.

**Hero line:** Seven specialist agents review every submitted bid against your
tender. Each finding carries the **source document, exact page number, and a
verbatim quote** — audit-grade by design.

**User journey (left → right, 4 numbered steps):**

1. **Officer uploads tender PDF** → tender schema (eligibility, technical,
   financial format, evaluation method) extracted with every field page-cited.
2. **Bidders sign up & submit** through the portal — an in-flight eligibility
   pre-check catches gaps before they hit "Submit".
3. **Officer clicks Run AI Review** → live dashboard streams the 7-agent pipeline
   (ingestion, tender parser, eligibility, technical, compliance, financial, risk)
   over every submitted bid in parallel.
4. **Comparison matrix appears** — bidder × agent cells, click for evidence,
   bounding-box highlighted PDF. **Download Audit Report** generates a CAG-style
   signed PDF the officer can put on file.

**Differentiator strip (bottom):**

| Detection | What it catches |
| --- | --- |
| Tech-vs-Compliance disagreement | Technical PASS + Compliance FAIL → human review |
| Duplicate-bidder | "Same documents, only the name changed" shell submissions |
| Abnormally low | Quote > 20% below estimate (CVC norms) |
| Cartel cluster | 3+ bids within 2% (CVC Circular 4/3/07) |
| Blacklist | Match against CVC debarred-firms registry |

---

## Slide 3 — Tools / tech stack

**Title:** Built like a government system, but modern.

**Two columns:**

**AI & evaluation engine**

- **Google Gemini 2.5 Pro** on Vertex AI (`asia-south1` Mumbai) — multimodal
  PDF understanding + reasoning with `response_schema`-constrained structured
  output. Gemini 2.5 Flash for cheap routing.
- **PyMuPDF** — born-digital PDF text extraction & per-page image rendering
  with bounding-box-accurate quote highlighting.
- **Pydantic Citation contract** — every AI claim has page > 0 + verbatim
  quote, or the orchestrator rejects and re-runs the agent (logged to
  `agent_runs.rejections`).
- **Async SSE pipeline (FastAPI + `sse-starlette`)** — five specialist agents
  run in parallel per bid via `asyncio.gather` + threaded Gemini calls.
- **reportlab** — CAG-style audit PDF generation, Arial-registered so the ₹
  glyph survives.

**Application & infrastructure**

- **Next.js 15** (App Router, TS, Tailwind v3, shadcn/ui)
- **Supabase** (Mumbai) — Postgres + pgvector + Auth (GoTrue) + Storage,
  full Row-Level Security
- **government-portal UI** — light institutional theme, tricolor strip,
  modern card surfaces, gov-navy + saffron accents
- **uv** for Python; built on Windows + Linux

**Bottom band — "Built with" (hackathon-required):**

> Built for the **OpenAI × Outskill AI Builders Hackathon 2026** using
> **Claude CLI** as the pair-programmer (see `docs/PROMPTS_LOG.md` for every
> prompt that shaped this codebase). The official submission lists the
> hackathon Codex Org ID.

---

## Slide 4 — Target audience

**Title:** Who uses TenderIQ.

**Three personas (cards):**

**1. Procurement Officer (primary)**
- Government ministry / CPSE / state department evaluator
- Issues 10–60 tenders / year, faces hundreds of bid pages each
- Needs: faster review, defensible recommendation, downloadable audit trail
- Buys via: GeM listing, direct CPSE pilot

**2. Vigilance / Audit (compliance buyer)**
- CVC officers, internal vigilance, CAG audit teams
- Needs: every recommendation traceable to a page-cited quote; integrity
  flags (cartel, duplicate, blacklist) surfaced and logged
- Bought into via: officer pilot → audit-team review → mandate

**3. Bidders (the other side of the market)**
- MSMEs and large vendors bidding on government work
- Needs: an in-flight eligibility pre-check + compliance review before they
  pay EMD and hit submit
- Acquired via: free signup, the eligibility pre-check is their wedge

**Market size (footer):**
- ~**₹40 lakh crore** annual procurement (GeM + CPPP combined)
- ~**4 lakh** registered bidders in India
- ~**1,200+** CPSEs / ministries / state agencies that issue tenders
- TAM is large; even a 1% capture is meaningful
