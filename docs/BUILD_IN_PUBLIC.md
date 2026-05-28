# Build-in-public — LinkedIn / Twitter post drafts

For the optional "Build In Public" Phase 1 progress post. Required hashtags:
`#AIBuildersHackathon #Outskill #OpenAI #Codex`.

---

## LinkedIn (long-form, ~1800 chars)

I spent the last few days building **TenderIQ** for the OpenAI × Outskill AI
Builders Hackathon — an AI-assisted bid-evaluation portal for Indian government
procurement, where every recommendation is grounded in a page-cited verbatim
quote from the bidder's own documents.

**Why this?** Indian government tenders run on 100+ page bid PDFs. Officers
read every one of them by hand, looking for missing OEM letters, expired
ISO certs, abnormally-low quotes, and shell submissions. The CAG and the
Central Vigilance Commission require every recommendation to be defensible
to the page — but evaluators paste-and-pray, and errors compound.

**What I built (Phase 1 MVP):**

→ 7-agent pipeline (ingestion, tender parser, eligibility, technical,
  compliance, financial, risk) running in parallel per submitted bid.
→ A non-negotiable **Citation contract** — every AI claim has the source
  document, exact page number, and verbatim quote, or the orchestrator
  rejects and re-runs the agent.
→ **Disagreement detection** — when the Technical agent passes a bid that
  the Compliance agent fails, the system refuses to recommend it and routes
  it to human review with the conflicting claims side-by-side.
→ **Duplicate-bidder check** — catches "same documents, only the name
  changed" shell submissions by comparing the substantive content of every
  bid after normalising bidder identities.
→ A modern government-portal UI (tricolor strip, navy + saffron accents,
  emblem), a live agent dashboard, a comparison matrix you can click into
  for evidence, server-rendered bounding-box-highlighted PDF pages, and a
  one-click **CAG-style audit report** download.

**How I used AI / Codex to build this:**
The whole codebase was paired with Claude CLI as the engineering counterpart
— every prompt is logged in `docs/PROMPTS_LOG.md` as the build history. The
underlying evaluation engine runs on Gemini 2.5 Pro (Vertex AI) using
`response_schema`-constrained structured output, which is what lets the
citation contract be enforceable rather than aspirational.

Live demo: <your-demo-link>
Repo: <your-github-link>

Would love feedback in the comments — especially from anyone who's been on
the receiving end of a Vigilance committee. What integrity checks would you
add?

#AIBuildersHackathon #Outskill #OpenAI #Codex #GovTech #PublicProcurement

---

## Twitter / X (thread, 4 tweets)

**1/** Spent Phase 1 of the @OpenAI × @Outskill_official AI Builders Hackathon
building **TenderIQ** — an AI-assisted bid-evaluation portal for Indian
government procurement, where every recommendation is **cited to the page**.

#AIBuildersHackathon #Outskill #OpenAI #Codex 🇮🇳

**2/** The problem: officers read 100+ pages of bid PDFs by hand, looking
for missing OEM letters, expired ISO certs, abnormally-low quotes, shell
submissions. CAG + CVC require every recommendation defensible to the page.
Today it's paste-and-pray.

**3/** What I shipped:
- 7-agent pipeline (eligibility / technical / compliance / financial / risk +
  ingestion + reasoning) running in parallel per submitted bid
- Non-negotiable Citation contract — every AI claim has page > 0 + verbatim
  quote, or it's rejected and re-run
- Disagreement detection (Tech PASS ⇄ Compliance FAIL → human review)
- Duplicate-bidder check (catches shell submissions where only the name
  differs)
- Modern government-portal UI + a one-click CAG-style audit PDF

**4/** Built with Claude CLI as the pair-programmer (every prompt logged in
the repo). Runs on Gemini 2.5 Pro on Vertex AI for the evaluation engine.
Supabase Postgres + RLS for data. Live demo + repo in replies 👇

Give it a try and tell me what integrity check I missed.

---

## Suggested visuals to attach

1. **Landing page hero screenshot** (`tests/screenshots/00-landing.png`) — the
   "Audit-grade bid evaluation for the Government of India" headline with the
   ranking-preview card.
2. **Officer review screenshot** (`tests/screenshots/04-officer-review.png`) —
   the comparison matrix with the disagreement banner and the duplicate-
   submission banner both visible.
3. **The SSE event log** from `scripts/mock_review_log.py` — proves the
   "every claim has a page + quote" promise with real output.
