"use client";

import { useEffect, useRef } from "react";

import { cn } from "@/lib/utils";

/** A single line in the live SSE terminal log. */
export type TerminalLine = {
  ts: number;            // ms since the start of this review run
  event: string;
  text: string;
  level?: "info" | "claim" | "warn" | "head";
};

function fmtMs(ms: number): string {
  const s = ms / 1000;
  return s < 10 ? `+${s.toFixed(2)}s` : `+${s.toFixed(1)}s`;
}

const LEVEL: Record<NonNullable<TerminalLine["level"]>, string> = {
  info:  "text-gov-ink-muted",
  claim: "text-gov-ink",
  warn:  "text-gov-maroon",
  head:  "text-gov-navy font-semibold",
};

/** Light-theme institutional log — JetBrains-Mono, gov-saffron timestamps, auto-scroll. */
export function AgentTerminal({ lines }: { lines: TerminalLine[] }) {
  const scroller = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = scroller.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [lines.length]);

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-sm border border-gov-border bg-gov-surface">
      <div className="flex h-10 shrink-0 items-center justify-between border-b border-gov-border bg-gov-bg px-4">
        <span className="flex items-center gap-2">
          <span className="size-2 animate-pulse-dot rounded-full bg-gov-saffron" />
          <span className="font-sans text-[12px] font-semibold uppercase tracking-wide text-gov-ink">
            Live Evaluation Trace
          </span>
        </span>
        <span className="font-mono text-[11px] tabular-nums text-gov-ink-muted">
          {lines.length} event{lines.length === 1 ? "" : "s"}
        </span>
      </div>
      <div
        ref={scroller}
        className="scrollbar-thin flex-1 overflow-y-auto bg-white px-4 py-3 font-mono text-[12px] leading-[1.6]"
      >
        {lines.length === 0 ? (
          <div className="text-gov-ink-faint">
            Awaiting events… select <span className="font-semibold text-gov-navy">Run AI Review</span> above to begin.
          </div>
        ) : (
          lines.map((l, i) => (
            <div key={i} className="grid grid-cols-[58px_1fr] gap-3">
              <span className="select-none tabular-nums text-gov-saffron">{fmtMs(l.ts)}</span>
              <span className={cn("whitespace-pre-wrap break-words", LEVEL[l.level ?? "info"])}>
                {l.text}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
