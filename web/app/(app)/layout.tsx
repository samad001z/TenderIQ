import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { createClient } from "@/lib/supabase/server";

// This layout reads cookies + auth on every request, so the whole protected
// tree must run dynamically. Scoped here so the root layout's `next/font/google`
// imports stay out of the Edge middleware bundle (otherwise __dirname blows up).
export const dynamic = "force-dynamic";

/** Auth + onboarded gate. The shell (and its tone) is applied per-role below. */
export default async function AppLayout({ children }: { children: ReactNode }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: profile } = await supabase
    .from("profiles")
    .select("onboarding_complete")
    .eq("id", user.id)
    .single();

  if (!profile || !profile.onboarding_complete) redirect("/onboarding");
  return <>{children}</>;
}
