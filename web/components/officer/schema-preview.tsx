"use client";

import { FileSearch } from "lucide-react";

import { cn } from "@/lib/utils";
import type { TenderSchema } from "@/lib/tender-schema";

const inr = (n: number | null | undefined) =>
  n == null ? "—" : `₹ ${new Intl.NumberFormat("en-IN").format(n)}`;

/** Clickable source-page chip — jumps the PDF to its page. */
function Src({ page, onJump }: { page: number; onJump: (p: number) => void }) {
  if (!page) return <span className="font-mono text-[11px] text-gov-ink-faint">no source</span>;
  return (
    <button
      onClick={() => onJump(page)}
      title="Jump to source page"
      className="inline-flex items-center gap-1 rounded-sm border border-gov-border bg-gov-bg px-2 py-0.5 font-mono text-[11px] text-gov-saffron font-semibold transition-colors hover:border-gov-navy hover:bg-gov-navy-soft hover:text-gov-navy"
    >
      <FileSearch className="size-3" />
      p.{page}
    </button>
  );
}

function Field({
  label,
  value,
  page,
  onJump,
}: {
  label: string;
  value: React.ReactNode;
  page: number;
  onJump: (p: number) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-gov-border py-3">
      <div className="min-w-0">
        <p className="font-mono text-[10px] uppercase tracking-wide text-gov-ink-faint">{label}</p>
        <p className="mt-1 text-[13px] leading-snug text-gov-ink">{value}</p>
      </div>
      <Src page={page} onJump={onJump} />
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="mt-6 font-sans text-[11px] font-semibold uppercase tracking-wide text-gov-ink-muted first:mt-0">
      {children}
    </h3>
  );
}

export function SchemaPreview({
  schema,
  onJump,
}: {
  schema: TenderSchema;
  onJump: (page: number) => void;
}) {
  const s = schema;
  return (
    <div className="px-4">
      <SectionTitle>Overview</SectionTitle>
      <Field label="Title" value={s.title.value || "—"} page={s.title.source_page} onJump={onJump} />
      <Field label="Reference no." value={<span className="font-mono">{s.reference_no.value || "—"}</span>} page={s.reference_no.source_page} onJump={onJump} />
      <Field label="Ministry" value={s.ministry.value || "—"} page={s.ministry.source_page} onJump={onJump} />
      <Field label="Department" value={s.department.value || "—"} page={s.department.source_page} onJump={onJump} />
      <Field label="Estimated value" value={<span className="font-mono tabular-nums">{inr(s.value_estimate.value)}</span>} page={s.value_estimate.source_page} onJump={onJump} />
      <Field label="Submission deadline" value={s.submission_deadline.value || "—"} page={s.submission_deadline.source_page} onJump={onJump} />

      <SectionTitle>Evaluation</SectionTitle>
      <Field
        label="Method"
        value={
          <span className="inline-flex items-center gap-2">
            <span className="rounded-sm border border-gov-navy/30 bg-gov-navy-soft px-2 py-0.5 font-mono text-[11px] font-semibold text-gov-navy">
              {s.evaluation_method}
            </span>
            {s.evaluation_method === "QCBS" && (
              <span className="font-mono text-[12px] tabular-nums text-gov-ink-muted">
                {s.qcbs_weights.technical}% tech · {s.qcbs_weights.financial}% cost
              </span>
            )}
          </span>
        }
        page={s.evaluation_method_source_page}
        onJump={onJump}
      />

      <SectionTitle>Eligibility criteria · {s.eligibility_criteria.length}</SectionTitle>
      {s.eligibility_criteria.map((c, i) => (
        <Field key={i} label={`Criterion ${i + 1}`} value={c.description} page={c.source_page} onJump={onJump} />
      ))}

      <SectionTitle>Technical criteria · {s.technical_criteria.length}</SectionTitle>
      {s.technical_criteria.map((c, i) => (
        <Field
          key={i}
          label={c.weight != null ? `${c.weight} marks` : `Criterion ${i + 1}`}
          value={c.description}
          page={c.source_page}
          onJump={onJump}
        />
      ))}

      <SectionTitle>Commercials & compliance</SectionTitle>
      <Field label="Financial format" value={s.financial_format.value || "—"} page={s.financial_format.source_page} onJump={onJump} />
      <Field label="EMD" value={<span className="font-mono tabular-nums">{inr(s.emd_amount.value)}</span>} page={s.emd_amount.source_page} onJump={onJump} />
      <Field label="Performance guarantee" value={s.pbg_percentage.value != null ? `${s.pbg_percentage.value}%` : "—"} page={s.pbg_percentage.source_page} onJump={onJump} />
      <Field
        label="Integrity pact"
        value={
          <span className={cn("font-semibold", s.integrity_pact_required.value ? "text-gov-saffron" : "text-gov-ink-muted")}>
            {s.integrity_pact_required.value ? "Required" : "Not required"}
          </span>
        }
        page={s.integrity_pact_required.source_page}
        onJump={onJump}
      />
      <Field label="PPP-MII class" value={s.ppp_mii_class === "none" ? "Open (no restriction)" : `Class ${s.ppp_mii_class}`} page={s.ppp_mii_source_page} onJump={onJump} />
    </div>
  );
}
