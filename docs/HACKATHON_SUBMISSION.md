# Hackathon submission — paste-ready answers

For the **Phase 1 MVP form** (OpenAI × Outskill AI Builders Hackathon, deadline
28 May 2026, 11:59 PM). Each section below maps to a form field.

---

## Email (registered for hackathon)
`001saadurrahman@gmail.com`

## Your name
Saad Ur Rahman

## Name of your product + solution
**TenderIQ — Audit-grade AI bid-evaluation portal for Indian government
procurement.**

(Sub-line, if a longer field: *Seven specialist agents review every submitted
bid against your tender. Every recommendation is grounded in a page-cited
verbatim quote from the bidder's own documents.*)

## MVP / working product link
Paste your **GitHub repo URL** here (push the codebase as-is — the README
covers setup + demo flow). If you also want a hosted demo, deploy `/web` to
Vercel pointing `NEXT_PUBLIC_API_BASE_URL` at the deployed `/api`.

## Presentation link
- Open Google Slides → File > Make a copy of the deck you built from
  `docs/PITCH_DECK.md`
- Share > "Anyone with the link can view" — paste that URL into the form.

## 4-slide pitch deck content
See `docs/PITCH_DECK.md` — all four slides written out, ready to paste into
your slide tool of choice.

## Build-in-public post link (optional)
Paste your LinkedIn or X post URL after publishing — copy from
`docs/BUILD_IN_PUBLIC.md`.

## Codex Org ID
**Only you can get this.** Steps from the form:
1. Sign in at https://platform.openai.com/settings/organization/general
2. Copy the **Organization ID** (`org-xxxxxxxxxxxxxxxxxxxx`) including the
   `org-` prefix.
3. Paste it into the form.

---

## Quick demo flow for judges (link this in your repo description)

1. `cd api && uv sync && uv run uvicorn main:app --port 8000` (terminal 1)
2. `cd web && npm install && npm run dev` (terminal 2)
3. Open `http://localhost:3000/` — landing page explains the product.
4. Sign in as **officer@tenderiq.test / TenderIQ#2026**.
5. Go to **Tenders** → click **View review** on "Selection of System
   Integrator — National e-Procurement Analytics Platform (Package B)".
6. See the ranking (StellarTech AWARD · Velocity HUMAN REVIEW · BudgetBuild
   + ShadowBuild REJECT + duplicate flag), the two disagreement banners,
   click any matrix cell to see the citations, click a citation pill to see
   the page-highlighted PDF, click **Download Audit Report** for the
   CAG-style PDF.

## Hermetic SSE log (no Vertex needed)
`uv run python api/scripts/mock_review_log.py` — runs the orchestration over
three synthetic scenarios with a fake Gemini, prints the full SSE event log
with all event types (`agent_start`, `claim_emitted`, `agent_complete`,
`disagreement_detected`, `orchestrator_complete`). Useful proof for judges
who can't / don't want to set up Vertex.

## Where the code lives

- `api/agents/` — one file per agent + the citation gate + the orchestrator
- `api/services/review_pipeline.py` — the SSE generator + DB persistence
- `api/services/page_highlight.py` — bounding-box-highlighted PDF page PNG
- `api/services/audit_pdf.py` — the CAG-style audit report
- `web/app/(app)/officer/tenders/[id]/review/` — the demo UI
- `web/app/page.tsx` — the public landing page
- `docs/CONTEXT_CARRY.md` — full phase-by-phase build log
- `docs/PROMPTS_LOG.md` — every Claude-CLI prompt that shaped the codebase
- `shared/citation.py` — the non-negotiable Citation contract
