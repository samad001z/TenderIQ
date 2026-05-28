import type { ReactNode } from "react";

// Auth pages render a Supabase browser client in their effects; opt them out
// of Next's static prerender so missing build-time env vars don't break the
// Vercel build. Scoped here (not on the root layout) to keep `next/font/google`
// in the static side of the build — otherwise its `__dirname` usage gets
// pulled into the Edge middleware bundle and crashes at runtime.
export const dynamic = "force-dynamic";

/** Linear-style two-pane auth shell: obsidian brand pane + form pane. */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="grid min-h-screen bg-obsidian lg:grid-cols-2">
      {/* Left — brand pane */}
      <div className="relative hidden flex-col justify-between border-r border-smoke bg-obsidian p-12 lg:flex">
        <div className="flex items-center gap-2">
          <span className="size-2 rounded-full bg-gold" />
          <span className="font-serif text-[28px] font-medium leading-none text-cream">
            TenderIQ
          </span>
        </div>

        <div className="space-y-4">
          <h1 className="font-serif text-[40px] font-medium leading-tight text-cream">
            Every claim, cited to the page.
          </h1>
          <p className="max-w-md text-[14px] leading-relaxed text-cream-muted">
            AI-native bid evaluation for Indian government procurement. Seven agents flag every
            issue with the exact PDF page and verbatim source text — audit-grade by design.
          </p>
        </div>

        <p className="font-mono text-[11px] uppercase tracking-wide text-cream-faint">
          Government Procurement Evaluation Portal · Central Public Procurement Cell
        </p>
      </div>

      {/* Right — form pane */}
      <div className="flex items-center justify-center p-6 lg:bg-obsidian-surface">
        <div className="w-full max-w-sm">{children}</div>
      </div>
    </div>
  );
}
