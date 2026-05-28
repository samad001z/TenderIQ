import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { GovShell } from "@/components/shell/gov-shell";
import { createClient } from "@/lib/supabase/server";

/** Officers only — institutional government-portal shell (Phase 7). */
export default async function OfficerLayout({ children }: { children: ReactNode }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: profile } = await supabase
    .from("profiles")
    .select("full_name, role, ministry, department")
    .eq("id", user.id)
    .single();

  if (profile?.role !== "officer") redirect("/bidder/tenders");
  const ministry = [profile?.ministry, profile?.department].filter(Boolean).join(" / ");

  return (
    <GovShell fullName={profile?.full_name || "Officer"} ministry={ministry || null}>
      {children}
    </GovShell>
  );
}
