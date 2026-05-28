/**
 * Seeds TenderIQ test data via the Supabase SERVICE ROLE (bypasses RLS).
 * Creates 1 officer + 2 bidders (email auto-confirmed), completes their profiles,
 * and seeds a published + draft tender with two bids — so RLS can be verified.
 *
 * Run from /web:
 *   node --env-file=../.env.local scripts/seed_test_users.mjs
 * (reads SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY from the root .env.local)
 */
import { createClient } from "@supabase/supabase-js";

const URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
if (!URL || !SERVICE_KEY) {
  console.error("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in env.");
  process.exit(1);
}

const admin = createClient(URL, SERVICE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false },
});

const PASSWORD = "TenderIQ#2026";

const USERS = [
  {
    key: "officer",
    email: "officer@tenderiq.test",
    role: "officer",
    full_name: "Anita Deshpande",
    profile: {
      org_name: "Ministry of Road Transport & Highways",
      ministry: "MoRTH",
      department: "National Highways",
      phone: "+91 90000 11111",
    },
  },
  {
    key: "bidderA",
    email: "bidder.meridian@tenderiq.test",
    role: "bidder",
    full_name: "Rohan Mehta",
    profile: {
      org_name: "Meridian Infra Pvt Ltd",
      gst_number: "27ABCDE1234F1Z5",
      pan_number: "ABCDE1234F",
      phone: "+91 90000 22222",
    },
  },
  {
    key: "bidderB",
    email: "bidder.orbit@tenderiq.test",
    role: "bidder",
    full_name: "Priya Nair",
    profile: {
      org_name: "Orbit Engineering LLP",
      gst_number: "29ZZZZZ9876Q1Z2",
      pan_number: "ZZZZZ9876Q",
      phone: "+91 90000 33333",
    },
  },
];

async function deleteExisting() {
  // Make the script idempotent — remove any prior test users by email.
  const emails = new Set(USERS.map((u) => u.email));
  let page = 1;
  for (;;) {
    const { data, error } = await admin.auth.admin.listUsers({ page, perPage: 200 });
    if (error) throw error;
    for (const u of data.users) {
      if (emails.has(u.email)) {
        await admin.auth.admin.deleteUser(u.id); // cascades to profiles/tenders/bids
      }
    }
    if (data.users.length < 200) break;
    page += 1;
  }
}

async function main() {
  await deleteExisting();

  const ids = {};
  for (const u of USERS) {
    const { data, error } = await admin.auth.admin.createUser({
      email: u.email,
      password: PASSWORD,
      email_confirm: true,
      user_metadata: { role: u.role, full_name: u.full_name },
    });
    if (error) throw new Error(`createUser ${u.email}: ${error.message}`);
    const id = data.user.id;
    ids[u.key] = id;

    // Trigger already inserted the profile; complete it.
    const { error: pErr } = await admin
      .from("profiles")
      .update({ ...u.profile, onboarding_complete: true })
      .eq("id", id);
    if (pErr) throw new Error(`profile ${u.email}: ${pErr.message}`);

    // Mirror onboarding flag into metadata (middleware reads it).
    await admin.auth.admin.updateUserById(id, {
      user_metadata: { role: u.role, full_name: u.full_name, onboarding_complete: true },
    });
    console.log(`✔ ${u.role.padEnd(7)} ${u.email}  ${id}`);
  }

  // Tenders owned by the officer.
  const { data: tenders, error: tErr } = await admin
    .from("tenders")
    .insert([
      {
        owner_id: ids.officer,
        reference_no: "GEM/2026/B/4821907",
        title: "Construction of 4-lane bypass — NH-65, Hyderabad",
        description: "Design & build of a 12 km 4-lane bypass with structures.",
        status: "published",
        ministry: "MoRTH",
        department: "National Highways",
        estimated_value: 124500000,
        emd_amount: 2500000,
        published_at: new Date().toISOString(),
        closing_at: new Date(Date.now() + 30 * 864e5).toISOString(),
      },
      {
        owner_id: ids.officer,
        reference_no: "GEM/2026/B/4820011",
        title: "Supply of traffic management systems (DRAFT)",
        status: "draft",
        ministry: "MoRTH",
        department: "National Highways",
        estimated_value: 32000000,
      },
    ])
    .select("id, status");
  if (tErr) throw new Error(`tenders: ${tErr.message}`);
  const published = tenders.find((t) => t.status === "published");
  const draft = tenders.find((t) => t.status === "draft");
  ids.tenderPublished = published.id;
  ids.tenderDraft = draft.id;

  // Bids on the published tender.
  const { data: bids, error: bErr } = await admin
    .from("bids")
    .insert([
      { tender_id: published.id, bidder_id: ids.bidderA, status: "submitted", quoted_amount: 124500000, submitted_at: new Date().toISOString() },
      { tender_id: published.id, bidder_id: ids.bidderB, status: "submitted", quoted_amount: 98750000, submitted_at: new Date().toISOString() },
    ])
    .select("id, bidder_id");
  if (bErr) throw new Error(`bids: ${bErr.message}`);
  ids.bidA = bids.find((b) => b.bidder_id === ids.bidderA).id;
  ids.bidB = bids.find((b) => b.bidder_id === ids.bidderB).id;

  console.log("\nSEED_IDS " + JSON.stringify(ids));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
