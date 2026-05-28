import { cn } from "@/lib/utils";

/** Evaluation-method chip (L1 / QCBS / LCS). */
export function EvalPill({ method }: { method?: string | null }) {
  const m = (method ?? "unknown").toUpperCase();
  const known = m === "L1" || m === "QCBS" || m === "LCS";
  return (
    <span
      className={cn(
        "inline-flex rounded-sm border px-2 py-0.5 font-mono text-[11px] uppercase tracking-wide",
        known ? "border-gold/40 bg-gold-faint text-gold" : "border-smoke text-cream-faint",
      )}
    >
      {m}
    </span>
  );
}
