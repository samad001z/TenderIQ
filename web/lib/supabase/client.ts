import { createBrowserClient } from "@supabase/ssr";

/** Browser Supabase client (cookie-based, so middleware/SSR can read the session). */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
