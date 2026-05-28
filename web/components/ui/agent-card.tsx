import { StatusDot, type AgentStatus } from "@/components/ui/status-dot";
import { cn } from "@/lib/utils";

const LABEL: Record<AgentStatus, string> = {
  idle: "Idle",
  running: "Analyzing…",
  done: "Complete",
  error: "Failed",
};

/** Agent status panel with a pulsing gold dot while running. */
export function AgentCard({
  name,
  role,
  status,
  findings,
  className,
}: {
  name: string;
  role: string;
  status: AgentStatus;
  findings?: number;
  className?: string;
}) {
  return (
    <div className={cn("rounded-lg border border-smoke bg-obsidian-surface p-4", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusDot status={status} />
          <span className="font-sans text-[14px] font-semibold text-cream">{name}</span>
        </div>
        <span className="font-mono text-[11px] uppercase tracking-wide text-cream-muted">
          {LABEL[status]}
        </span>
      </div>
      <p className="mt-2 text-[13px] leading-snug text-cream-muted">{role}</p>
      {typeof findings === "number" && (
        <div className="mt-3 flex items-baseline gap-1 border-t border-smoke pt-3">
          <span className="font-mono text-[18px] tabular-nums text-cream">{findings}</span>
          <span className="text-[12px] text-cream-faint">findings</span>
        </div>
      )}
    </div>
  );
}
