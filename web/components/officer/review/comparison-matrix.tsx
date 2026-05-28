"use client";

import { ChevronRight, Crown, ShieldAlert, XCircle } from "lucide-react";

import { MATRIX_COLUMNS, type RankingRow, type ReviewSummary, type Verdict } from "@/lib/review-types";
import { formatINR } from "@/lib/format";
import { cn } from "@/lib/utils";

const VERDICT_CLS: Record<Verdict, string> = {
  PASS: "border-gov-green/40 bg-gov-green-soft text-gov-green",
  FAIL: "border-gov-maroon/40 bg-gov-maroon-soft text-gov-maroon",
  FLAG: "border-gov-saffron/50 bg-gov-saffron-soft text-gov-ink",
  INFO: "border-gov-navy/30 bg-gov-navy-soft text-gov-navy",
};

const ACTION_STYLE: Record<string, { label: string; cls: string; icon?: React.ComponentType<{ className?: string }> }> = {
  award:     { label: "AWARD",     cls: "text-gov-green border-gov-green/40 bg-gov-green-soft", icon: Crown },
  shortlist: { label: "SHORTLIST", cls: "text-gov-navy border-gov-navy/40 bg-gov-navy-soft" },
  review:    { label: "REVIEW",    cls: "text-gov-saffron border-gov-saffron/50 bg-gov-saffron-soft", icon: ShieldAlert },
  reject:    { label: "REJECT",    cls: "text-gov-maroon border-gov-maroon/40 bg-gov-maroon-soft", icon: XCircle },
};

export type CellSelection = { bidId: string; agent: string };

export function ComparisonMatrix({
  summary, onSelectCell, selected,
}: {
  summary: ReviewSummary;
  onSelectCell: (sel: CellSelection) => void;
  selected: CellSelection | null;
}) {
  const verdictsByBid = new Map<string, Record<string, Verdict>>();
  for (const b of summary.bids) {
    const v: Record<string, Verdict> = {};
    for (const a of b.agents) v[a.agent] = a.verdict;
    verdictsByBid.set(b.bid_id, v);
  }
  const rankByBid = new Map(summary.ranking.map((r) => [r.bid_id, r]));

  return (
    <section className="overflow-hidden rounded-sm border border-gov-border bg-gov-surface">
      <header className="border-b border-gov-border bg-gov-bg px-4 py-3">
        <h2 className="font-sans text-[13px] font-semibold uppercase tracking-wide text-gov-ink">
          Evaluation Matrix
        </h2>
        <p className="mt-0.5 text-[12px] text-gov-ink-muted">
          Each cell shows the agent's verdict and citation count for that bidder. Select a cell to inspect the evidence.
        </p>
      </header>
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-gov-border bg-gov-bg">
            <th className="px-4 py-2.5 text-left font-sans text-[11.5px] font-semibold uppercase tracking-wide text-gov-ink-muted">
              Bidder
            </th>
            {MATRIX_COLUMNS.map((c) => (
              <th
                key={c.key}
                className="px-3 py-2.5 text-left font-sans text-[11.5px] font-semibold uppercase tracking-wide text-gov-ink-muted"
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {summary.bids.map((b) => {
            const rank = rankByBid.get(b.bid_id);
            const v = verdictsByBid.get(b.bid_id) ?? {};
            return (
              <tr key={b.bid_id} className="border-b border-gov-border last:border-0">
                <td className="px-4 py-3 align-top">
                  <BidderHeader b={b} rank={rank} />
                </td>
                {MATRIX_COLUMNS.map((c) => {
                  if (c.key === "final") {
                    return (
                      <FinalCell
                        key="final" b={b} rank={rank}
                        active={selected?.bidId === b.bid_id && selected.agent === "final"}
                        onClick={() => onSelectCell({ bidId: b.bid_id, agent: "final" })}
                      />
                    );
                  }
                  const agentName = c.key;
                  const agentBlock = b.agents.find((a) => a.agent === agentName);
                  return (
                    <MatrixCell
                      key={agentName}
                      verdict={v[agentName]}
                      score={
                        agentName === "technical_agent" ? b.technical_score
                        : agentName === "financial_agent" ? b.combined_score
                        : null
                      }
                      claimCount={agentBlock?.claims.length ?? 0}
                      active={selected?.bidId === b.bid_id && selected.agent === agentName}
                      onClick={() => onSelectCell({ bidId: b.bid_id, agent: agentName })}
                    />
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

function BidderHeader({ b, rank }: { b: ReviewSummary["bids"][number]; rank?: RankingRow }) {
  return (
    <div>
      <div className="flex items-center gap-2">
        <span className="font-sans text-[14px] font-semibold text-gov-ink">{b.org_name}</span>
        {rank?.rank && (
          <span className="rounded-sm border border-gov-navy/30 bg-gov-navy-soft px-1.5 py-0.5 font-mono text-[10.5px] font-semibold tabular-nums text-gov-navy">
            L{rank.rank}
          </span>
        )}
      </div>
      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 font-mono text-[11.5px] text-gov-ink-muted">
        <span>{formatINR(b.quoted_amount)}</span>
        {b.technical_score != null && <span>tech&nbsp;{b.technical_score.toFixed(1)}</span>}
        {b.financial_score != null && <span>fin&nbsp;{b.financial_score.toFixed(1)}</span>}
        {b.combined_score != null && (
          <span>combined&nbsp;<span className="text-gov-navy">{b.combined_score.toFixed(2)}</span></span>
        )}
      </div>
    </div>
  );
}

function MatrixCell({
  verdict, score, claimCount, active, onClick,
}: {
  verdict?: Verdict;
  score: number | null;
  claimCount: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <td className="p-1.5 align-top">
      <button
        onClick={onClick}
        className={cn(
          "flex w-full flex-col gap-1.5 rounded-sm border px-3 py-2.5 text-left transition-colors",
          active ? "border-gov-navy bg-gov-navy-soft" : "border-gov-border bg-white hover:border-gov-navy/50 hover:bg-gov-bg",
        )}
      >
        <div className="flex items-center justify-between">
          {verdict ? <VerdictPill verdict={verdict} /> : <span className="font-mono text-[10px] uppercase tracking-wide text-gov-ink-faint">—</span>}
          {claimCount > 0 && (
            <span className="font-mono text-[10.5px] tabular-nums text-gov-ink-faint">
              {claimCount} cite{claimCount === 1 ? "" : "s"}
            </span>
          )}
        </div>
        {score != null && (
          <div className="font-mono text-[12.5px] tabular-nums text-gov-ink">
            {score.toFixed(1)}
            <span className="ml-1 text-[9.5px] text-gov-ink-faint">/ 100</span>
          </div>
        )}
      </button>
    </td>
  );
}

function FinalCell({
  b, rank, active, onClick,
}: {
  b: ReviewSummary["bids"][number];
  rank?: RankingRow;
  active: boolean;
  onClick: () => void;
}) {
  const action = b.recommended_action ?? "—";
  const cfg = ACTION_STYLE[action] ?? null;
  const Icon = cfg?.icon ?? null;
  return (
    <td className="p-1.5 align-top">
      <button
        onClick={onClick}
        className={cn(
          "flex w-full items-center gap-2 rounded-sm border px-3 py-2.5 text-left transition-colors",
          active ? "border-gov-navy bg-gov-navy-soft" : "border-gov-border bg-white hover:border-gov-navy/50 hover:bg-gov-bg",
        )}
      >
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-sm border px-2 py-1 font-sans text-[11px] font-semibold uppercase leading-none tracking-wide",
            cfg?.cls ?? "border-gov-border text-gov-ink-faint",
          )}
        >
          {Icon && <Icon className="size-3" />}
          {cfg?.label ?? "—"}
        </span>
        {rank?.rank ? (
          <span className="font-mono text-[11px] tabular-nums text-gov-ink-muted">L{rank.rank}</span>
        ) : null}
        <ChevronRight className="ml-auto size-3.5 text-gov-ink-faint" />
      </button>
    </td>
  );
}

/** Local gov-themed verdict pill. Used inline so we don't poison the shared UI primitive. */
function VerdictPill({ verdict }: { verdict: Verdict }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-2 py-0.5 font-sans text-[10.5px] font-semibold uppercase leading-none tracking-wide",
        VERDICT_CLS[verdict],
      )}
    >
      {verdict}
    </span>
  );
}
