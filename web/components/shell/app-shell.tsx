import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import { Sidebar, type SidebarProfile } from "./sidebar";
import { Topbar } from "./topbar";

/** App frame: 240px sidebar + 56px topbar + centered max-w-1440 content.
 *  tone="carbon" gives the bidder portal a slightly warmer backdrop. */
export function AppShell({
  children,
  profile,
  title,
  subtitle,
  tone = "obsidian",
}: {
  children: ReactNode;
  profile?: SidebarProfile;
  title?: string;
  subtitle?: string;
  tone?: "obsidian" | "carbon";
}) {
  const bg = tone === "carbon" ? "bg-carbon" : "bg-obsidian";
  return (
    <div className={cn("flex h-screen overflow-hidden", bg)}>
      <Sidebar profile={profile} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar title={title} subtitle={subtitle} />
        <main className={cn("flex-1 overflow-y-auto scrollbar-thin", bg)}>
          <div className="mx-auto w-full max-w-content px-8 py-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
