-- ============================================================================
-- TenderIQ — 004_revoke_anon_role_helpers
-- Supabase grants EXECUTE to anon/authenticated via DEFAULT PRIVILEGES, so a
-- `revoke from public` (003) didn't strip anon. Revoke from anon explicitly.
-- (anon never needs these — all RLS policies that call them are `to authenticated`.)
-- The remaining "authenticated can execute SECURITY DEFINER" advisor warning is
-- accepted: RLS evaluation REQUIRES authenticated to call them, and they only
-- reveal whether the caller is an officer/bidder (no data exposure).
-- ============================================================================

revoke execute on function public.is_officer() from anon;
revoke execute on function public.is_bidder() from anon;
