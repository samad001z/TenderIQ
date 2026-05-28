"use client";

import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase/client";

/** Logout in the gov-shell visual style (navy on light). */
export function GovLogoutButton() {
  const router = useRouter();
  async function logout() {
    await createClient().auth.signOut();
    router.push("/login");
    router.refresh();
  }
  return (
    <button
      onClick={logout}
      className="inline-flex items-center gap-1.5 rounded-sm border border-gov-border bg-gov-surface px-3 py-1.5 text-[12px] text-gov-ink-muted transition-colors hover:border-gov-navy hover:text-gov-navy"
    >
      <LogOut className="size-3.5" />
      Sign out
    </button>
  );
}
