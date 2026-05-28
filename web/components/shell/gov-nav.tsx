"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";

import { cn } from "@/lib/utils";

type NavItem = { label: string; href: string };

const NAV: NavItem[] = [
  { label: "Dashboard", href: "/officer/dashboard" },
  { label: "Tenders", href: "/officer/tenders" },
  { label: "New Tender", href: "/officer/tenders/new" },
];

/** Horizontal primary navigation in deep navy — government-portal style. */
export function GovNav() {
  const pathname = usePathname() ?? "";
  return (
    <nav aria-label="Primary" className="border-b border-gov-border bg-gov-navy">
      <div className="mx-auto flex max-w-content items-stretch px-3">
        {NAV.map((item) => {
          const active =
            pathname === item.href ||
            (item.href !== "/officer/dashboard" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "relative flex items-center px-5 py-3 font-sans text-[13px] font-semibold tracking-wide text-white/85 transition-colors hover:bg-white/10 hover:text-white",
                active && "bg-white text-gov-navy hover:bg-white",
              )}
            >
              {item.label}
              {active && (
                <span className="pointer-events-none absolute -bottom-[1px] left-0 right-0 h-[2px] bg-gov-saffron" />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

/** Breadcrumb trail — slot-style: pass the labels you want shown.
 *  e.g. <GovBreadcrumb items={[{label:"Home", href:"/officer/dashboard"}, {label:"Tenders", href:"/officer/tenders"}, {label:"Review"}]} /> */
export function GovBreadcrumb({
  items,
}: {
  items: Array<{ label: string; href?: string }>;
}) {
  return (
    <nav
      aria-label="Breadcrumb"
      className="border-b border-gov-border bg-gov-bg"
    >
      <ol className="mx-auto flex max-w-content items-center gap-1 px-6 py-2 text-[12px] text-gov-ink-muted">
        {items.map((it, i) => {
          const last = i === items.length - 1;
          return (
            <li key={i} className="flex items-center gap-1">
              {i > 0 && <ChevronRight className="size-3 text-gov-ink-faint" aria-hidden />}
              {it.href && !last ? (
                <Link href={it.href} className="hover:text-gov-navy hover:underline">
                  {it.label}
                </Link>
              ) : (
                <span className={cn(last && "text-gov-ink font-semibold")} aria-current={last ? "page" : undefined}>
                  {it.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
