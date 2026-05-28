"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ClipboardCheck,
  FilePlus,
  FileText,
  Gavel,
  LayoutDashboard,
  type LucideIcon,
  Palette,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { LogoutButton } from "./logout-button";

export type SidebarProfile = {
  full_name: string;
  role: "bidder" | "officer";
  org_name?: string | null;
};

type Item = { label: string; href?: string; icon: LucideIcon; soon?: boolean };

const OFFICER_NAV: Item[] = [
  { label: "Dashboard", href: "/officer/dashboard", icon: LayoutDashboard },
  { label: "New Tender", href: "/officer/tenders/new", icon: FilePlus },
  { label: "Tenders", href: "/officer/tenders", icon: FileText },
  { label: "Reviews", icon: ClipboardCheck, soon: true },
];
const BIDDER_NAV: Item[] = [
  { label: "Tenders", href: "/bidder/tenders", icon: FileText },
  { label: "My Bids", href: "/bidder/submissions", icon: Gavel },
];
const DESIGN_ITEM: Item = { label: "Design Test", href: "/design-test", icon: Palette };

export function Sidebar({ profile }: { profile?: SidebarProfile }) {
  const pathname = usePathname();
  const section = pathname.startsWith("/officer")
    ? "officer"
    : pathname.startsWith("/bidder")
      ? "bidder"
      : (profile?.role ?? "public");

  const items =
    section === "officer" ? OFFICER_NAV : section === "bidder" ? BIDDER_NAV : [];
  const nav = [...items, DESIGN_ITEM];

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-smoke bg-obsidian">
      <div className="flex h-14 items-center gap-2 border-b border-smoke px-4">
        <span className="size-2 rounded-full bg-gold" />
        <span className="font-serif text-[22px] font-medium leading-none text-cream">TenderIQ</span>
      </div>

      <nav className="flex flex-col gap-1 p-3">
        {nav.map((item) => {
          const Icon = item.icon;
          if (item.soon || !item.href) {
            return (
              <span
                key={item.label}
                className="flex cursor-default items-center justify-between rounded-sm px-3 py-2 text-[13px] text-cream-faint"
              >
                <span className="flex items-center gap-3">
                  <Icon className="size-4" />
                  {item.label}
                </span>
                <span className="font-mono text-[10px] uppercase tracking-wide">soon</span>
              </span>
            );
          }
          const active =
            item.href === pathname || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.label}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 rounded-sm px-3 py-2 text-[13px] transition-colors",
                active
                  ? "bg-gold-faint text-cream"
                  : "text-cream-muted hover:bg-obsidian-elevated hover:text-cream",
              )}
            >
              {active && (
                <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-gold" />
              )}
              <Icon
                className={cn(
                  "size-4",
                  active ? "text-gold" : "text-cream-faint group-hover:text-cream-muted",
                )}
              />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto border-t border-smoke p-4">
        {profile ? (
          <div className="space-y-3">
            <div className="min-w-0">
              <p className="truncate font-sans text-[13px] font-medium text-cream">
                {profile.full_name || "Unnamed"}
              </p>
              <p className="truncate font-mono text-[11px] uppercase tracking-wide text-cream-faint">
                {profile.role}
                {profile.org_name ? ` · ${profile.org_name}` : ""}
              </p>
            </div>
            <LogoutButton />
          </div>
        ) : (
          <p className="font-mono text-[11px] text-cream-faint">v0.2.0 · Phase 2</p>
        )}
      </div>
    </aside>
  );
}
