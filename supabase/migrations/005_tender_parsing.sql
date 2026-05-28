-- ============================================================================
-- TenderIQ — 005_tender_parsing
-- Columns to hold the uploaded PDF reference + Gemini ingestion output.
--   parsed_layout  : PyMuPDF per-page text/tables (raw grounding, analog of a
--                    layout model's pages[]/tables[])
--   parsed_schema  : the structured tender_schema from Gemini 2.5 Pro
-- ============================================================================

alter table public.tenders
  add column if not exists source_file_name   text,
  add column if not exists source_storage_path text,
  add column if not exists parsed_layout       jsonb,
  add column if not exists parsed_schema        jsonb,
  add column if not exists parse_status         text not null default 'pending'
       check (parse_status in ('pending','parsing','parsed','failed')),
  add column if not exists parse_error          text,
  add column if not exists parsed_at            timestamptz;
