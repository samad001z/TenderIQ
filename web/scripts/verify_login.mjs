/**
 * End-to-end auth check: signs in each seeded user with the PUBLISHABLE (anon)
 * key — the exact call the /login page makes — and prints session + metadata.
 *
 * Run from /web:  node --env-file=.env.local scripts/verify_login.mjs
 */
import { createClient } from "@supabase/supabase-js";

const URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

const CREDS = [
  ["officer@tenderiq.test", "TenderIQ#2026"],
  ["bidder.meridian@tenderiq.test", "TenderIQ#2026"],
  ["bidder.orbit@tenderiq.test", "TenderIQ#2026"],
];

for (const [email, password] of CREDS) {
  const sb = createClient(URL, KEY, { auth: { persistSession: false } });
  const { data, error } = await sb.auth.signInWithPassword({ email, password });
  if (error) {
    console.log(`✗ FAIL  ${email}  ${error.message}`);
    continue;
  }
  const m = data.user.user_metadata;
  console.log(
    `✔ ${email.padEnd(32)} session=${Boolean(data.session)} role=${m.role} onboarded=${m.onboarding_complete}`,
  );
}
