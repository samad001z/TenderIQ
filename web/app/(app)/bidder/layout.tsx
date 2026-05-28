import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { AppShell } from "@/components/shell/app-shell";
import { createClient } from "@/lib/supabase/server";

/** Bidders only — warmer (carbon) shell. */
export default async function BidderLayout({ children }: { children: ReactNode }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: profile } = await supabase
    .from("profiles")
    .select("full_name, role, org_name")
    .eq("id", user.id)
    .single();

  if (profile?.role !== "bidder") redirect("/officer/dashboard");
  return (
    <AppShell
      tone="carbon"
      profile={{ full_name: profile.full_name, role: profile.role, org_name: profile.org_name }}
    >
      {children}
    </AppShell>
  );
}
