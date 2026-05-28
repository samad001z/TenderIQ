"use client";

import { Check, Loader2, X } from "lucide-react";

import { ALL_AGENTS, AGENT_LABEL, type Verdict } from "@/lib/review-types";
import { cn } from "@/lib/utils";

export type AgentCellStatus = "idle" | "running" | "done" | "error";

export type AgentCell = {
  status: AgentCellStatus;
  verdict?: Verdict;
  claims?: number;
  elapsedMs?: number;
};

export type BidHeader = { bid_id: string; org_name: string };

const VERDICT_TEXT: Record<Verdict, string> = {
  PASS: "text-gov-green",
  FAIL: "text-gov-maroon",
  FLAG: "text-gov-saffron",
  INFO: "text-gov-navy",
};

export function AgentGrid({
  bids,
  cells,
}: {
  bids: BidHeader[];
  cells: Record<string, AgentCell | undefined>;
}) {
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-sm border border-gov-border bg-gov-surface">
      <div className="flex h-10 shrink-0 items-center justify-between border-b border-gov-border bg-gov-bg px-4">
        <span className="font-sans text-[12px] font-semibold uppercase tracking-wide text-gov-ink">
          Agent Progress
        </span>
        <span className="font-mono text-[11px] tabular-nums text-gov-ink-muted">
          {ALL_AGENTS.length} agents × {bids.length} bid{bids.length === 1 ? "" : "s"}
        </span>
      </div>
      <div className="scrollbar-thin flex-1 overflow-y-auto p-3">
        <div
          className="grid gap-2"
          style={{ gridTemplateColumns: `132px repeat(${Math.max(1, bids.length)}, minmax(0,1fr))` }}
        >
          <div />
          {bids.map((b) => (
            <div key={b.bid_id} className="px-2 pb-1 text-[12px] font-semibold text-gov-ink truncate">
              {b.org_name}
            </div>
          ))}
          {ALL_AGENTS.map((agent) => (
            <Row key={agent} agent={agent} bids={bids} cells={cells} />
          ))}
        </div>
      </div>
    </div>
  );
}

function Row({
  agent, bids, cells,
}: {
  agent: string;
  bids: BidHeader[];
  cells: Record<string, AgentCell | undefined>;
}) {
  return (
    <>
      <div className="flex items-center font-mono text-[11px] uppercase tracking-wide text-gov-ink-muted">
        {AGENT_LABEL[agent] ?? agent}
      </div>
      {bids.map((b) => {
        const cell = cells[`${b.bid_id}::${agent}`] ?? { status: "idle" };
        return <Cell key={b.bid_id + agent} cell={cell} />;
      })}
    </>
  );
}

function Cell({ cell }: { cell: AgentCell }) {
  const { status, verdict, claims, elapsedMs } = cell;
  return (
    <div
      className={cn(
        "rounded-sm border px-2.5 py-2 transition-colors",
        status === "idle" && "border-gov-border bg-white",
        status === "running" && "border-gov-saffron bg-gov-saffron-soft",
        status === "done" && "border-gov-border bg-gov-bg",
        status === "error" && "border-gov-maroon/40 bg-gov-maroon-soft",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <Indicator status={status} verdict={verdict} />
        {typeof elapsedMs === "number" && status === "done" && (
          <span className="font-mono text-[10px] tabular-nums text-gov-ink-faint">
            {(elapsedMs / 1000).toFixed(1)}s
          </span>
        )}
      </div>
      <div className="mt-1 flex items-baseline justify-between">
        <span className={cn("font-mono text-[10px] uppercase tracking-wide", verdict ? VERDICT_TEXT[verdict] : "text-gov-ink-faint")}>
          {status === "done" ? (verdict ?? "—") : status === "running" ? "running" : status === "error" ? "error" : "queued"}
        </span>
        <span className="font-mono text-[11px] tabular-nums text-gov-ink">
          {typeof claims === "number" ? claims : ""}
          {typeof claims === "number" && (
            <span className="ml-1 text-[9px] text-gov-ink-faint">claim{claims === 1 ? "" : "s"}</span>
          )}
        </span>
      </div>
    </div>
  );
}

function Indicator({ status, verdict }: { status: AgentCellStatus; verdict?: Verdict }) {
  if (status === "running") return <Loader2 className="size-3.5 animate-spin text-gov-saffron" />;
  if (status === "done") {
    if (verdict === "FAIL") return <X className="size-3.5 text-gov-maroon" />;
    if (verdict === "FLAG") return <span className="size-2 rounded-full bg-gov-saffron" />;
    if (verdict === "INFO") return <span className="size-2 rounded-full bg-gov-navy" />;
    return <Check className="size-3.5 text-gov-green" />;
  }
  if (status === "error") return <X className="size-3.5 text-gov-maroon" />;
  return <span className="size-2 rounded-full bg-gov-ink-faint/40" />;
}
