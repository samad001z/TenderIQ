"use client";

import { FileText, X } from "lucide-react";

import type { ClaimRow, ReviewSummary, Severity, Verdict } from "@/lib/review-types";
import { AGENT_LABEL } from "@/lib/review-types";
import { cn } from "@/lib/utils";

const VERDICT_CLS: Record<Verdict, string> = {
  PASS: "border-gov-green/40 bg-gov-green-soft text-gov-green",
  FAIL: "border-gov-maroon/40 bg-gov-maroon-soft text-gov-maroon",
  FLAG: "border-gov-saffron/50 bg-gov-saffron-soft text-gov-ink",
  INFO: "border-gov-navy/30 bg-gov-navy-soft text-gov-navy",
};
const SEVERITY_DOT: Record<Severity, string> = {
  low:      "bg-gov-navy",
  medium:   "bg-gov-saffron",
  high:     "bg-gov-saffron",
  critical: "bg-gov-maroon",
};

export type DrawerSelection = { bidId: string; agent: string };

export function CitationDrawer({
  open, selection, summary, onClose, onOpenCitation,
}: {
  open: boolean;
  selection: DrawerSelection | null;
  summary: ReviewSummary;
  onClose: () => void;
  onOpenCitation: (claim: ClaimRow) => void;
}) {
  const bid = selection ? summary.bids.find((b) => b.bid_id === selection.bidId) : null;
  const isFinal = selection?.agent === "final";
  const agentBlock = bid && !isFinal ? bid.agents.find((a) => a.agent === selection!.agent) : null;
  const claims: ClaimRow[] = isFinal && bid
    ? bid.agents.flatMap((a) => a.claims).filter(
        (c) => c.severity === "critical" || c.verdict === "FAIL" || c.agent === "reasoning_agent",
      )
    : (agentBlock?.claims ?? []);
  const verdict: Verdict | undefined = isFinal
    ? (bid?.recommended_action === "reject" ? "FAIL" : bid?.recommended_action === "review" ? "FLAG" : "PASS")
    : agentBlock?.verdict;
  const heading = isFinal
    ? "Final recommendation"
    : (AGENT_LABEL[selection?.agent ?? ""] ?? selection?.agent ?? "");

  return (
    <>
      <div
        onClick={onClose}
        className={cn(
          "fixed inset-0 z-30 bg-gov-ink/30 backdrop-blur-[1px] transition-opacity",
          open ? "opacity-100" : "pointer-events-none opacity-0",
        )}
      />
      <aside
        className={cn(
          "fixed right-0 top-0 z-40 flex h-screen w-[420px] flex-col border-l border-gov-border bg-gov-surface shadow-2xl transition-transform duration-200",
          open ? "translate-x-0" : "translate-x-full",
        )}
      >
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-gov-border bg-gov-bg px-4">
          <div className="min-w-0">
            <div className="truncate font-mono text-[10.5px] uppercase tracking-wide text-gov-ink-muted">
              {bid?.org_name ?? "—"}
            </div>
            <div className="flex items-center gap-2">
              <span className="font-sans text-[15px] font-semibold text-gov-ink">{heading}</span>
              {verdict && (
                <span className={cn("inline-flex items-center rounded-sm border px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide", VERDICT_CLS[verdict])}>
                  {verdict}
                </span>
              )}
            </div>
          </div>
          <button onClick={onClose} className="rounded-sm p-1.5 text-gov-ink-muted hover:bg-gov-bg hover:text-gov-ink">
            <X className="size-4" />
          </button>
        </div>

        {isFinal && bid && (
          <div className="border-b border-gov-border bg-gov-bg px-4 py-3">
            {bid.summary && <p className="font-sans text-[13.5px] leading-snug text-gov-ink">{bid.summary}</p>}
            {bid.rationale && (
              <p className="mt-2 font-serif text-[13px] italic leading-snug text-gov-ink-muted">{bid.rationale}</p>
            )}
          </div>
        )}

        <div className="scrollbar-thin flex-1 overflow-y-auto px-4 py-3">
          {claims.length === 0 && (
            <p className="text-[13px] text-gov-ink-muted">No citations to display.</p>
          )}
          <div className="space-y-3">
            {claims.map((c, i) => (
              <ClaimCard key={i} c={c} onOpen={() => onOpenCitation(c)} />
            ))}
          </div>
        </div>
      </aside>
    </>
  );
}

function ClaimCard({ c, onOpen }: { c: ClaimRow; onOpen: () => void }) {
  return (
    <div className="rounded-sm border border-gov-border bg-white p-3">
      <div className="flex items-center justify-between gap-2">
        <span className={cn(
          "inline-flex items-center rounded-sm border px-2 py-0.5 font-sans text-[10.5px] font-semibold uppercase leading-none tracking-wide",
          VERDICT_CLS[c.verdict],
        )}>
          {c.verdict}
        </span>
        <span className="flex items-center gap-1 font-mono text-[10.5px] uppercase tracking-wide text-gov-ink-muted">
          <span className={cn("size-2 rounded-full", SEVERITY_DOT[c.severity])} />
          {c.severity}
        </span>
      </div>
      <p className="mt-2 text-[13px] leading-snug text-gov-ink">{c.claim}</p>
      {c.quote && (
        <p className="mt-2 font-serif italic text-[12.5px] leading-snug text-gov-ink-muted">
          “{c.quote.length > 280 ? c.quote.slice(0, 280) + "…" : c.quote}”
        </p>
      )}
      <div className="mt-2 flex items-center justify-between gap-2">
        <button
          onClick={onOpen}
          className="inline-flex items-center gap-1.5 rounded-sm border border-gov-navy/30 bg-gov-navy-soft px-2 py-1 font-mono text-[11.5px] text-gov-navy hover:border-gov-navy hover:bg-white"
          aria-label="Open evidence page"
        >
          <FileText className="size-3" />
          {c.source_doc}
          <span className="text-gov-ink-faint">·</span>
          <span className="text-gov-saffron font-semibold">p.{c.page_number}</span>
        </button>
        <span className="font-mono text-[10.5px] tabular-nums text-gov-ink-faint">
          conf {Math.round((c.confidence ?? 0) * 100)}%
        </span>
      </div>
      <div className="mt-1 h-0.5 w-full overflow-hidden rounded-full bg-gov-border">
        <div
          className="h-full bg-gov-navy/70"
          style={{ width: `${Math.max(2, Math.min(100, (c.confidence ?? 0) * 100))}%` }}
        />
      </div>
    </div>
  );
}
