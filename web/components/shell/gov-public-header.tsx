import Link from "next/link";

import { GovEmblem } from "./gov-emblem";

/** Public-facing header for the landing page — same identity language as the
 *  officer workspace header but without the signed-in identity block. Adds
 *  Sign in / Create account CTAs. */
export function GovPublicHeader() {
  return (
    <header className="sticky top-0 z-40 bg-gov-surface/90 backdrop-blur">
      {/* Tricolor strip */}
      <div aria-hidden className="flex h-[5px]">
        <div className="flex-1 bg-gov-saffron" />
        <div className="flex-1 bg-white" />
        <div className="flex-1 bg-gov-green" />
      </div>
      <div className="border-b border-gov-border">
        <div className="mx-auto flex max-w-content items-center gap-5 px-6 py-4">
          <Link href="/" className="flex items-center gap-3 min-w-0">
            <GovEmblem className="size-10 shrink-0" />
            <div className="min-w-0">
              <p className="font-sans text-[16px] font-semibold leading-tight tracking-tight text-gov-ink">
                TenderIQ <span className="text-gov-ink-muted">·</span>{" "}
                <span className="text-gov-navy">Procurement Evaluation Portal</span>
              </p>
              <p className="mt-0.5 text-[11.5px] text-gov-ink-muted">
                Central Public Procurement Cell · Government of India
              </p>
            </div>
          </Link>
          <nav className="ml-auto flex items-center gap-2">
            <Link
              href="/login"
              className="rounded-md border border-gov-border bg-white px-4 py-1.5 font-sans text-[13px] font-semibold text-gov-ink hover:border-gov-navy hover:text-gov-navy"
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className="rounded-md bg-gov-navy px-4 py-1.5 font-sans text-[13px] font-semibold text-white shadow-gov-sm hover:bg-gov-navy-hover hover:shadow-gov-md"
            >
              Create an account
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
