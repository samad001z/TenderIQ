import Link from "next/link";
import { ArrowUpRight, CheckCircle2, Clock, FilePlus, FileSearch } from "lucide-react";

import { GovBreadcrumb } from "@/components/shell/gov-nav";
import { formatINR } from "@/lib/format";
import { createClient } from "@/lib/supabase/server";
import { cn } from "@/lib/utils";

export default async function OfficerTendersPage() {
  const sb = await createClient();
  const { data: tenders } = await sb
    .from("tenders")
    .select("id, title, reference_no, status, parse_status, estimated_value, parsed_schema, last_reviewed_at, created_at")
    .order("created_at", { ascending: false });

  const ids = (tenders ?? []).map((t) => t.id);
  const { data: bidRows } = ids.length
    ? await sb.from("bids").select("tender_id, status").in("tender_id", ids)
    : { data: [] };
  const stats = new Map<string, { submitted: number; total: number; reviewed: number }>();
  for (const id of ids) stats.set(id, { submitted: 0, total: 0, reviewed: 0 });
  for (const b of bidRows ?? []) {
    const s = stats.get(b.tender_id)!;
    s.total += 1;
    if (b.status === "submitted" || b.status === "under_review") s.submitted += 1;
    if (["evaluated", "human_review_required", "rejected", "accepted"].includes(b.status)) s.reviewed += 1;
  }

  return (
    <>
      <GovBreadcrumb items={[{ label: "Home", href: "/officer/dashboard" }, { label: "Tenders" }]} />

      <div className="mt-6 space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-gov-saffron">
              Tenders
            </p>
            <h1 className="mt-1.5 font-sans text-[32px] font-semibold leading-[1.1] tracking-tight text-gov-ink">
              Tenders issued
            </h1>
            <p className="mt-2 max-w-2xl text-[14px] text-gov-ink-muted">
              All tenders issued under your authority. Use <span className="font-semibold text-gov-navy">Run AI Review</span> on a
              tender that has submitted bids to evaluate them against the parsed schema.
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

        <div className="overflow-hidden rounded-lg border border-gov-border bg-gov-surface shadow-gov-sm">
          <table className="w-full">
            <thead className="border-b border-gov-border bg-gov-bg/60">
              <tr className="text-left text-[11px] font-semibold uppercase tracking-wide text-gov-ink-muted">
                <th className="px-5 py-3">Title</th>
                <th className="px-3 py-3">Reference</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">Method</th>
                <th className="px-3 py-3 text-right">Estimate</th>
                <th className="px-3 py-3 text-right">Bids</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gov-border">
              {(tenders ?? []).map((t) => {
                const s = stats.get(t.id) ?? { submitted: 0, total: 0, reviewed: 0 };
                const method = (t.parsed_schema as { evaluation_method?: string } | null)?.evaluation_method;
                const reviewable = t.status === "published" && t.parse_status === "parsed" && (s.submitted + s.reviewed) > 0;
                const reviewLabel = t.last_reviewed_at
                  ? "View review"
                  : s.submitted > 0
                    ? `Run AI Review · ${s.submitted}`
                    : "—";
                return (
                  <tr key={t.id} className="transition-colors hover:bg-gov-bg/40">
                    <td className="px-5 py-4 align-top text-[13.5px] text-gov-ink">
                      <p className="line-clamp-2 max-w-md font-medium leading-snug">{t.title}</p>
                    </td>
                    <td className="px-3 py-4 align-top font-mono text-[12px] text-gov-ink-muted">{t.reference_no ?? "—"}</td>
                    <td className="px-3 py-4 align-top"><StatusPill value={t.status} /></td>
                    <td className="px-3 py-4 align-top"><MethodPill method={method} /></td>
                    <td className="px-3 py-4 text-right align-top font-mono text-[13px] tabular-nums text-gov-ink">
                      {formatINR(t.estimated_value)}
                    </td>
                    <td className="px-3 py-4 text-right align-top">
                      <BidsCount stats={s} />
                    </td>
                    <td className="px-5 py-4 text-right align-top">
                      {reviewable ? (
                        <Link
                          href={`/officer/tenders/${t.id}/review`}
                          className={cn(
                            "group inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 font-sans text-[12.5px] font-semibold transition-colors",
                            t.last_reviewed_at
                              ? "border border-gov-border bg-white text-gov-navy hover:border-gov-navy hover:bg-gov-navy-soft"
                              : "bg-gov-navy text-white shadow-gov-sm hover:bg-gov-navy-hover hover:shadow-gov-md",
                          )}
                        >
                          {t.last_reviewed_at ? <FileSearch className="size-3.5" /> : null}
                          {reviewLabel}
                          <ArrowUpRight className="size-3 opacity-0 transition-opacity group-hover:opacity-100" />
                        </Link>
                      ) : (
                        <span className="font-mono text-[11px] text-gov-ink-faint">{reviewLabel}</span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {(tenders ?? []).length === 0 && (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-[13.5px] text-gov-ink-muted">
                    No tenders yet. <Link href="/officer/tenders/new" className="font-semibold text-gov-navy hover:underline">Upload one</Link>.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

function StatusPill({ value }: { value: string }) {
  const map: Record<string, string> = {
    draft: "border-gov-border bg-gov-bg text-gov-ink-muted",
    published: "border-gov-green/30 bg-gov-green-soft text-gov-green",
    closed: "border-gov-border text-gov-ink-faint",
    awarded: "border-gov-saffron/40 bg-gov-saffron-soft text-gov-ink",
  };
  return (
    <span className={cn(
      "inline-flex rounded-full border px-2 py-0.5 font-sans text-[10.5px] font-semibold uppercase tracking-wide",
      map[value] ?? "border-gov-border text-gov-ink-muted",
    )}>{value}</span>
  );
}

function MethodPill({ method }: { method?: string | null }) {
  const m = (method ?? "—").toUpperCase();
  const known = m === "L1" || m === "QCBS" || m === "LCS";
  return (
    <span className={cn(
      "inline-flex rounded-md border px-2 py-0.5 font-mono text-[11px] font-semibold tracking-wide",
      known ? "border-gov-navy/30 bg-gov-navy-soft text-gov-navy" : "border-gov-border text-gov-ink-faint",
    )}>{m}</span>
  );
}

function BidsCount({ stats }: { stats: { submitted: number; total: number; reviewed: number } }) {
  if (stats.total === 0) return <span className="font-mono text-[12px] text-gov-ink-faint">—</span>;
  const n = stats.submitted + stats.reviewed;
  return (
    <div className="flex flex-col items-end">
      <span className="font-mono text-[14px] font-semibold tabular-nums text-gov-ink">{n}</span>
      {stats.reviewed > 0 ? (
        <span className="inline-flex items-center gap-1 font-mono text-[10.5px] text-gov-green">
          <CheckCircle2 className="size-3" /> reviewed
        </span>
      ) : stats.submitted > 0 ? (
        <span className="inline-flex items-center gap-1 font-mono text-[10.5px] text-gov-saffron">
          <Clock className="size-3" /> ready
        </span>
      ) : null}
    </div>
  );
}
