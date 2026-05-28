-- ============================================================================
-- TenderIQ — 002_harden_functions
-- Address security-advisor warnings from 001 without weakening RLS.
-- ============================================================================

-- Pin search_path (was mutable).
alter function public.set_updated_at() set search_path = '';

-- is_officer/is_bidder only ever inspect the CALLER's own profile row, which the
-- "Users read own profile" policy already permits — so they work fine as
-- SECURITY INVOKER, removing the "public can execute SECURITY DEFINER" warnings.
create or replace function public.is_officer()
returns boolean language sql security invoker stable set search_path = public as $$
  select exists (select 1 from public.profiles where id = auth.uid() and role = 'officer');
$$;

create or replace function public.is_bidder()
returns boolean language sql security invoker stable set search_path = public as $$
  select exists (select 1 from public.profiles where id = auth.uid() and role = 'bidder');
$$;

-- handle_new_user must stay SECURITY DEFINER (inserts the profile at signup,
-- bypassing RLS) but should never be callable directly via the REST RPC surface.
revoke execute on function public.handle_new_user() from public, anon, authenticated;
