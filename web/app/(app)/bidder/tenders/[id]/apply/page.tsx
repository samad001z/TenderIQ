"use client";

import { AlertTriangle, ShieldCheck } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { BidDropzone } from "@/components/bidder/bid-dropzone";
import { Button } from "@/components/ui/button";
import { CitationPill } from "@/components/ui/citation-pill";
import { StatusDot } from "@/components/ui/status-dot";
import { VerdictPill } from "@/components/ui/verdict-pill";
import {
  complianceCheckStream,
  eligibilityCheckStream,
  ensureBid,
  getAccessToken,
  submitBid,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Verdict } from "@shared/citation";

type Elig = { criterion: string; verdict: Verdict; reason: string; tender_page: number; quote: string };
type Finding = {
  claim: string;
  verdict: Verdict;
  category: string;
  source_doc: string;
  page_number: number;
  quote: string;
  severity: string;
};

function Section({ letter, title, children }: { letter: string; title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-smoke bg-carbon-surface p-5">
      <div className="mb-4 flex items-center gap-3">
        <span className="flex size-6 items-center justify-center rounded-sm bg-gold-faint font-mono text-[12px] font-semibold text-gold">
          {letter}
        </span>
        <h2 className="font-sans text-[15px] font-semibold text-cream">{title}</h2>
      </div>
      {children}
    </section>
  );
}

export default function ApplyPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const tenderId = params.id;

  const [bidId, setBidId] = useState<string | null>(null);
  const [setupError, setSetupError] = useState<string | null>(null);

  // Section A
  const [elig, setElig] = useState<Elig[]>([]);
  const [eligPhase, setEligPhase] = useState<"idle" | "running" | "done" | "error">("idle");
  const [eligMsg, setEligMsg] = useState("");
  const [acknowledged, setAcknowledged] = useState(false);

  // Section B
  const [technical, setTechnical] = useState<string | null>(null);
  const [financial, setFinancial] = useState<string | null>(null);

  // Section C
  const [findings, setFindings] = useState<Finding[]>([]);
  const [compPhase, setCompPhase] = useState<"idle" | "running" | "done" | "error">("idle");
  const [compMsg, setCompMsg] = useState("");

  const [submitting, setSubmitting] = useState(false);

  // Ensure a bid, then auto-run the eligibility pre-check.
  useEffect(() => {
    (async () => {
      const token = await getAccessToken();
      if (!token) return setSetupError("Your session expired — sign in again.");
      try {
        const { bid_id } = await ensureBid(tenderId, token);
        setBidId(bid_id);
        setEligPhase("running");
        await eligibilityCheckStream(bid_id, token, (event, data) => {
          if (event === "progress") setEligMsg(String(data.message));
          else if (event === "result") setElig((r) => [...r, data as unknown as Elig]);
          else if (event === "done") setEligPhase("done");
          else if (event === "error") {
            setEligMsg(String(data.message));
            setEligPhase("error");
          }
        });
      } catch (e) {
        setSetupError(e instanceof Error ? e.message : "Could not start the application.");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const eligFails = elig.filter((e) => e.verdict === "FAIL").length;
  const bothUploaded = Boolean(technical && financial);

  async function runCompliance() {
    if (!bidId) return;
    const token = await getAccessToken();
    if (!token) return;
    setFindings([]);
    setCompPhase("running");
    await complianceCheckStream(bidId, token, (event, data) => {
      if (event === "progress") setCompMsg(String(data.message));
      else if (event === "result") setFindings((f) => [...f, data as unknown as Finding]);
      else if (event === "done") setCompPhase("done");
      else if (event === "error") {
        setCompMsg(String(data.message));
        setCompPhase("error");
      }
    });
  }

  async function onSubmit() {
    if (!bidId) return;
    setSubmitting(true);
    const token = await getAccessToken();
    if (!token) return setSubmitting(false);
    try {
      await submitBid(bidId, token);
      router.push("/bidder/submissions");
    } catch {
      setSubmitting(false);
    }
  }

  if (setupError) {
    return <p className="text-[13px] text-verdict-fail">{setupError}</p>;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div>
        <h1 className="font-serif text-[30px] font-medium leading-tight text-cream">Apply to tender</h1>
        <p className="mt-1 text-[14px] text-cream-muted">
          TenderIQ pre-checks your eligibility and your documents before you submit.
        </p>
      </div>

      {/* A — Eligibility pre-check */}
      <Section letter="A" title="Eligibility pre-check">
        {eligPhase === "running" && elig.length === 0 && (
          <div className="flex items-center gap-3 text-[13px] text-cream-muted">
            <StatusDot status="running" /> {eligMsg || "Checking…"}
          </div>
        )}
        <div className="space-y-2">
          {elig.map((e, i) => (
            <div key={i} className="flex items-start justify-between gap-3 rounded-sm border border-smoke bg-carbon-elevated px-3 py-2">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <VerdictPill verdict={e.verdict} />
                  <span className="text-[13px] font-medium text-cream">{e.criterion}</span>
                </div>
                <p className="mt-1 text-[12px] leading-snug text-cream-muted">{e.reason}</p>
              </div>
              <CitationPill doc="tender.pdf" page={e.tender_page} />
            </div>
          ))}
        </div>
        {eligPhase === "error" && <p className="mt-2 text-[12px] text-verdict-fail">{eligMsg}</p>}
        {eligPhase === "done" && eligFails > 0 && !acknowledged && (
          <div className="mt-4 flex items-center justify-between gap-3 rounded-sm border border-verdict-flag/40 bg-verdict-flag/10 px-4 py-3">
            <span className="flex items-center gap-2 text-[13px] text-verdict-flag">
              <AlertTriangle className="size-4" />
              {eligFails} criteria failed. You can still apply, but your bid will be flagged.
            </span>
            <Button variant="secondary" size="sm" onClick={() => setAcknowledged(true)}>
              Continue anyway
            </Button>
          </div>
        )}
        {eligPhase === "done" && eligFails === 0 && (
          <p className="mt-3 flex items-center gap-2 text-[12px] text-verdict-pass">
            <ShieldCheck className="size-4" /> You meet all auto-checkable criteria.
          </p>
        )}
      </Section>

      {/* B — Upload */}
      <Section letter="B" title="Upload your bid documents">
        <div className="grid gap-4 sm:grid-cols-2">
          {bidId && (
            <>
              <BidDropzone bidId={bidId} docType="technical" label="Technical bid" onUploaded={setTechnical} />
              <BidDropzone bidId={bidId} docType="financial" label="Financial bid" onUploaded={setFinancial} />
            </>
          )}
        </div>
      </Section>

      {/* C — Compliance check */}
      <Section letter="C" title="Pre-submission compliance check">
        <p className="mb-3 text-[13px] text-cream-muted">
          We scan your <span className="text-cream">technical bid</span> for missing OEM authorisations,
          certificates and declarations — with the exact page in your own file.
        </p>
        <Button variant="secondary" size="sm" onClick={runCompliance} disabled={!technical || compPhase === "running"}>
          {compPhase === "running" ? "Reviewing…" : findings.length ? "Re-run check" : "Run compliance check"}
        </Button>
        {!technical && (
          <p className="mt-2 font-mono text-[11px] text-cream-faint">Upload your technical bid first.</p>
        )}
        {compPhase === "running" && (
          <div className="mt-3 flex items-center gap-3 text-[13px] text-cream-muted">
            <StatusDot status="running" /> {compMsg || "Reviewing…"}
          </div>
        )}
        <div className="mt-3 space-y-2">
          {findings.map((f, i) => (
            <div key={i} className="flex items-start justify-between gap-3 rounded-sm border border-smoke bg-carbon-elevated px-3 py-2">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <VerdictPill verdict={f.verdict} />
                  <span className="font-mono text-[10px] uppercase tracking-wide text-cream-faint">{f.category}</span>
                </div>
                <p className="mt-1 text-[13px] leading-snug text-cream">{f.claim}</p>
              </div>
              {f.page_number > 0 ? (
                <CitationPill doc={f.source_doc} page={f.page_number} />
              ) : (
                <span className="shrink-0 rounded-sm border border-verdict-fail/40 bg-verdict-fail/10 px-2 py-0.5 font-mono text-[11px] text-verdict-fail">
                  missing
                </span>
              )}
            </div>
          ))}
        </div>
        {compPhase === "error" && <p className="mt-2 text-[12px] text-verdict-fail">{compMsg}</p>}
      </Section>

      {/* Submit */}
      <div className="flex items-center justify-between rounded-lg border border-smoke bg-carbon-surface px-5 py-4">
        <span className="text-[12px] text-cream-muted">
          {bothUploaded ? "Both documents uploaded." : "Upload both the technical and financial bid to submit."}
        </span>
        <Button onClick={onSubmit} disabled={!bothUploaded || submitting}>
          {submitting ? "Submitting…" : "Submit bid"}
        </Button>
      </div>
    </div>
  );
}
