"use client";

import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase/client";

export function LogoutButton() {
  const router = useRouter();
  async function logout() {
    await createClient().auth.signOut();
    router.push("/login");
    router.refresh();
  }
  return (
    <button
      onClick={logout}
      className="flex items-center gap-2 text-[12px] text-cream-muted transition-colors hover:text-cream"
    >
      <LogOut className="size-4" />
      Sign out
    </button>
  );
}
