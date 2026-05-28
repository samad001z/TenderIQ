import { createClient } from "@supabase/supabase-js";

/**
 * SERVER ONLY — Supabase admin client (service-role key, bypasses RLS).
 * Import ONLY in route handlers / server actions, never in a client component.
 * (SUPABASE_SERVICE_ROLE_KEY is not a NEXT_PUBLIC var, so its value is undefined
 * in client bundles — but treat this module as privileged regardless.)
 */
export function createAdminClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } },
  );
}
