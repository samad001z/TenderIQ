"use client";

import { ArrowRight, ChevronDown, FileSearch } from "lucide-react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { fetchTenderFileUrl, getAccessToken } from "@/lib/api";
import { formatINR } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { TenderSchema } from "@/lib/tender-schema";

const PdfViewer = dynamic(
  () => import("@/components/officer/pdf-viewer").then((m) => m.PdfViewer),
  { ssr: false, loading: () => <p className="p-4 text-[13px] text-cream-muted">Loading viewer…</p> },
);

type Meta = { title: string; ministry: string | null; reference_no: string | null; estimated_value: number | null };
type Row = { label: string; value: React.ReactNode; page: number };

function SrcChip({ page, onJump }: { page: number; onJump: (p: number) => void }) {
  if (!page) return <span className="font-mono text-[11px] text-cream-faint">—</span>;
  return (
    <button
      onClick={() => onJump(page)}
      className="inline-flex items-center gap-1 rounded-sm border border-smoke bg-carbon-elevated px-2 py-0.5 font-mono text-[11px] text-gold transition-colors hover:border-gold"
    >
      <FileSearch className="size-3" />
      p.{page}
    </button>
  );
}

function Collapsible({
  title,
  count,
  rows,
  onJump,
  defaultOpen = false,
}: {
  title: string;
  count?: number;
  rows: Row[];
  onJump: (p: number) => void;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-smoke">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="font-sans text-[12px] font-semibold uppercase tracking-wide text-cream">
          {title}
          {count != null && <span className="ml-2 text-cream-faint">· {count}</span>}
        </span>
        <ChevronDown className={cn("size-4 text-cream-muted transition-transform", open && "rotate-180")} />
      </button>
      {open && (
        <div className="px-4 pb-3">
          {rows.map((r, i) => (
            <div key={i} className="flex items-start justify-between gap-3 border-t border-smoke py-2.5 first:border-t-0">
              <div className="min-w-0">
                <p className="font-mono text-[10px] uppercase tracking-wide text-cream-faint">{r.label}</p>
                <p className="mt-0.5 text-[13px] leading-snug text-cream">{r.value}</p>
              </div>
              <SrcChip page={r.page} onJump={onJump} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function TenderDetail({
  tenderId,
  meta,
  schema,
}: {
  tenderId: string;
  meta: Meta;
  schema: TenderSchema | null;
}) {
  const [signedUrl, setSignedUrl] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const token = await getAccessToken();
      if (!token) return setError("Your session expired — sign in again.");
      try {
        setSignedUrl(await fetchTenderFileUrl(tenderId, token));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load the PDF.");
      }
    })();
  }, [tenderId]);

  const s = schema;
  const eligibility: Row[] = (s?.eligibility_criteria ?? []).map((c, i) => ({
    label: `Criterion ${i + 1}`,
    value: c.description,
    page: c.source_page,
  }));
  const technical: Row[] = (s?.technical_criteria ?? []).map((c, i) => ({
    label: c.weight != null ? `${c.weight} marks` : `Criterion ${i + 1}`,
    value: c.description,
    page: c.source_page,
  }));
  const financial: Row[] = s
    ? [
        { label: "Format", value: s.financial_format.value || "—", page: s.financial_format.source_page },
        { label: "EMD", value: formatINR(s.emd_amount.value), page: s.emd_amount.source_page },
        { label: "Performance guarantee", value: s.pbg_percentage.value != null ? `${s.pbg_percentage.value}%` : "—", page: s.pbg_percentage.source_page },
      ]
    : [];
  const compliance: Row[] = s
    ? [
        {
          label: "Evaluation method",
          value: s.evaluation_method === "QCBS" ? `QCBS · ${s.qcbs_weights.technical}% tech / ${s.qcbs_weights.financial}% cost` : s.evaluation_method,
          page: s.evaluation_method_source_page,
        },
        { label: "Integrity pact", value: s.integrity_pact_required.value ? "Required" : "Not required", page: s.integrity_pact_required.source_page },
        { label: "PPP-MII class", value: s.ppp_mii_class === "none" ? "Open" : `Class ${s.ppp_mii_class}`, page: s.ppp_mii_source_page },
        { label: "Submission deadline", value: s.submission_deadline.value || "—", page: s.submission_deadline.source_page },
      ]
    : [];

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="font-serif text-[28px] font-medium leading-tight text-cream">{meta.title}</h1>
          <p className="mt-1 font-mono text-[12px] text-cream-muted">
            {meta.reference_no ?? "—"} · {meta.ministry ?? "—"} · {formatINR(meta.estimated_value)}
          </p>
        </div>
        <Button asChild>
          <Link href={`/bidder/tenders/${tenderId}/apply`}>
            Apply to this Tender <ArrowRight />
          </Link>
        </Button>
      </div>

      <div className="grid h-[calc(100vh-220px)] grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="overflow-hidden rounded-lg border border-smoke bg-carbon-surface">
          {signedUrl ? (
            <PdfViewer url={signedUrl} page={page} />
          ) : (
            <p className="p-4 text-[13px] text-cream-muted">{error ?? "Loading PDF…"}</p>
          )}
        </div>
        <div className="overflow-y-auto scrollbar-thin rounded-lg border border-smoke bg-carbon-surface">
          {s ? (
            <>
              <Collapsible title="Eligibility" count={eligibility.length} rows={eligibility} onJump={setPage} defaultOpen />
              <Collapsible title="Technical" count={technical.length} rows={technical} onJump={setPage} />
              <Collapsible title="Financial" rows={financial} onJump={setPage} />
              <Collapsible title="Compliance" rows={compliance} onJump={setPage} />
            </>
          ) : (
            <p className="p-4 text-[13px] text-cream-muted">Schema not available for this tender.</p>
          )}
        </div>
      </div>
    </div>
  );
}
