import { cn } from "@/lib/utils";

export type AgentStatus = "idle" | "running" | "done" | "error";

const DOT: Record<AgentStatus, string> = {
  idle: "bg-cream-faint",
  running: "bg-gold animate-pulse-dot",
  done: "bg-verdict-pass",
  error: "bg-verdict-fail",
};

/** 8px round status indicator. Pulses gold while an agent is running. */
export function StatusDot({ status, className }: { status: AgentStatus; className?: string }) {
  return <span className={cn("inline-block size-2 rounded-full", DOT[status], className)} />;
}
