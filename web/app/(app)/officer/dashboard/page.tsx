import Link from "next/link";
import { ArrowUpRight, ClipboardCheck, FilePlus, FileText, ShieldCheck } from "lucide-react";

import { GovBreadcrumb } from "@/components/shell/gov-nav";
import { formatINR } from "@/lib/format";
import { createClient } from "@/lib/supabase/server";
import { cn } from "@/lib/utils";

export default async function OfficerDashboardPage() {
  const sb = await createClient();
  const { data: tenders } = await sb
    .from("tenders")
    .select("id, title, status, last_reviewed_at, estimated_value, parse_status, reference_no")
    .order("created_at", { ascending: false });

  const counts = { published: 0, drafts: 0, reviewed: 0 };
  for (const t of tenders ?? []) {
    if (t.status === "published") counts.published += 1;
    if (t.status === "draft") counts.drafts += 1;
    if (t.last_reviewed_at) counts.reviewed += 1;
  }
  const recent = (tenders ?? []).slice(0, 5);

  return (
    <>
      <GovBreadcrumb items={[{ label: "Home" }]} />

      <div className="mt-6 space-y-8">
        {/* Hero */}
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-gov-saffron">
              Officer Workspace
            </p>
            <h1 className="mt-1.5 font-sans text-[34px] font-semibold leading-[1.1] tracking-tight text-gov-ink">
              Dashboard
            </h1>
            <p className="mt-2 max-w-2xl text-[14.5px] leading-relaxed text-gov-ink-muted">
              Issue tenders, evaluate submitted bids with the AI-assisted review pipeline, and download
              CAG-style audit reports. Every recommendation is grounded in a page-cited verbatim quote.
            </p>
          </div>
          <Link
            href="/officer/tenders/new"
            className="inline-flex items-center gap-2 rounded-md bg-gov-navy px-5 py-2.5 font-sans text-[13.5px] font-semibold text-white shadow-gov-sm hover:bg-gov-navy-hover hover:shadow-gov-md"
          >
            <FilePlus className="size-4" />
            Upload new tender
          </Link>
        </div>

        {/* Stat tiles */}
        <div className="grid gap-4 sm:grid-cols-3">
          <StatTile label="Tenders published" value={counts.published} icon={FileText} accent="navy" />
          <StatTile label="Tenders in draft" value={counts.drafts} icon={FilePlus} accent="saffron" />
          <StatTile label="Tenders reviewed" value={counts.reviewed} icon={ShieldCheck} accent="green" />
        </div>

        {/* Recent tenders */}
        <section className="overflow-hidden rounded-lg border border-gov-border bg-gov-surface shadow-gov-sm">
          <header className="flex items-center justify-between border-b border-gov-border px-5 py-4">
            <div>
              <h2 className="font-sans text-[15px] font-semibold text-gov-ink">
                Recent tenders
              </h2>
              <p className="mt-0.5 text-[12.5px] text-gov-ink-muted">
                The most recent {recent.length} tender{recent.length === 1 ? "" : "s"} you've issued.
              </p>
            </div>
            <Link
              href="/officer/tenders"
              className="inline-flex items-center gap-1 rounded-md px-3 py-1.5 font-sans text-[13px] font-semibold text-gov-navy hover:bg-gov-navy-soft"
            >
              View all
              <ArrowUpRight className="size-3.5" />
            </Link>
          </header>
          <ul className="divide-y divide-gov-border">
            {recent.length === 0 && (
              <li className="px-5 py-10 text-center text-[13.5px] text-gov-ink-muted">
                No tenders yet. <Link href="/officer/tenders/new" className="font-semibold text-gov-navy hover:underline">Upload one</Link>.
              </li>
            )}
            {recent.map((t) => (
              <li key={t.id} className="flex items-center gap-5 px-5 py-4 hover:bg-gov-bg/50">
                <div className="min-w-0 flex-1">
                  <p className="font-sans text-[14px] font-medium text-gov-ink line-clamp-1">
                    {t.title}
                  </p>
                  <p className="mt-1 flex items-center gap-3 font-mono text-[11.5px] text-gov-ink-muted">
                    <StatusChip value={t.status} />
                    <span>{formatINR(t.estimated_value)}</span>
                    {t.last_reviewed_at && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-gov-green-soft px-2 py-0.5 text-[10.5px] font-semibold text-gov-green">
                        <ClipboardCheck className="size-2.5" />
                        reviewed
                      </span>
                    )}
                  </p>
                </div>
                <Link
                  href={`/officer/tenders/${t.id}/review`}
                  className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-gov-border bg-white px-3 py-1.5 font-sans text-[12.5px] font-semibold text-gov-navy hover:border-gov-navy hover:bg-gov-navy-soft"
                >
                  Open review
                  <ArrowUpRight className="size-3" />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  );
}

function StatTile({
  label, value, icon: Icon, accent,
}: {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  accent: "navy" | "saffron" | "green";
}) {
  const ACCENT = {
    navy: { wrap: "bg-gov-navy-soft text-gov-navy", bar: "bg-gov-navy" },
    saffron: { wrap: "bg-gov-saffron-soft text-gov-saffron", bar: "bg-gov-saffron" },
    green: { wrap: "bg-gov-green-soft text-gov-green", bar: "bg-gov-green" },
  }[accent];
  return (
    <div className="relative overflow-hidden rounded-lg border border-gov-border bg-gov-surface px-5 py-5 shadow-gov-sm transition-shadow hover:shadow-gov-md">
      <span aria-hidden className={cn("absolute left-0 top-0 h-full w-[3px]", ACCENT.bar)} />
      <div className="flex items-start justify-between">
        <div>
          <p className="font-sans text-[11.5px] font-semibold uppercase tracking-wide text-gov-ink-muted">
            {label}
          </p>
          <p className="mt-2 font-sans text-[36px] font-semibold leading-none tabular-nums text-gov-ink">
            {value}
          </p>
        </div>
        <div className={cn("grid size-9 place-items-center rounded-md", ACCENT.wrap)}>
          <Icon className="size-4.5" />
        </div>
      </div>
    </div>
  );
}

function StatusChip({ value }: { value: string }) {
  const cls: Record<string, string> = {
    draft: "border-gov-border bg-gov-bg text-gov-ink-muted",
    published: "border-gov-green/30 bg-gov-green-soft text-gov-green",
    closed: "border-gov-border text-gov-ink-faint",
    awarded: "border-gov-saffron/40 bg-gov-saffron-soft text-gov-ink",
  };
  return (
    <span className={cn(
      "inline-flex rounded-full border px-2 py-0.5 font-sans text-[10.5px] font-semibold uppercase tracking-wide",
      cls[value] ?? "border-gov-border text-gov-ink-muted",
    )}>{value}</span>
  );
}
