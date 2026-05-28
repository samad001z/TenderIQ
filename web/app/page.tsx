import Link from "next/link";
import { redirect } from "next/navigation";
import {
  ArrowRight,
  BadgeCheck,
  Brain,
  Copy,
  FileCheck2,
  FileSearch,
  Layers,
  Quote,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";

import { GovFooter } from "@/components/shell/gov-footer";
import { GovPublicHeader } from "@/components/shell/gov-public-header";
import { homePathForRole } from "@/lib/auth";
import { createClient } from "@/lib/supabase/server";

/** Public landing for tenderiq.gov.in.
 *
 *  Signed-in users still flow to their role home (or /onboarding). Visitors see
 *  the marketing landing — hero, capabilities, how-it-works, integrity callouts,
 *  CTA. The visual language matches the officer workspace (gov-light, tricolor,
 *  navy + saffron accents) so a visitor lands on the same portal they'll work in.
 */
// Hits cookies/auth on every request — must run dynamically. Scoped here
// so the root layout stays static-eligible (otherwise next/font/google's
// __dirname usage leaks into the Edge middleware bundle).
export const dynamic = "force-dynamic";

export default async function Root() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (user) {
    const { data: profile } = await supabase
      .from("profiles")
      .select("role, onboarding_complete")
      .eq("id", user.id)
      .single();
    if (!profile?.onboarding_complete) redirect("/onboarding");
    redirect(homePathForRole(profile.role));
  }

  return (
    <div className="min-h-screen bg-gov-bg text-gov-ink">
      <GovPublicHeader />
      <main>
        <Hero />
        <Capabilities />
        <HowItWorks />
        <IntegritySection />
        <CallToAction />
      </main>
      <GovFooter />
    </div>
  );
}

/* ----------------------------------------------------------------- Hero */
function Hero() {
  return (
    <section className="border-b border-gov-border bg-gradient-to-b from-white to-gov-bg">
      <div className="mx-auto grid max-w-content items-center gap-10 px-6 py-20 md:grid-cols-[1.2fr_1fr]">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full border border-gov-saffron/40 bg-gov-saffron-soft px-3 py-1 font-mono text-[11px] font-semibold uppercase tracking-wide text-gov-ink">
            <Sparkles className="size-3.5 text-gov-saffron" />
            AI-assisted procurement
          </span>
          <h1 className="mt-5 font-serif text-[clamp(36px,5vw,56px)] font-semibold leading-[1.05] tracking-tight text-gov-ink">
            Audit-grade bid evaluation <span className="text-gov-navy">for the Government of India</span>.
          </h1>
          <p className="mt-5 max-w-xl text-[16px] leading-relaxed text-gov-ink-muted">
            Seven specialist agents review every submitted bid against your tender's
            eligibility, technical, compliance, financial and integrity requirements.
            Every recommendation is grounded in a <strong className="font-semibold text-gov-ink">page-cited verbatim quote</strong>{" "}
            from the bidder's own documents — defensible before the auditor and the CAG.
          </p>
          <div className="mt-7 flex flex-wrap items-center gap-3">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-md bg-gov-navy px-5 py-3 font-sans text-[14px] font-semibold text-white shadow-gov-sm hover:bg-gov-navy-hover hover:shadow-gov-md"
            >
              Sign in to your workspace
              <ArrowRight className="size-4" />
            </Link>
            <Link
              href="/signup"
              className="inline-flex items-center gap-2 rounded-md border border-gov-border bg-white px-5 py-3 font-sans text-[14px] font-semibold text-gov-ink hover:border-gov-navy hover:text-gov-navy"
            >
              Create an account
            </Link>
          </div>
          <p className="mt-6 flex flex-wrap items-center gap-x-4 gap-y-2 text-[12px] text-gov-ink-muted">
            <span className="inline-flex items-center gap-1.5"><BadgeCheck className="size-3.5 text-gov-green" /> GFR 2017 aligned</span>
            <span className="inline-flex items-center gap-1.5"><BadgeCheck className="size-3.5 text-gov-green" /> CVC Integrity Pact</span>
            <span className="inline-flex items-center gap-1.5"><BadgeCheck className="size-3.5 text-gov-green" /> PPP-MII Class-I aware</span>
            <span className="inline-flex items-center gap-1.5"><BadgeCheck className="size-3.5 text-gov-green" /> CAG-style audit trail</span>
          </p>
        </div>

        {/* Decorative ranking preview card */}
        <div className="relative">
          <div aria-hidden className="absolute -inset-4 -z-10 rounded-2xl bg-gradient-to-br from-gov-saffron-soft via-transparent to-gov-navy-soft blur-2xl" />
          <div className="overflow-hidden rounded-lg border border-gov-border bg-gov-surface shadow-gov-lg">
            <div className="border-b border-gov-border bg-gov-bg px-5 py-3">
              <p className="font-mono text-[10.5px] font-semibold uppercase tracking-wide text-gov-ink-muted">
                Recommendation — QCBS evaluation
              </p>
              <p className="mt-1 font-sans text-[16px] font-semibold leading-tight text-gov-ink">
                Recommended for award: <span className="text-gov-navy">StellarTech Pvt Ltd</span>
              </p>
            </div>
            <ul className="divide-y divide-gov-border">
              <RankingDemoRow rank="L1" action="AWARD" actionCls="bg-gov-green-soft text-gov-green border-gov-green/40" name="StellarTech Pvt Ltd" price="₹ 7,22,50,000" />
              <RankingDemoRow rank="—" action="REVIEW" actionCls="bg-gov-saffron-soft text-gov-ink border-gov-saffron/40" name="Velocity Systems" price="₹ 6,80,00,000" note="Tech PASS ⇄ Compliance FAIL" />
              <RankingDemoRow rank="—" action="REJECT" actionCls="bg-gov-maroon-soft text-gov-maroon border-gov-maroon/40" name="BudgetBuild Co" price="₹ 4,42,00,000" note="Abnormally low · duplicate flag" />
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}

function RankingDemoRow({
  rank, action, actionCls, name, price, note,
}: {
  rank: string; action: string; actionCls: string;
  name: string; price: string; note?: string;
}) {
  return (
    <li className="flex items-center gap-4 px-5 py-3.5">
      <span className="w-7 font-mono text-[12px] font-semibold tabular-nums text-gov-ink-muted">{rank}</span>
      <div className="min-w-0 flex-1">
        <p className="font-sans text-[13.5px] font-semibold text-gov-ink truncate">{name}</p>
        {note && <p className="mt-0.5 text-[11.5px] text-gov-ink-muted">{note}</p>}
      </div>
      <span className={`rounded-full border px-2 py-0.5 font-sans text-[10.5px] font-semibold uppercase tracking-wide ${actionCls}`}>
        {action}
      </span>
      <span className="w-28 text-right font-mono text-[12.5px] tabular-nums text-gov-ink">{price}</span>
    </li>
  );
}

/* ----------------------------------------------------------------- Capabilities */
const CAPABILITIES = [
  {
    icon: Quote,
    title: "Citation contract",
    body: "Every AI-emitted claim carries the source document, the exact page number, and a verbatim quote — non-negotiable. Claims missing a page or quote are rejected and re-run automatically.",
    tag: "Audit grade",
  },
  {
    icon: Workflow,
    title: "Seven specialist agents",
    body: "Eligibility, Technical, Compliance, Financial, Risk and Reasoning agents — plus the ingestion + tender-parser steps. They run in parallel for every submitted bid.",
    tag: "Parallel pipeline",
  },
  {
    icon: ShieldAlert,
    title: "Disagreement detection",
    body: "When the Technical agent says PASS but Compliance says FAIL, the orchestrator refuses to recommend the bid and surfaces the conflicting claims for an officer's call.",
    tag: "Human review",
  },
  {
    icon: Copy,
    title: "Duplicate-bidder check",
    body: "Catches \"same documents, different name\" shell submissions by comparing the substantive content of every bid after normalising bidder identities.",
    tag: "Integrity",
  },
  {
    icon: ShieldCheck,
    title: "CVC-aware integrity rules",
    body: "Cartel suspicion when three or more bids cluster within 2% (Circular 4/3/07), abnormally-low flag at >20% below the estimate, and blacklist screening against the debarred-firms registry.",
    tag: "GFR / CVC",
  },
  {
    icon: FileCheck2,
    title: "CAG-style audit report",
    body: "One-click PDF with the executive summary, ranked recommendation, disagreement callouts, every claim with its citation, and an officer sign-off block.",
    tag: "Downloadable",
  },
];

function Capabilities() {
  return (
    <section className="border-b border-gov-border bg-gov-surface">
      <div className="mx-auto max-w-content px-6 py-20">
        <div className="mx-auto max-w-3xl text-center">
          <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-gov-saffron">
            Capabilities
          </p>
          <h2 className="mt-2 font-serif text-[36px] font-semibold leading-tight tracking-tight text-gov-ink">
            Everything an evaluation committee needs, with the evidence baked in.
          </h2>
          <p className="mt-3 text-[15px] leading-relaxed text-gov-ink-muted">
            Built for the way Indian government procurement actually runs — GFR rules,
            CVC integrity pact, PPP-MII Class-I checks, and the audit trail an officer
            needs to defend a recommendation.
          </p>
        </div>

        <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {CAPABILITIES.map((c) => (
            <CapabilityCard key={c.title} {...c} />
          ))}
        </div>
      </div>
    </section>
  );
}

function CapabilityCard({
  icon: Icon, title, body, tag,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string; body: string; tag: string;
}) {
  return (
    <article className="group flex flex-col rounded-lg border border-gov-border bg-gov-surface p-6 shadow-gov-sm transition-shadow hover:shadow-gov-md">
      <div className="flex items-center justify-between">
        <span className="grid size-10 place-items-center rounded-md bg-gov-navy-soft text-gov-navy">
          <Icon className="size-5" />
        </span>
        <span className="rounded-full border border-gov-border bg-gov-bg px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide text-gov-ink-muted">
          {tag}
        </span>
      </div>
      <h3 className="mt-4 font-sans text-[16px] font-semibold leading-tight text-gov-ink">
        {title}
      </h3>
      <p className="mt-2 text-[13.5px] leading-relaxed text-gov-ink-muted">{body}</p>
    </article>
  );
}

/* ----------------------------------------------------------------- How it works */
function HowItWorks() {
  const steps = [
    {
      n: "01",
      icon: FileSearch,
      title: "Upload your tender",
      body: "Drop the tender PDF — the parser extracts a structured schema (eligibility, technical, financial format, evaluation method) with every field carrying its source page.",
    },
    {
      n: "02",
      icon: Layers,
      title: "Bidders submit",
      body: "Registered bidders apply online, with an in-flight eligibility pre-check that catches gaps before submission. Their documents land in your workspace, page-indexed.",
    },
    {
      n: "03",
      icon: Brain,
      title: "Run AI Review",
      body: "Seven agents evaluate every submitted bid in parallel. You see a live dashboard, then a comparison matrix where each cell opens its evidence — and a CAG-style audit PDF.",
    },
  ];
  return (
    <section className="border-b border-gov-border">
      <div className="mx-auto max-w-content px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-gov-saffron">
            How it works
          </p>
          <h2 className="mt-2 font-serif text-[32px] font-semibold leading-tight tracking-tight text-gov-ink">
            From tender to award, with a complete audit trail.
          </h2>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {steps.map((s) => (
            <div key={s.n} className="relative flex flex-col rounded-lg border border-gov-border bg-gov-surface p-6 shadow-gov-sm">
              <span className="font-mono text-[34px] font-semibold leading-none text-gov-navy-soft">
                {s.n}
              </span>
              <s.icon className="mt-3 size-6 text-gov-navy" />
              <h3 className="mt-4 font-sans text-[16px] font-semibold leading-tight text-gov-ink">
                {s.title}
              </h3>
              <p className="mt-2 text-[13.5px] leading-relaxed text-gov-ink-muted">{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ----------------------------------------------------------------- Integrity */
function IntegritySection() {
  return (
    <section className="border-b border-gov-border bg-gov-surface">
      <div className="mx-auto grid max-w-content items-center gap-12 px-6 py-20 md:grid-cols-2">
        <div>
          <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-gov-saffron">
            Integrity by design
          </p>
          <h2 className="mt-2 font-serif text-[32px] font-semibold leading-tight tracking-tight text-gov-ink">
            Built for officers who have to defend the decision.
          </h2>
          <p className="mt-4 text-[15px] leading-relaxed text-gov-ink-muted">
            Three protections, baked in. The portal will not auto-recommend a bid if any
            of these fire — it routes the case to a human officer with the evidence in hand.
          </p>
          <ul className="mt-6 space-y-4">
            <IntegrityRow
              icon={ShieldAlert}
              title="Disagreement between agents"
              body="If the Technical agent passes a bid that the Compliance agent fails, the system refuses to recommend it."
            />
            <IntegrityRow
              icon={Copy}
              title="Duplicate / proxy submissions"
              body="If two bidders submit substantially identical documents, both are flagged — even when only the name is different."
            />
            <IntegrityRow
              icon={ShieldCheck}
              title="Cartel & abnormally-low bids"
              body="Three bids within 2% of each other (CVC Circular 4/3/07), or >20% below the estimate, are routed to human review."
            />
          </ul>
        </div>
        <div className="rounded-lg border border-gov-border bg-gov-bg p-6">
          <p className="font-mono text-[10.5px] font-semibold uppercase tracking-wide text-gov-ink-muted">
            From the audit trail
          </p>
          <blockquote className="mt-3 border-l-2 border-gov-saffron pl-4">
            <p className="font-serif text-[18px] italic leading-snug text-gov-ink">
              "OEM / Manufacturer's Authorisation Form: NOT ENCLOSED with this bid."
            </p>
            <footer className="mt-2 font-mono text-[11px] uppercase tracking-wide text-gov-ink-muted">
              velocity_technical.pdf · p.13 · compliance_agent · FAIL
            </footer>
          </blockquote>
          <p className="mt-6 text-[13px] leading-relaxed text-gov-ink-muted">
            That single quote — copied verbatim from the bidder's own submission, cited
            to its exact page — is what makes the recommendation defensible. Every claim
            in TenderIQ carries one.
          </p>
        </div>
      </div>
    </section>
  );
}

function IntegrityRow({
  icon: Icon, title, body,
}: { icon: React.ComponentType<{ className?: string }>; title: string; body: string }) {
  return (
    <li className="flex items-start gap-3">
      <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-md bg-gov-saffron-soft text-gov-saffron">
        <Icon className="size-4" />
      </span>
      <div>
        <p className="font-sans text-[14px] font-semibold text-gov-ink">{title}</p>
        <p className="mt-1 text-[13px] leading-relaxed text-gov-ink-muted">{body}</p>
      </div>
    </li>
  );
}

/* ----------------------------------------------------------------- CTA */
function CallToAction() {
  return (
    <section className="bg-gov-navy text-white">
      <div className="mx-auto flex max-w-content flex-wrap items-center justify-between gap-6 px-6 py-12">
        <div>
          <h2 className="font-serif text-[28px] font-semibold leading-tight tracking-tight">
            Ready to evaluate your next tender?
          </h2>
          <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-white/80">
            Sign in to your officer workspace, or create an account as a bidder or evaluator
            to begin. The portal is in operational pilot with the Central Public Procurement Cell.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href="/login"
            className="inline-flex items-center gap-2 rounded-md bg-white px-5 py-3 font-sans text-[14px] font-semibold text-gov-navy shadow-gov-sm hover:bg-gov-bg"
          >
            Sign in
            <ArrowRight className="size-4" />
          </Link>
          <Link
            href="/signup"
            className="inline-flex items-center gap-2 rounded-md border border-white/30 px-5 py-3 font-sans text-[14px] font-semibold text-white hover:bg-white/10"
          >
            Create an account
          </Link>
        </div>
      </div>
    </section>
  );
}
