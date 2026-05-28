-- ============================================================================
-- TenderIQ — 008_review_scores
-- Phase 6: persist QCBS / L1 scores and rank per bid so the audit PDF (which
-- runs post-review, possibly hours later) can be reproduced from the DB without
-- replaying the LLM. Also stamps the tender with last_reviewed_at for the
-- officer tenders list.
-- ============================================================================

alter table public.bids
  add column if not exists technical_score numeric(6,2),
  add column if not exists financial_score numeric(6,2),
  add column if not exists combined_score  numeric(6,2),
  add column if not exists review_rank     int;

alter table public.tenders
  add column if not exists last_reviewed_at timestamptz;
