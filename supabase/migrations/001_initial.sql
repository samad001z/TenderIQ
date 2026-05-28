-- ============================================================================
-- TenderIQ — 001_initial
-- Schema + two-role auth + Row Level Security.
--
-- Roles live in public.profiles.role ('bidder' | 'officer'). RLS is keyed off
-- ownership (auth.uid()) so most policies need no role lookup; where a role
-- gate IS required (e.g. only officers create tenders) we use SECURITY DEFINER
-- helpers that read profiles WITHOUT RLS to avoid recursion.
--
-- The FastAPI backend uses the service_role key, which BYPASSES RLS entirely.
-- ============================================================================

create extension if not exists vector with schema extensions;  -- pgvector, for Phase 3 embeddings

-- ----------------------------------------------------------------------------
-- Shared helpers
-- ----------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ============================================================================
-- profiles  (1:1 with auth.users)
-- ============================================================================
create table public.profiles (
  id                  uuid primary key references auth.users(id) on delete cascade,
  role                text not null default 'bidder' check (role in ('bidder','officer')),
  full_name           text not null default '',
  email               text,
  org_name            text,            -- company (bidder) or organisation (officer)
  -- bidder fields
  gst_number          text,
  pan_number          text,
  -- officer fields
  ministry            text,
  department          text,
  phone               text,
  onboarding_complete boolean not null default false,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create trigger profiles_set_updated_at
  before update on public.profiles
  for each row execute function public.set_updated_at();

-- Role helpers (SECURITY DEFINER -> read profiles bypassing RLS, no recursion).
create or replace function public.is_officer()
returns boolean language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.profiles where id = auth.uid() and role = 'officer');
$$;

create or replace function public.is_bidder()
returns boolean language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.profiles where id = auth.uid() and role = 'bidder');
$$;

-- Auto-create a profile when a user signs up. Role + full_name come from the
-- signUp metadata (the /signup role selector). Self-selected role is by design
-- (the product has a public Bidder/Officer chooser).
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, role, full_name)
  values (
    new.id,
    new.email,
    coalesce(nullif(new.raw_user_meta_data->>'role', ''), 'bidder'),
    coalesce(new.raw_user_meta_data->>'full_name', '')
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ============================================================================
-- tenders  (owned by an officer)
-- ============================================================================
create table public.tenders (
  id              uuid primary key default gen_random_uuid(),
  owner_id        uuid not null references public.profiles(id) on delete cascade,
  reference_no    text,
  title           text not null,
  description     text,
  status          text not null default 'draft' check (status in ('draft','published','closed','awarded')),
  ministry        text,
  department      text,
  estimated_value numeric(16,2),
  emd_amount      numeric(16,2),
  published_at    timestamptz,
  closing_at      timestamptz,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index tenders_owner_idx  on public.tenders(owner_id);
create index tenders_status_idx on public.tenders(status);
create trigger tenders_set_updated_at
  before update on public.tenders
  for each row execute function public.set_updated_at();

-- ============================================================================
-- tender_documents  (a tender can have many files: RFP, corrigenda, annexures)
-- ============================================================================
create table public.tender_documents (
  id           uuid primary key default gen_random_uuid(),
  tender_id    uuid not null references public.tenders(id) on delete cascade,
  file_name    text not null,
  storage_path text not null,                          -- object key in the tender-docs bucket
  doc_type     text not null default 'rfp' check (doc_type in ('rfp','corrigendum','annexure','boq','other')),
  page_count   int,
  uploaded_by  uuid references public.profiles(id),
  created_at   timestamptz not null default now()
);
create index tender_documents_tender_idx on public.tender_documents(tender_id);

-- ============================================================================
-- bids  (a bidder's submission to a tender)
-- ============================================================================
create table public.bids (
  id             uuid primary key default gen_random_uuid(),
  tender_id      uuid not null references public.tenders(id) on delete cascade,
  bidder_id      uuid not null references public.profiles(id) on delete cascade,
  status         text not null default 'draft' check (status in ('draft','submitted','under_review','evaluated','accepted','rejected')),
  quoted_amount  numeric(16,2),
  score          numeric(6,2),
  submitted_at   timestamptz,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  unique (tender_id, bidder_id)                        -- one bid per bidder per tender
);
create index bids_tender_idx on public.bids(tender_id);
create index bids_bidder_idx on public.bids(bidder_id);
create trigger bids_set_updated_at
  before update on public.bids
  for each row execute function public.set_updated_at();

-- ============================================================================
-- bid_documents  (technical + financial + extras)
-- ============================================================================
create table public.bid_documents (
  id           uuid primary key default gen_random_uuid(),
  bid_id       uuid not null references public.bids(id) on delete cascade,
  file_name    text not null,
  storage_path text not null,                          -- object key in the bidder-docs bucket
  doc_type     text not null default 'technical' check (doc_type in ('technical','financial','extra')),
  page_count   int,
  uploaded_by  uuid references public.profiles(id),
  created_at   timestamptz not null default now()
);
create index bid_documents_bid_idx on public.bid_documents(bid_id);

-- ============================================================================
-- agent_runs  (one row per agent execution against a bid)
--   rejections: log of Citations rejected by the orchestrator (page<=0 / empty quote)
-- ============================================================================
create table public.agent_runs (
  id            uuid primary key default gen_random_uuid(),
  bid_id        uuid not null references public.bids(id) on delete cascade,
  agent         text not null,                         -- which of the 7 agents
  status        text not null default 'queued' check (status in ('queued','running','completed','failed')),
  model         text,                                  -- e.g. gemini-2.5-pro
  rejections    jsonb not null default '[]'::jsonb,    -- rejected-citation audit log
  raw_output    jsonb,
  error         text,
  started_at    timestamptz,
  completed_at  timestamptz,
  created_at    timestamptz not null default now()
);
create index agent_runs_bid_idx on public.agent_runs(bid_id);

-- ============================================================================
-- citations  (denormalized claim rows — the audit grid; mirrors shared/citation.py)
-- ============================================================================
create table public.citations (
  id                 uuid primary key default gen_random_uuid(),
  agent_run_id       uuid references public.agent_runs(id) on delete cascade,
  bid_id             uuid not null references public.bids(id) on delete cascade,     -- denormalized
  tender_id          uuid not null references public.tenders(id) on delete cascade,  -- denormalized
  claim              text not null,
  verdict            text not null check (verdict in ('PASS','FAIL','FLAG','INFO')),
  source_doc         text not null,
  page_number        int  not null,
  quote              text not null,
  confidence         real not null,
  tender_clause      text,
  tender_clause_page int,
  severity           text not null check (severity in ('low','medium','high','critical')),
  agent              text not null,
  created_at         timestamptz not null default now()
);
create index citations_bid_idx     on public.citations(bid_id);
create index citations_tender_idx  on public.citations(tender_id);
create index citations_verdict_idx on public.citations(verdict);

-- ============================================================================
-- recommendations  (final aggregated verdict per bid)
-- ============================================================================
create table public.recommendations (
  id                 uuid primary key default gen_random_uuid(),
  bid_id             uuid not null references public.bids(id) on delete cascade,
  tender_id          uuid not null references public.tenders(id) on delete cascade,
  recommended_action text check (recommended_action in ('award','shortlist','reject','review')),
  overall_score      numeric(6,2),
  summary            text,
  rationale          text,
  generated_by       text,                              -- model id
  created_at         timestamptz not null default now()
);
create index recommendations_bid_idx    on public.recommendations(bid_id);
create index recommendations_tender_idx on public.recommendations(tender_id);

-- ============================================================================
-- Row Level Security
-- ============================================================================
alter table public.profiles         enable row level security;
alter table public.tenders          enable row level security;
alter table public.tender_documents enable row level security;
alter table public.bids             enable row level security;
alter table public.bid_documents    enable row level security;
alter table public.agent_runs       enable row level security;
alter table public.citations        enable row level security;
alter table public.recommendations  enable row level security;

-- ---- profiles -------------------------------------------------------------
create policy "Users read own profile" on public.profiles
  for select to authenticated using (id = auth.uid());

create policy "Officers read bidder profiles on their tenders" on public.profiles
  for select to authenticated using (
    public.is_officer() and exists (
      select 1 from public.bids b
      join public.tenders t on t.id = b.tender_id
      where b.bidder_id = profiles.id and t.owner_id = auth.uid()
    )
  );

create policy "Users insert own profile" on public.profiles
  for insert to authenticated with check (id = auth.uid());

create policy "Users update own profile" on public.profiles
  for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- ---- tenders --------------------------------------------------------------
-- Bidders see PUBLISHED tenders; officers see the tenders they own (any status).
create policy "Read published or owned tenders" on public.tenders
  for select to authenticated using (status = 'published' or owner_id = auth.uid());

create policy "Officers create own tenders" on public.tenders
  for insert to authenticated with check (owner_id = auth.uid() and public.is_officer());

create policy "Officers update own tenders" on public.tenders
  for update to authenticated using (owner_id = auth.uid()) with check (owner_id = auth.uid());

create policy "Officers delete own tenders" on public.tenders
  for delete to authenticated using (owner_id = auth.uid());

-- ---- tender_documents -----------------------------------------------------
create policy "Read docs of published or owned tenders" on public.tender_documents
  for select to authenticated using (
    tender_id in (select id from public.tenders where status = 'published' or owner_id = auth.uid())
  );

create policy "Officers manage docs of owned tenders" on public.tender_documents
  for all to authenticated
  using      (tender_id in (select id from public.tenders where owner_id = auth.uid()))
  with check (tender_id in (select id from public.tenders where owner_id = auth.uid()));

-- ---- bids -----------------------------------------------------------------
-- Bidders see their own bids; officers see bids on tenders they own.
create policy "Read own bids or bids on owned tenders" on public.bids
  for select to authenticated using (
    bidder_id = auth.uid()
    or tender_id in (select id from public.tenders where owner_id = auth.uid())
  );

create policy "Bidders create own bids" on public.bids
  for insert to authenticated with check (bidder_id = auth.uid() and public.is_bidder());

create policy "Bidders update own bids; officers update bids on owned tenders" on public.bids
  for update to authenticated using (
    bidder_id = auth.uid()
    or tender_id in (select id from public.tenders where owner_id = auth.uid())
  ) with check (
    bidder_id = auth.uid()
    or tender_id in (select id from public.tenders where owner_id = auth.uid())
  );

-- ---- bid_documents --------------------------------------------------------
create policy "Read own bid docs or docs on owned tenders" on public.bid_documents
  for select to authenticated using (
    bid_id in (select id from public.bids where bidder_id = auth.uid())
    or bid_id in (
      select b.id from public.bids b join public.tenders t on t.id = b.tender_id
      where t.owner_id = auth.uid()
    )
  );

create policy "Bidders manage own bid docs" on public.bid_documents
  for all to authenticated
  using      (bid_id in (select id from public.bids where bidder_id = auth.uid()))
  with check (bid_id in (select id from public.bids where bidder_id = auth.uid()));

-- ---- agent_runs / citations / recommendations -----------------------------
-- Written by the backend (service_role, bypasses RLS). Visible to the OFFICER
-- who owns the tender the bid was submitted to.
create policy "Officers read agent_runs for their tenders' bids" on public.agent_runs
  for select to authenticated using (
    bid_id in (
      select b.id from public.bids b join public.tenders t on t.id = b.tender_id
      where t.owner_id = auth.uid()
    )
  );

create policy "Officers read citations for their tenders' bids" on public.citations
  for select to authenticated using (
    tender_id in (select id from public.tenders where owner_id = auth.uid())
  );

create policy "Officers read recommendations for their tenders' bids" on public.recommendations
  for select to authenticated using (
    tender_id in (select id from public.tenders where owner_id = auth.uid())
  );
