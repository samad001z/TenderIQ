import { NextResponse } from "next/server";

import { createAdminClient } from "@/lib/supabase/admin";

// Next.js route handler (same-origin, NOT the FastAPI backend). Creates an
// email-confirmed user via the service role so signup works regardless of the
// Supabase "Confirm email" dashboard setting. The client then signs in to get
// a session. Profile is auto-created by the handle_new_user trigger.
export const runtime = "nodejs";

export async function POST(request: Request) {
  let body: { email?: string; password?: string; role?: string; full_name?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const { email, password, role, full_name } = body;
  if (!email || !password) {
    return NextResponse.json({ error: "Email and password are required." }, { status: 400 });
  }
  if (password.length < 8) {
    return NextResponse.json({ error: "Password must be at least 8 characters." }, { status: 400 });
  }
  if (role !== "bidder" && role !== "officer") {
    return NextResponse.json({ error: "Please choose a valid role." }, { status: 400 });
  }

  const admin = createAdminClient();
  const { error } = await admin.auth.admin.createUser({
    email,
    password,
    email_confirm: true,
    user_metadata: { role, full_name: full_name ?? "" },
  });

  if (error) {
    const exists = /registered|already|exists/i.test(error.message);
    return NextResponse.json(
      { error: exists ? "An account with this email already exists." : error.message },
      { status: exists ? 409 : 400 },
    );
  }

  return NextResponse.json({ ok: true });
}
