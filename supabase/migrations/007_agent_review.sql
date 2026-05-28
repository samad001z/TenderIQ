-- ============================================================================
-- TenderIQ — 007_agent_review
-- Phase 5: the officer-side 7-agent review pipeline.
--
-- The reasoning_agent (orchestrator) refuses to recommend a bid when its
-- specialists disagree (e.g. Technical PASS but Compliance FAIL) or when a
-- cross-bid cartel pattern is detected (CVC Circular 4/3/07). Such bids are
-- parked in a new terminal-ish state 'human_review_required' instead of being
-- auto-evaluated. Extend the bids.status check to allow it.
--
-- Everything else the pipeline writes (agent_runs, citations, recommendations)
-- already exists from 001_initial.
-- ============================================================================

alter table public.bids drop constraint if exists bids_status_check;
alter table public.bids
  add constraint bids_status_check
  check (status in (
    'draft','submitted','under_review','evaluated',
    'human_review_required','accepted','rejected'
  ));
