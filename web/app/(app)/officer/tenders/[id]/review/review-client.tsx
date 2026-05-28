"use client";

import { Download, FileSearch, Play, RotateCcw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AgentTerminal, type TerminalLine } from "@/components/officer/review/agent-terminal";
import { AgentGrid, type AgentCell, type BidHeader } from "@/components/officer/review/agent-grid";
import { CitationDrawer } from "@/components/officer/review/citation-drawer";
import { ComparisonMatrix, type CellSelection } from "@/components/officer/review/comparison-matrix";
import { DisagreementBanner } from "@/components/officer/review/disagreement-banner";
import { PageHighlightModal, type HighlightTarget } from "@/components/officer/review/page-highlight-modal";
import { GovBreadcrumb } from "@/components/shell/gov-nav";
import { fetchReviewSummary, getAccessToken, openAuditPdf, reviewTenderStream } from "@/lib/api";
import {
  AGENT_LABEL,
  type ClaimRow,
  type Disagreement,
  type ReviewSummary,
  type Verdict,
} from "@/lib/review-types";
import { formatINR } from "@/lib/format";
import { cn } from "@/lib/utils";

type Phase = "loading" | "idle" | "running" | "complete" | "error";

export function ReviewClient({ tenderId }: { tenderId: string }) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<ReviewSummary | null>(null);

  const [lines, setLines] = useState<TerminalLine[]>([]);
  const [bids, setBids] = useState<BidHeader[]>([]);
  const [cells, setCells] = useState<Record<string, AgentCell | undefined>>({});
  const [liveDisagreements, setLiveDisagreements] = useState<Disagreement[]>([]);

  const [drawerSel, setDrawerSel] = useState<CellSelection | null>(null);
  const [highlight, setHighlight] = useState<HighlightTarget | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const tok = await getAccessToken();
        if (!tok) throw new Error("Session expired — please sign in.");
        const s = await fetchReviewSummary(tenderId, tok);
        if (cancelled) return;
        setSummary(s);
        setPhase(s.reviewed ? "complete" : "idle");
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Could not load tender.");
        setPhase("error");
      }
    })();
    return () => { cancelled = true; };
  }, [tenderId]);

  const start = useCallback(async () => {
    setError(null);
    setLines([]);
    setBids([]);
    setCells({});
    setLiveDisagreements([]);
    setPhase("running");

    const tok = await getAccessToken();
    if (!tok) { setError("Session expired — please sign in again."); setPhase("error"); return; }

    const tStart = performance.now();
    const pushLine = (line: Omit<TerminalLine, "ts">) =>
      setLines((ls) => [...ls, { ...line, ts: performance.now() - tStart }]);

    try {
      await reviewTenderStream(tenderId, tok, (event, data) => {
        switch (event) {
          case "review_start":
            pushLine({ event, level: "head",
              text: `▶ REVIEW START · method=${data.evaluation_method} · ${data.bids} bid${data.bids === 1 ? "" : "s"}` });
            break;
          case "bid_start": {
            const b = { bid_id: String(data.bid_id), org_name: String(data.org_name) };
            setBids((bs) => bs.find((x) => x.bid_id === b.bid_id) ? bs : [...bs, b]);
            pushLine({ event, level: "head", text: `── BID ${b.org_name} (${b.bid_id.slice(0,8)}) ──` });
            break;
          }
          case "agent_start": {
            const bid_id = String(data.bid_id ?? "");
            const agent = String(data.agent);
            setCells((c) => ({ ...c, [`${bid_id}::${agent}`]: { status: "running" } }));
            pushLine({ event, text: `   ▷ ${(AGENT_LABEL[agent] ?? agent).toUpperCase()}` });
            break;
          }
          case "claim_emitted": {
            const c = data as ClaimRow;
            pushLine({ event, level: "claim",
              text: `      • [${c.verdict}] ${(AGENT_LABEL[c.agent] ?? c.agent).toUpperCase()}  ${c.source_doc} p.${c.page_number}` });
            const key = `${c.bid_id}::${c.agent}`;
            setCells((cells) => {
              const cur = cells[key] ?? { status: "running" as const };
              return { ...cells, [key]: { ...cur, claims: (cur.claims ?? 0) + 1 } };
            });
            break;
          }
          case "agent_complete": {
            const bid_id = String(data.bid_id ?? "");
            const agent = String(data.agent);
            setCells((c) => ({
              ...c,
              [`${bid_id}::${agent}`]: {
                status: data.status === "failed" ? "error" : "done",
                verdict: data.verdict as Verdict,
                claims: typeof data.claims === "number" ? data.claims : (c[`${bid_id}::${agent}`]?.claims ?? 0),
                elapsedMs: data.elapsed_ms as number,
              },
            }));
            pushLine({ event, text: `   ◁ ${(AGENT_LABEL[agent] ?? agent).toUpperCase()}  ${data.verdict ?? "—"}  ${(data.elapsed_ms ?? 0)}ms` });
            break;
          }
          case "disagreement_detected":
            setLiveDisagreements((ds) => [...ds, data as Disagreement]);
            pushLine({ event, level: "warn",
              text: `   ⚠ DISAGREEMENT  [${String(data.type)}]  ${(data as Disagreement).org_name ?? ""}` });
            break;
          case "orchestrator_complete":
            pushLine({ event, level: "head", text: "■ ORCHESTRATOR COMPLETE" });
            break;
          case "review_error":
            pushLine({ event, level: "warn", text: `ERROR: ${String((data as { message: string }).message)}` });
            break;
        }
      });

      const t = await getAccessToken();
      if (t) {
        const s = await fetchReviewSummary(tenderId, t);
        setSummary(s);
        setPhase("complete");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Review failed.");
      setPhase("error");
    }
  }, [tenderId]);

  const downloadAudit = useCallback(async () => {
    const tok = await getAccessToken();
    if (!tok) { setError("Session expired."); return; }
    try { await openAuditPdf(tenderId, tok); }
    catch (e) { setError(e instanceof Error ? e.message : "Audit PDF failed."); }
  }, [tenderId]);

  const submittedBidCount = useMemo(
    () => summary?.bids.filter((b) => b.bid_status === "submitted").length ?? 0,
    [summary],
  );
  const totalBids = summary?.bids.length ?? 0;
  const t = summary?.tender;
  const reviewedAlready = phase === "complete" || (summary?.reviewed ?? false);

  if (phase === "loading") {
    return <div className="font-mono text-[12px] text-gov-ink-muted">Loading review…</div>;
  }
  if (phase === "error") {
    return (
      <div className="rounded-sm border border-gov-maroon/40 bg-gov-maroon-soft px-4 py-3 text-[13px] text-gov-maroon">
        {error}
      </div>
    );
  }

  return (
    <>
      <GovBreadcrumb items={[
        { label: "Home", href: "/officer/dashboard" },
        { label: "Tenders", href: "/officer/tenders" },
        { label: "Review" },
      ]} />

      <div className="mt-4 flex flex-col gap-5">
        {/* Tender meta header */}
        <div className="overflow-hidden rounded-sm border border-gov-border bg-gov-surface">
          <div className="border-l-4 border-l-gov-navy px-5 py-4">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0">
                <h1 className="font-serif text-[24px] font-semibold leading-tight text-gov-ink line-clamp-2">
                  {t?.title ?? "Tender review"}
                </h1>
                <p className="mt-1 font-mono text-[12px] text-gov-ink-muted">
                  Ref&nbsp;<span className="text-gov-ink">{t?.reference_no ?? "—"}</span>
                  &nbsp;·&nbsp;Method&nbsp;<span className="font-semibold text-gov-navy">{t?.evaluation_method ?? "—"}</span>
                  &nbsp;·&nbsp;Estimated value&nbsp;<span className="text-gov-ink">{formatINR(t?.estimated_value ?? null)}</span>
                  &nbsp;·&nbsp;<span className="text-gov-ink">{totalBids}</span>&nbsp;bid{totalBids === 1 ? "" : "s"} received
                </p>
                {phase === "idle" && submittedBidCount > 0 && (
                  <p className="mt-2 text-[13px] font-semibold text-gov-navy">
                    {submittedBidCount} submitted bid{submittedBidCount === 1 ? "" : "s"} ready — click <span className="underline">Run AI Review</span> to begin.
                  </p>
                )}
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {phase !== "running" && (
                  <button
                    onClick={start}
                    disabled={submittedBidCount === 0 && !reviewedAlready}
                    className={cn(
                      "inline-flex items-center gap-2 rounded-sm px-4 py-2 font-sans text-[13px] font-semibold transition-colors",
                      reviewedAlready
                        ? "border border-gov-border bg-gov-surface text-gov-navy hover:bg-gov-bg"
                        : "bg-gov-navy text-white hover:bg-gov-navy-hover",
                      submittedBidCount === 0 && !reviewedAlready && "cursor-not-allowed opacity-50",
                    )}
                  >
                    {reviewedAlready ? <><RotateCcw className="size-4" /> Re-run review</> : <><Play className="size-4" /> Run AI Review</>}
                  </button>
                )}
                {phase === "running" && (
                  <span className="inline-flex items-center gap-2 rounded-sm border border-gov-saffron bg-gov-saffron-soft px-3 py-2 font-sans text-[12px] font-semibold uppercase tracking-wide text-gov-ink">
                    <span className="size-2 animate-pulse-dot rounded-full bg-gov-saffron" />
                    Evaluation in progress
                  </span>
                )}
                {reviewedAlready && (
                  <button
                    onClick={downloadAudit}
                    className="inline-flex items-center gap-2 rounded-sm border border-gov-navy bg-gov-navy px-4 py-2 font-sans text-[13px] font-semibold text-white hover:bg-gov-navy-hover"
                  >
                    <Download className="size-4" /> Download Audit Report
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Body */}
        {phase === "running" && (
          <div className="grid h-[calc(100vh-360px)] min-h-[480px] grid-cols-1 gap-4 lg:grid-cols-[3fr_2fr]">
            <AgentTerminal lines={lines} />
            <AgentGrid bids={bids} cells={cells} />
          </div>
        )}

        {(phase === "complete" || (phase === "idle" && reviewedAlready)) && summary && (
          <CompleteView
            summary={summary}
            drawerSel={drawerSel}
            onSelect={setDrawerSel}
            onCloseDrawer={() => setDrawerSel(null)}
            onOpenCitation={(c) =>
              setHighlight({ bidId: c.bid_id, sourceDoc: c.source_doc, page: c.page_number, quote: c.quote })
            }
            onJumpFromBanner={(bidId, sourceDoc, page, quote) =>
              bidId && setHighlight({ bidId, sourceDoc, page, quote })
            }
            liveDisagreements={liveDisagreements}
          />
        )}

        {phase === "idle" && !reviewedAlready && summary && (
          <EmptyState submittedCount={submittedBidCount} totalBids={totalBids} onRun={start} />
        )}
      </div>

      <PageHighlightModal target={highlight} onClose={() => setHighlight(null)} />
    </>
  );
}

function CompleteView({
  summary, drawerSel, onSelect, onCloseDrawer, onOpenCitation, onJumpFromBanner, liveDisagreements,
}: {
  summary: ReviewSummary;
  drawerSel: CellSelection | null;
  onSelect: (s: CellSelection) => void;
  onCloseDrawer: () => void;
  onOpenCitation: (c: ClaimRow) => void;
  onJumpFromBanner: (bidId: string | undefined, sourceDoc: string, page: number, quote: string) => void;
  liveDisagreements: Disagreement[];
}) {
  // Reconstruct disagreements from persisted claims; merge with live cartel/duplicate events.
  const techVsComp: Disagreement[] = summary.bids
    .filter((b) => b.bid_status === "human_review_required" && b.recommended_action === "review")
    .map((b) => {
      const tech = b.agents.find((a) => a.agent === "technical_agent");
      const comp = b.agents.find((a) => a.agent === "compliance_agent");
      const techClaim = tech?.claims.find((c) => c.verdict === "PASS") ?? tech?.claims.find((c) => c.verdict === "FLAG");
      const compClaim = comp?.claims.find((c) => c.verdict === "FAIL");
      if (!techClaim || !compClaim) return null;
      return {
        type: "technical_vs_compliance",
        bid_id: b.bid_id,
        org_name: b.org_name,
        note: "Technical evaluation passed but Compliance failed — the orchestrator refuses to recommend automatically and routes this bid to human review.",
        conflicting_claims: [techClaim, compClaim].map((c) => ({
          claim: c.claim, verdict: c.verdict, agent: c.agent,
          source_doc: c.source_doc, page_number: c.page_number, quote: c.quote, severity: c.severity,
        })),
      } as Disagreement;
    })
    .filter((x): x is Disagreement => x !== null);

  const liveExtras = liveDisagreements.filter((d) =>
    d.type === "cartel_suspicion" || d.type === "duplicate_bidders" || d.type === "abnormally_low_bid",
  );

  // Reconstruct duplicate-bidder disagreements from the persisted reasoning_agent
  // citations, so the banner survives a page refresh (the live SSE events would
  // otherwise be the only carrier).
  const persistedDup = (() => {
    if (liveExtras.some((d) => d.type === "duplicate_bidders")) return null;
    const dupBids = summary.bids.filter((b) =>
      b.agents.some((a) =>
        a.agent === "reasoning_agent" && a.claims.some((c) => c.claim.includes("Bid content matches"))
      )
    );
    if (dupBids.length < 2) return null;
    return {
      type: "duplicate_bidders",
      note:
        `${dupBids.length} bids share substantially identical content after normalising ` +
        "bidder names — possible shell / proxy submission. Investigate identity, ownership, " +
        "and authorised-signatory linkage before any award.",
      bids: dupBids.map((b) => ({
        bid_id: b.bid_id,
        org_name: b.org_name,
        quoted_amount: b.quoted_amount ?? 0,
      })),
    } as Disagreement;
  })();

  const disagreements = [
    ...techVsComp,
    ...liveExtras,
    ...(persistedDup ? [persistedDup] : []),
  ];

  const award = summary.ranking.find((r) => r.recommended_action === "award");
  const needsReview = summary.human_review_required.length > 0;

  return (
    <div className="flex flex-col gap-5">
      <RankingHeader summary={summary} award={award} needsReview={needsReview} />
      {disagreements.length > 0 && (
        <div className="space-y-3">
          {disagreements.map((d, i) => (
            <DisagreementBanner key={i} d={d} onJump={onJumpFromBanner} />
          ))}
        </div>
      )}
      <ComparisonMatrix summary={summary} selected={drawerSel} onSelectCell={onSelect} />
      <CitationDrawer
        open={!!drawerSel}
        selection={drawerSel}
        summary={summary}
        onClose={onCloseDrawer}
        onOpenCitation={onOpenCitation}
      />
    </div>
  );
}

function RankingHeader({
  summary, award, needsReview,
}: {
  summary: ReviewSummary;
  award?: ReviewSummary["ranking"][number];
  needsReview: boolean;
}) {
  return (
    <section className={cn(
      "overflow-hidden rounded-sm border bg-gov-surface",
      needsReview ? "border-gov-maroon/40" : "border-gov-border",
    )}>
      <div className="border-b border-gov-border bg-gov-bg px-5 py-3">
        <h2 className="font-sans text-[12px] font-semibold uppercase tracking-wide text-gov-ink-muted">
          Recommendation — {summary.tender.evaluation_method ?? "—"} evaluation
        </h2>
      </div>
      <div className="px-5 py-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            {needsReview && !award ? (
              <p className="font-serif text-[22px] font-semibold leading-tight text-gov-maroon">
                HUMAN REVIEW REQUIRED
              </p>
            ) : award ? (
              <p className="font-serif text-[22px] font-semibold leading-tight text-gov-ink">
                Recommended for award: <span className="text-gov-navy">{award.org_name}</span>
                <span className="ml-2 rounded-sm border border-gov-green/50 bg-gov-green-soft px-2 py-0.5 align-middle font-sans text-[11px] font-semibold uppercase tracking-wide text-gov-green">
                  L1 · award
                </span>
              </p>
            ) : (
              <p className="font-serif text-[22px] font-semibold leading-tight text-gov-ink">
                No bid recommended for award
              </p>
            )}
            {needsReview && (
              <p className="mt-1 text-[12.5px] text-gov-ink-muted">
                One or more bids were routed to human review (disagreement, abnormally-low, cartel suspicion,
                or duplicate submission). See the highlighted alerts below.
              </p>
            )}
          </div>
          {award && (
            <div className="text-right">
              <div className="font-sans text-[10.5px] font-semibold uppercase tracking-wide text-gov-ink-muted">Quoted price</div>
              <div className="font-mono text-[18px] tabular-nums text-gov-ink">{formatINR(award.quoted_amount)}</div>
            </div>
          )}
        </div>

        <div className="mt-4 grid grid-cols-1 gap-2 md:grid-cols-3">
          {summary.ranking.map((r) => (
            <div key={r.bid_id}
              className={cn(
                "flex items-center justify-between gap-3 rounded-sm border px-3 py-2.5",
                r.recommended_action === "award"     && "border-gov-green/40 bg-gov-green-soft",
                r.recommended_action === "review"    && "border-gov-saffron/50 bg-gov-saffron-soft",
                r.recommended_action === "reject"    && "border-gov-maroon/40 bg-gov-maroon-soft",
                r.recommended_action === "shortlist" && "border-gov-navy/30 bg-gov-navy-soft",
                !r.recommended_action && "border-gov-border bg-white",
              )}>
              <div className="min-w-0">
                <div className="font-sans text-[13px] font-semibold text-gov-ink truncate">{r.org_name}</div>
                <div className="font-mono text-[11px] uppercase tracking-wide text-gov-ink-muted">
                  {r.rank ? `L${r.rank}` : "—"} · {(r.recommended_action ?? "—").toUpperCase()}
                </div>
              </div>
              <div className="text-right font-mono text-[12px] tabular-nums text-gov-ink">
                {formatINR(r.quoted_amount)}
                {r.combined_score != null && (
                  <div className="text-[10.5px] text-gov-ink-faint">cmb {r.combined_score.toFixed(2)}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function EmptyState({
  submittedCount, totalBids, onRun,
}: { submittedCount: number; totalBids: number; onRun: () => void }) {
  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="max-w-md rounded-sm border border-dashed border-gov-border bg-gov-surface px-6 py-10 text-center">
        {submittedCount > 0 ? (
          <>
            <div className="mx-auto mb-3 grid size-12 place-items-center rounded-sm bg-gov-navy-soft text-gov-navy">
              <FileSearch className="size-6" />
            </div>
            <h2 className="font-serif text-[18px] font-semibold text-gov-ink">
              {submittedCount} submitted bid{submittedCount === 1 ? "" : "s"} ready for evaluation
            </h2>
            <p className="mt-2 text-[13px] text-gov-ink-muted">
              Run the AI-assisted pipeline to evaluate every submitted bid against the parsed tender schema.
              You will see live progress as each agent runs, then a comparison matrix with citation evidence.
            </p>
            <button
              onClick={onRun}
              className="mt-5 inline-flex items-center gap-2 rounded-sm bg-gov-navy px-4 py-2 font-sans text-[13px] font-semibold text-white hover:bg-gov-navy-hover"
            >
              <Play className="size-4" /> Run AI Review
            </button>
          </>
        ) : (
          <>
            <h2 className="font-serif text-[18px] font-semibold text-gov-ink">No submitted bids</h2>
            <p className="mt-2 text-[13px] text-gov-ink-muted">
              {totalBids === 0 ? "No bids have been received on this tender yet." : "Bids exist but none are in 'submitted' state."}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
