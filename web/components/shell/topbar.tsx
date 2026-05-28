export function Topbar({ title, subtitle }: { title?: string; subtitle?: string }) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-smoke bg-obsidian px-8">
      <div className="flex flex-col">
        <span className="font-sans text-[14px] font-semibold leading-tight text-cream">
          {title ?? "TenderIQ"}
        </span>
        {subtitle && <span className="text-[12px] text-cream-muted">{subtitle}</span>}
      </div>
      <div className="flex items-center gap-4">
        <span className="font-mono text-[11px] text-cream-faint">asia-south1</span>
        <span className="flex size-7 items-center justify-center rounded-full bg-obsidian-elevated font-mono text-[12px] text-cream-muted">
          S
        </span>
      </div>
    </header>
  );
}
