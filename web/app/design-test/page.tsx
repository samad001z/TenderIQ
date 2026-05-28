import { ArrowRight, Download, Plus } from "lucide-react";

import { AgentCard } from "@/components/ui/agent-card";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CitationPill } from "@/components/ui/citation-pill";
import { Input } from "@/components/ui/input";
import { StatusDot } from "@/components/ui/status-dot";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { VerdictPill } from "@/components/ui/verdict-pill";

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <section className="space-y-4">
      <h2 className="font-sans text-[11px] font-medium uppercase tracking-wide text-cream-muted">
        {label}
      </h2>
      {children}
    </section>
  );
}

const AGENTS = [
  { name: "Eligibility Agent", role: "Verifies bidder meets every mandatory eligibility clause.", status: "done", findings: 2 },
  { name: "Financial Agent", role: "Reconciles quoted amounts, taxes, and EMD against tender terms.", status: "running", findings: undefined },
  { name: "Technical Compliance", role: "Maps technical specs to the BoQ line by line.", status: "running", findings: undefined },
  { name: "Document Integrity", role: "Detects tampering, missing signatures, and stale dates.", status: "idle", findings: undefined },
  { name: "Clause Cross-Reference", role: "Links bid claims to the exact tender clause.", status: "done", findings: 5 },
  { name: "Risk & Anomaly", role: "Flags outlier pricing and collusion signals.", status: "error", findings: undefined },
  { name: "Final Scoring", role: "Aggregates agent verdicts into an auditable score.", status: "idle", findings: undefined },
] as const;

const SWATCHES = [
  { name: "obsidian", cls: "bg-obsidian", hex: "#0B0D0F" },
  { name: "surface", cls: "bg-obsidian-surface", hex: "#14171A" },
  { name: "elevated", cls: "bg-obsidian-elevated", hex: "#1C2024" },
  { name: "smoke", cls: "bg-smoke", hex: "#2A2F35" },
  { name: "cream", cls: "bg-cream", hex: "#F5F1E8" },
  { name: "cream-muted", cls: "bg-cream-muted", hex: "#9BA1A8" },
  { name: "gold", cls: "bg-gold", hex: "#C8A14A" },
  { name: "gold-hover", cls: "bg-gold-hover", hex: "#D9B45E" },
  { name: "pass", cls: "bg-verdict-pass", hex: "#3FB950" },
  { name: "fail", cls: "bg-verdict-fail", hex: "#E5484D" },
  { name: "flag", cls: "bg-verdict-flag", hex: "#E0A23B" },
  { name: "info", cls: "bg-verdict-info", hex: "#5B8DEF" },
];

const SPACING = [
  { t: "space-1", px: 4 },
  { t: "space-2", px: 8 },
  { t: "space-3", px: 12 },
  { t: "space-4", px: 16 },
  { t: "space-5", px: 24 },
  { t: "space-6", px: 32 },
  { t: "space-7", px: 48 },
  { t: "space-8", px: 64 },
  { t: "space-9", px: 96 },
];

export default function DesignTest() {
  return (
    <div className="space-y-9 pb-9">
      {/* Hero — Cormorant Garamond display */}
      <header className="space-y-3 border-b border-smoke pb-8">
        <p className="font-mono text-[11px] uppercase tracking-wide text-gold">Visual baseline · v0.1.0</p>
        <h1 className="font-serif text-[48px] font-medium leading-none text-cream">
          TenderIQ Design System
        </h1>
        <p className="max-w-2xl text-[14px] leading-relaxed text-cream-muted">
          Bloomberg terminal × Linear × Stripe Dashboard. Obsidian, gold, and cream. One of every
          component below — this page is our visual regression baseline.
        </p>
      </header>

      {/* Typography */}
      <Section label="Typography">
        <div className="grid gap-6 md:grid-cols-3">
          <div className="space-y-2">
            <p className="font-mono text-[11px] uppercase tracking-wide text-cream-faint">
              Cormorant Garamond · display
            </p>
            <p className="font-serif text-[32px] leading-tight text-cream">Audit-grade clarity</p>
            <p className="font-serif text-[18px] text-cream-muted">शासकीय निविदा मूल्यांकन</p>
          </div>
          <div className="space-y-2">
            <p className="font-mono text-[11px] uppercase tracking-wide text-cream-faint">
              DM Sans · UI / body
            </p>
            <p className="font-sans text-[16px] font-semibold text-cream">Every claim is cited.</p>
            <p className="font-sans text-[14px] text-cream-muted">
              Page-accurate, verbatim, and re-runnable.
            </p>
          </div>
          <div className="space-y-2">
            <p className="font-mono text-[11px] uppercase tracking-wide text-cream-faint">
              JetBrains Mono · numeric
            </p>
            <p className="font-mono text-[18px] tabular-nums text-cream">₹ 1,24,50,000.00</p>
            <p className="font-mono text-[13px] text-cream-muted">conf 0.94 · p.23</p>
          </div>
        </div>
      </Section>

      {/* Buttons */}
      <Section label="Buttons">
        <div className="flex flex-wrap items-center gap-4">
          <Button>
            <Plus /> Primary
          </Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Reject bid</Button>
          <Button variant="link">
            View source <ArrowRight />
          </Button>
          <Button disabled>Disabled</Button>
          <Button size="sm">Small</Button>
          <Button size="lg">Large</Button>
        </div>
      </Section>

      {/* Input */}
      <Section label="Input">
        <div className="max-w-sm space-y-2">
          <label className="font-sans text-[12px] font-medium text-cream-muted">Tender ID</label>
          <Input placeholder="e.g. GEM/2026/B/4821907" />
        </div>
      </Section>

      {/* Card */}
      <Section label="Card">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Eligibility summary</CardTitle>
            <CardDescription>3 mandatory clauses · 1 flagged</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between text-[13px]">
              <span className="text-cream-muted">Turnover requirement</span>
              <VerdictPill verdict="PASS" />
            </div>
            <div className="flex items-center justify-between text-[13px]">
              <span className="text-cream-muted">PAN / GST validity</span>
              <VerdictPill verdict="FLAG" />
            </div>
          </CardContent>
        </Card>
      </Section>

      {/* Table with mono numeric cell + verdict pills */}
      <Section label="Table · numeric cells + verdicts">
        <Card>
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Bidder</TableHead>
                <TableHead className="text-right">Bid amount (₹)</TableHead>
                <TableHead className="text-right">Compliance</TableHead>
                <TableHead>Verdict</TableHead>
                <TableHead>Source</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-medium">Meridian Infra Pvt Ltd</TableCell>
                <TableCell className="text-right font-mono tabular-nums">1,24,50,000</TableCell>
                <TableCell className="text-right font-mono tabular-nums">92%</TableCell>
                <TableCell><VerdictPill verdict="PASS" /></TableCell>
                <TableCell><CitationPill doc="bid_a.pdf" page={23} /></TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Sahara Constructions</TableCell>
                <TableCell className="text-right font-mono tabular-nums">98,75,000</TableCell>
                <TableCell className="text-right font-mono tabular-nums">61%</TableCell>
                <TableCell><VerdictPill verdict="FAIL" /></TableCell>
                <TableCell><CitationPill doc="bid_b.pdf" page={7} /></TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Orbit Engineering LLP</TableCell>
                <TableCell className="text-right font-mono tabular-nums">1,11,20,000</TableCell>
                <TableCell className="text-right font-mono tabular-nums">78%</TableCell>
                <TableCell><VerdictPill verdict="FLAG" /></TableCell>
                <TableCell><CitationPill doc="bid_c.pdf" page={41} /></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Card>
      </Section>

      {/* Verdict pills */}
      <Section label="Verdict pills">
        <div className="flex flex-wrap items-center gap-3">
          <VerdictPill verdict="PASS" />
          <VerdictPill verdict="FAIL" />
          <VerdictPill verdict="FLAG" />
          <VerdictPill verdict="INFO" />
        </div>
      </Section>

      {/* Citation pills */}
      <Section label="Citation pills">
        <div className="flex flex-wrap items-center gap-3">
          <CitationPill doc="bid_a.pdf" page={23} />
          <CitationPill doc="tender_GEM_4821907.pdf" page={4} />
          <CitationPill doc="emd_receipt.pdf" page={1} />
        </div>
      </Section>

      {/* Status dots */}
      <Section label="Status dots">
        <div className="flex flex-wrap items-center gap-6 text-[12px] text-cream-muted">
          <span className="flex items-center gap-2"><StatusDot status="idle" /> idle</span>
          <span className="flex items-center gap-2"><StatusDot status="running" /> running (pulses gold)</span>
          <span className="flex items-center gap-2"><StatusDot status="done" /> done</span>
          <span className="flex items-center gap-2"><StatusDot status="error" /> error</span>
        </div>
      </Section>

      {/* Agent cards — the 7 agents */}
      <Section label="Agent cards · the 7 agents">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {AGENTS.map((a) => (
            <AgentCard
              key={a.name}
              name={a.name}
              role={a.role}
              status={a.status}
              findings={a.findings}
            />
          ))}
        </div>
      </Section>

      {/* Color tokens */}
      <Section label="Color tokens">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
          {SWATCHES.map((s) => (
            <div key={s.name} className="overflow-hidden rounded-lg border border-smoke">
              <div className={`h-12 ${s.cls}`} />
              <div className="space-y-0.5 bg-obsidian-surface px-3 py-2">
                <p className="font-sans text-[12px] text-cream">{s.name}</p>
                <p className="font-mono text-[11px] text-cream-faint">{s.hex}</p>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* Spacing scale */}
      <Section label="Spacing scale · 4 → 96 only">
        <div className="space-y-2">
          {SPACING.map((s) => (
            <div key={s.t} className="flex items-center gap-4">
              <span className="w-20 font-mono text-[11px] text-cream-faint">{s.t}</span>
              <div className="h-3 rounded-sm bg-gold" style={{ width: s.px }} />
              <span className="font-mono text-[11px] tabular-nums text-cream-muted">{s.px}px</span>
            </div>
          ))}
        </div>
      </Section>

      {/* Radius scale */}
      <Section label="Border radius · ≤ 6px on containers">
        <div className="flex flex-wrap items-end gap-6">
          {[
            { t: "sm · 4px", cls: "rounded-sm" },
            { t: "md · 5px", cls: "rounded-md" },
            { t: "lg · 6px", cls: "rounded-lg" },
            { t: "full · dots only", cls: "rounded-full" },
          ].map((r) => (
            <div key={r.t} className="space-y-2 text-center">
              <div className={`size-16 border border-smoke bg-obsidian-elevated ${r.cls}`} />
              <p className="font-mono text-[11px] text-cream-faint">{r.t}</p>
            </div>
          ))}
        </div>
      </Section>

      <footer className="flex items-center gap-3 border-t border-smoke pt-6">
        <Button variant="secondary">
          <Download /> Export baseline
        </Button>
        <span className="font-mono text-[11px] text-cream-faint">
          Tokens from docs/DESIGN_SYSTEM.md
        </span>
      </footer>
    </div>
  );
}
