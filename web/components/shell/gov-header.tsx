import { GovEmblem } from "./gov-emblem";

/** Institutional but modern header. Tricolor strip, slim utility bar, then a
 *  generous identifier row. No serif chrome — we save serif for hero moments. */
export function GovHeader({
  fullName,
  ministry,
}: {
  fullName: string;
  ministry?: string | null;
}) {
  const today = new Date().toLocaleDateString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
  });
  return (
    <header className="bg-gov-surface">
      {/* Tricolor strip */}
      <div aria-hidden className="flex h-[5px]">
        <div className="flex-1 bg-gov-saffron" />
        <div className="flex-1 bg-white" />
        <div className="flex-1 bg-gov-green" />
      </div>

      {/* Utility bar — neutral, low-weight */}
      <div className="bg-gov-bg/70">
        <div className="mx-auto flex h-8 max-w-content items-center justify-between px-6 text-[11.5px] text-gov-ink-muted">
          <div className="flex items-center gap-4">
            <a href="#main" className="hover:text-gov-navy hover:underline">Skip to main content</a>
            <span aria-hidden className="hidden h-3 w-px bg-gov-border md:block" />
            <span className="hidden md:inline">An initiative of the Government of India</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-mono tabular-nums">{today}</span>
            <span aria-hidden className="hidden h-3 w-px bg-gov-border md:block" />
            <span aria-label="Accessibility — font size" className="hidden items-center gap-1 md:flex">
              <button className="rounded-sm px-1.5 leading-none text-gov-ink-muted hover:text-gov-navy">A-</button>
              <button className="rounded-sm px-1.5 font-semibold leading-none text-gov-ink hover:text-gov-navy">A</button>
              <button className="rounded-sm px-1.5 leading-none text-gov-ink-muted hover:text-gov-navy">A+</button>
            </span>
          </div>
        </div>
      </div>

      {/* Identifier — emblem + name + signed-in officer. More breathing room. */}
      <div className="border-b border-gov-border">
        <div className="mx-auto flex max-w-content items-center gap-5 px-6 py-6">
          <GovEmblem className="size-12 shrink-0" />
          <div className="min-w-0">
            <p className="font-sans text-[20px] font-semibold leading-tight tracking-tight text-gov-ink">
              TenderIQ <span className="text-gov-ink-muted">·</span> <span className="text-gov-navy">Government Procurement Evaluation Portal</span>
            </p>
            <p className="mt-0.5 text-[12.5px] text-gov-ink-muted">
              Officer Review Workspace · Central Public Procurement Cell
            </p>
          </div>
          <div className="ml-auto hidden text-right md:block">
            <p className="font-mono text-[10.5px] uppercase tracking-wide text-gov-ink-faint">
              Signed in as
            </p>
            <p className="font-sans text-[13px] font-semibold text-gov-ink">{fullName}</p>
            {ministry && (
              <p className="font-mono text-[10.5px] uppercase tracking-wide text-gov-ink-muted">
                {ministry}
              </p>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
