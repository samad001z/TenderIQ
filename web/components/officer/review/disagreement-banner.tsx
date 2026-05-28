"use client";

import { AlertTriangle, ChevronDown, Copy, Users2 } from "lucide-react";
import { useState } from "react";

import type { Disagreement, Verdict } from "@/lib/review-types";
import { cn } from "@/lib/utils";

const VERDICT_CLS: Record<Verdict, string> = {
  PASS: "border-gov-green/40 bg-gov-green-soft text-gov-green",
  FAIL: "border-gov-maroon/40 bg-gov-maroon-soft text-gov-maroon",
  FLAG: "border-gov-saffron/50 bg-gov-saffron-soft text-gov-ink",
  INFO: "border-gov-navy/30 bg-gov-navy-soft text-gov-navy",
};

function titleFor(type: string): { headline: string; icon: React.ComponentType<{ className?: string }> } {
  switch (type) {
    case "technical_vs_compliance":
      return { headline: "Conflict between Technical and Compliance evaluations", icon: AlertTriangle };
    case "cartel_suspicion":
      return { headline: "Cartel suspicion — clustered bid amounts", icon: Users2 };
    case "duplicate_bidders":
      return { headline: "Possible duplicate submission — identical bid content", icon: Copy };
    case "abnormally_low_bid":
      return { headline: "Abnormally low bid (>20% below estimate)", icon: AlertTriangle };
    default:
      return { headline: type.replace(/_/g, " "), icon: AlertTriangle };
  }
}

/** Institutional alert banner. Dark-saffron border on a saffron-soft background, with
 *  side-by-side conflicting claims when expanded. */
export function DisagreementBanner({
  d,
  onJump,
}: {
  d: Disagreement;
  onJump?: (bidId: string | undefined, sourceDoc: string, page: number, quote: string) => void;
}) {
  const [open, setOpen] = useState(true);
  const { headline, icon: Icon } = titleFor(d.type);
  const isCartel = d.type === "cartel_suspicion";
  const isDuplicate = d.type === "duplicate_bidders";

  return (
    <div className="rounded-sm border-l-4 border-l-gov-saffron border border-gov-saffron/40 bg-gov-saffron-soft">
      <button
        onClick={() => setOpen((x) => !x)}
        className="flex w-full items-center justify-between gap-4 px-5 py-3 text-left"
      >
        <div className="flex items-center gap-3">
          <Icon className="size-5 text-gov-saffron" />
          <div>
            <div className="font-sans text-[14.5px] font-semibold leading-tight text-gov-ink">
              {headline}{" "}
              {d.org_name && !isCartel && !isDuplicate && (
                <span className="text-gov-ink-muted">— {d.org_name}</span>
              )}
            </div>
            {d.note && (
              <div className="mt-0.5 line-clamp-2 text-[12.5px] text-gov-ink-muted">{d.note}</div>
            )}
          </div>
        </div>
        <ChevronDown className={cn("size-4 text-gov-ink-muted transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="border-t border-gov-saffron/40 px-5 py-4">
          {isCartel || isDuplicate ? (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              {d.bids?.map((b) => (
                <div key={b.bid_id} className="rounded-sm border border-gov-saffron/30 bg-white p-3">
                  <div className="font-sans text-[13px] font-semibold text-gov-ink">{b.org_name}</div>
                  {b.quoted_amount != null && (
                    <div className="mt-1 font-mono text-[12px] tabular-nums text-gov-ink-muted">
                      ₹ {new Intl.NumberFormat("en-IN").format(b.quoted_amount)}
                    </div>
                  )}
                </div>
              ))}
              {isCartel && d.spread_pct != null && (
                <p className="md:col-span-3 mt-1 text-[12.5px] text-gov-ink-muted">
                  Price spread {d.spread_pct}% (CVC threshold ≤ {d.threshold_pct ?? 2}%, Circular 4/3/07).
                </p>
              )}
              {isDuplicate && (
                <p className="md:col-span-3 mt-1 text-[12.5px] text-gov-ink-muted">
                  The bid documents above were found to be substantially identical after the bidder names
                  were normalised — a common pattern in shell / proxy bidding. Investigate before any award.
                </p>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {(d.conflicting_claims ?? []).map((c, i) => (
                <div key={i} className="rounded-sm border border-gov-saffron/30 bg-white p-3">
                  <div className="flex items-center justify-between">
                    <span className={cn(
                      "inline-flex items-center rounded-sm border px-2 py-0.5 font-sans text-[10.5px] font-semibold uppercase tracking-wide",
                      VERDICT_CLS[c.verdict],
                    )}>
                      {c.verdict}
                    </span>
                    <span className="font-mono text-[10px] uppercase tracking-wide text-gov-ink-muted">
                      {c.agent.replace(/_agent$/, "")}
                    </span>
                  </div>
                  <p className="mt-2 text-[13px] leading-snug text-gov-ink">{c.claim}</p>
                  <button
                    onClick={() => onJump?.(d.bid_id, c.source_doc, c.page_number, c.quote)}
                    className="mt-2 inline-flex items-center gap-1.5 rounded-sm border border-gov-navy/30 bg-gov-navy-soft px-2 py-1 font-mono text-[11.5px] text-gov-navy hover:border-gov-navy hover:bg-white"
                  >
                    {c.source_doc} <span className="text-gov-ink-faint">·</span> <span className="text-gov-saffron font-semibold">p.{c.page_number}</span>
                  </button>
                  {c.quote && (
                    <p className="mt-2 font-serif italic text-[12.5px] leading-snug text-gov-ink-muted">
                      “{c.quote.length > 220 ? c.quote.slice(0, 220) + "…" : c.quote}”
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
