-- ============================================================================
-- TenderIQ — 003_fix_role_helper_recursion
--
-- 002 switched is_officer/is_bidder to SECURITY INVOKER to clear an advisor
-- warning. That was wrong: those functions read public.profiles, and the
-- profiles policy "Officers read bidder profiles..." CALLS is_officer() — so an
-- INVOKER read re-enters profiles RLS and recurses infinitely (stack depth).
--
-- Fix: they MUST be SECURITY DEFINER (bypass RLS on the internal profiles read).
-- To address the "anon can execute" lint without breaking RLS, we revoke EXECUTE
-- from PUBLIC/anon and grant only to `authenticated` (which RLS evaluation needs).
-- They only ever reveal whether the CALLER is an officer/bidder — no data leak.
-- ============================================================================

create or replace function public.is_officer()
returns boolean language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.profiles where id = auth.uid() and role = 'officer');
$$;

create or replace function public.is_bidder()
returns boolean language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.profiles where id = auth.uid() and role = 'bidder');
$$;

revoke execute on function public.is_officer() from public;
revoke execute on function public.is_bidder() from public;
grant execute on function public.is_officer() to authenticated;
grant execute on function public.is_bidder() to authenticated;
