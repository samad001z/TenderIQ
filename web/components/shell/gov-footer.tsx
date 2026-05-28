import Link from "next/link";

import { GovEmblem } from "./gov-emblem";

/** Slim modern footer. Two columns + a single bottom row. Government identity
 *  preserved (emblem, copyright, last-reviewed date) but without the dense
 *  institutional clutter of a four-column statutory-reference dump. */
export function GovFooter() {
  const reviewed = new Date().toLocaleDateString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
  });
  return (
    <footer className="mt-16 border-t border-gov-border bg-gov-surface">
      <div className="mx-auto grid max-w-content gap-10 px-6 py-10 md:grid-cols-[2fr_1fr_1fr]">
        <div>
          <div className="flex items-center gap-3">
            <GovEmblem className="size-10" />
            <p className="font-sans text-[15px] font-semibold text-gov-ink">
              TenderIQ · Government Procurement Evaluation Portal
            </p>
          </div>
          <p className="mt-3 max-w-md text-[13px] leading-relaxed text-gov-ink-muted">
            Audit-grade AI bid evaluation for the Government of India. Every
            recommendation is grounded in a page-cited verbatim quote from the
            bidder's own documents — built for officers, auditors, and the CAG.
          </p>
        </div>
        <Section title="Quick Links">
          <FooterLink href="/officer/dashboard">Dashboard</FooterLink>
          <FooterLink href="/officer/tenders">All Tenders</FooterLink>
          <FooterLink href="/officer/tenders/new">Upload a New Tender</FooterLink>
        </Section>
        <Section title="Help &amp; Contact">
          <FooterLink href="#">Documentation</FooterLink>
          <FooterLink href="mailto:cppc@gov.in">cppc@gov.in</FooterLink>
          <FooterLink href="#">Report an issue</FooterLink>
        </Section>
      </div>

      <div className="border-t border-gov-border bg-gov-bg/60">
        <div className="mx-auto flex max-w-content flex-wrap items-center justify-between gap-3 px-6 py-3 text-[11.5px] text-gov-ink-muted">
          <span>
            © {new Date().getFullYear()} Government of India · Central Public Procurement Cell
          </span>
          <div className="flex items-center gap-4">
            <span>Last reviewed: <span className="font-mono tabular-nums">{reviewed}</span></span>
            <a href="#" className="hover:text-gov-navy hover:underline">Disclaimer</a>
            <a href="#" className="hover:text-gov-navy hover:underline">Privacy</a>
            <a href="#" className="hover:text-gov-navy hover:underline">Sitemap</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-3 font-sans text-[11.5px] font-semibold uppercase tracking-wide text-gov-ink">
        {title}
      </h3>
      <ul className="space-y-2 text-[13px] text-gov-ink-muted">{children}</ul>
    </div>
  );
}

function FooterLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <li>
      <Link href={href} className="hover:text-gov-navy hover:underline">
        {children}
      </Link>
    </li>
  );
}
