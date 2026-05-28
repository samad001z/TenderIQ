import { FileText } from "lucide-react";

import { cn } from "@/lib/utils";

/** Audit citation chip: [ filename.pdf · p.NN ] — page number in gold. */
export function CitationPill({
  doc,
  page,
  className,
}: {
  doc: string;
  page: number;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-sm border border-smoke bg-obsidian-elevated px-2 py-1 font-mono text-[12px] leading-none text-cream",
        className,
      )}
    >
      <FileText className="size-3 text-cream-muted" />
      <span>{doc}</span>
      <span className="text-cream-faint">·</span>
      <span className="text-gold">p.{page}</span>
    </span>
  );
}
