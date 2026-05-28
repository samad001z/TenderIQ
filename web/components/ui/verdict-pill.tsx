import { cn } from "@/lib/utils";
import type { Verdict } from "@shared/citation";

const STYLES: Record<Verdict, string> = {
  PASS: "text-verdict-pass border-verdict-pass/40 bg-verdict-pass/10",
  FAIL: "text-verdict-fail border-verdict-fail/40 bg-verdict-fail/10",
  FLAG: "text-verdict-flag border-verdict-flag/40 bg-verdict-flag/10",
  INFO: "text-verdict-info border-verdict-info/40 bg-verdict-info/10",
};

/** PASS / FAIL / FLAG / INFO verdict pill — functional status color, not brand accent. */
export function VerdictPill({ verdict, className }: { verdict: Verdict; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-2 py-1 font-sans text-[11px] font-semibold uppercase leading-none tracking-wide",
        STYLES[verdict],
        className,
      )}
    >
      {verdict}
    </span>
  );
}
