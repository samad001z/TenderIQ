"""The officer-review orchestration: run the agent pipeline over submitted bids and
stream live SSE events.

`stream_review` is an async generator of (event, payload) tuples. The FastAPI route
wraps each as an SSE frame; tests/scripts can consume the tuples directly with a
NullPersist (no DB/LLM coupling).

Events emitted (per Phase 5 spec, plus a few framing events):
  review_start            once, at the top
  bid_start               per bid
  agent_start             per agent (ingestion, tender_parser, the 5 specialists, reasoning)
  claim_emitted           per validated Citation
  agent_complete          per agent (carries verdict, #claims, #rejections, elapsed_ms)
  disagreement_detected   Technical-vs-Compliance conflicts and cartel clusters
  orchestrator_complete   once, with the final ranking + recommendations
  review_error            on a fatal pipeline error

Concurrency: the five specialists run concurrently per bid (asyncio.gather/as_completed);
each agent offloads its blocking Gemini/PDF work to a thread, so Vertex latency overlaps.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator, Optional

from agents import SPECIALISTS, reasoning_agent
from agents import ingestion_agent, tender_parser_agent
from agents.base import AgentResult
from shared.citation import Citation

# Which model string to record per agent in agent_runs.model.
_AGENT_MODEL = {
    "ingestion_agent": "pymupdf",
    "tender_parser_agent": "reference",
    "risk_agent": "deterministic",
    "reasoning_agent": "deterministic",
}


def _claim_payload(c: Citation, bid_id: str, agent_run_id: str | None) -> dict:
    return {
        "bid_id": bid_id,
        "agent_run_id": agent_run_id,
        "agent": c.agent,
        "claim": c.claim,
        "verdict": c.verdict,
        "source_doc": c.source_doc,
        "page_number": c.page_number,
        "quote": c.quote,
        "confidence": c.confidence,
        "tender_clause": c.tender_clause,
        "tender_clause_page": c.tender_clause_page,
        "severity": c.severity,
    }


# ---------------------------------------------------------------------------
# Persistence — DB-backed for the route, null for hermetic tests
# ---------------------------------------------------------------------------
class NullPersist:
    """No-op persistence. agent_run() returns a fake id so claim_emitted has one."""

    async def set_bid_status(self, bid_id: str, status: str, quoted_amount: float | None = None) -> None:
        return None

    async def agent_run(self, bid_id: str, tender_id: str, result: AgentResult) -> str | None:
        return f"mock-run-{uuid.uuid4().hex[:8]}"

    async def citations(self, agent_run_id: str | None, bid_id: str, tender_id: str, claims: list[Citation]) -> None:
        return None

    async def recommendation(self, bid_id: str, tender_id: str, rec: dict) -> None:
        return None

    async def review_scores(self, bid_id: str, scores: dict) -> None:
        return None

    async def stamp_tender(self, tender_id: str) -> None:
        return None


class DbPersist:
    """Writes agent_runs, citations, recommendations, and bid status to Supabase."""

    def __init__(self, sb, model: str):
        self.sb = sb
        self.model = model  # the Gemini Pro model id used by the LLM specialists

    async def set_bid_status(self, bid_id: str, status: str, quoted_amount: float | None = None) -> None:
        update: dict[str, Any] = {"status": status}
        if quoted_amount is not None:
            update["quoted_amount"] = quoted_amount

        def _do():
            self.sb.table("bids").update(update).eq("id", bid_id).execute()

        await asyncio.to_thread(_do)

    async def agent_run(self, bid_id: str, tender_id: str, result: AgentResult) -> str | None:
        now = datetime.now(timezone.utc)
        started = now - timedelta(milliseconds=result.elapsed_ms)
        row = {
            "bid_id": bid_id,
            "agent": result.agent_name,
            "status": result.status,
            "model": _AGENT_MODEL.get(result.agent_name, self.model),
            "rejections": result.rejections,
            "raw_output": result.raw_output,
            "error": result.error,
            "started_at": started.isoformat(),
            "completed_at": now.isoformat(),
        }

        def _do():
            res = self.sb.table("agent_runs").insert(row).execute()
            return res.data[0]["id"] if res.data else None

        return await asyncio.to_thread(_do)

    async def citations(self, agent_run_id: str | None, bid_id: str, tender_id: str, claims: list[Citation]) -> None:
        if not claims:
            return
        rows = [
            {
                "agent_run_id": agent_run_id,
                "bid_id": bid_id,
                "tender_id": tender_id,
                "claim": c.claim,
                "verdict": c.verdict,
                "source_doc": c.source_doc,
                "page_number": c.page_number,
                "quote": c.quote,
                "confidence": c.confidence,
                "tender_clause": c.tender_clause,
                "tender_clause_page": c.tender_clause_page,
                "severity": c.severity,
                "agent": c.agent,
            }
            for c in claims
        ]

        def _do():
            self.sb.table("citations").insert(rows).execute()

        await asyncio.to_thread(_do)

    async def recommendation(self, bid_id: str, tender_id: str, rec: dict) -> None:
        row = {"bid_id": bid_id, "tender_id": tender_id, **rec}

        def _do():
            self.sb.table("recommendations").insert(row).execute()

        await asyncio.to_thread(_do)

    async def review_scores(self, bid_id: str, scores: dict) -> None:
        # Pass None through so previous values are overwritten when this bid is no longer
        # ranked (e.g. now in human_review_required after being shortlisted in a prior run).
        def _do():
            self.sb.table("bids").update(scores).eq("id", bid_id).execute()

        await asyncio.to_thread(_do)

    async def stamp_tender(self, tender_id: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()

        def _do():
            self.sb.table("tenders").update({"last_reviewed_at": ts}).eq("id", tender_id).execute()

        await asyncio.to_thread(_do)


# ---------------------------------------------------------------------------
# The pipeline
# ---------------------------------------------------------------------------
def _ref_result(name: str, data: dict) -> AgentResult:
    return AgentResult(agent_name=name, status="completed", verdict="INFO", claims=[], data=data)


def _price_citation(fin: Optional[AgentResult]) -> Citation | None:
    """The financial agent's price line — used to ground a cartel citation."""
    if not fin:
        return None
    # Prefer a non-FAIL valid claim (the price line) over the abnormally-low FAIL.
    for c in fin.claims:
        if c.page_number > 0 and c.verdict in ("INFO", "FLAG"):
            return c
    return next((c for c in fin.claims if c.page_number > 0), None)


async def stream_review(
    tender_schema: dict[str, Any],
    intels: list[dict[str, Any]],
    *,
    gemini: Any = None,
    persist: Any = None,
    tender_id: str | None = None,
) -> AsyncIterator[tuple[str, dict]]:
    persist = persist or NullPersist()
    method = (tender_schema or {}).get("evaluation_method", "unknown")

    yield "review_start", {
        "tender_id": tender_id,
        "evaluation_method": method,
        "bids": len(intels),
    }

    syntheses: list[reasoning_agent.BidSynthesis] = []
    price_cites: dict[str, Citation] = {}
    # Collect the FULL per-bid intel (with extracted documents) for cross-bid checks
    # like duplicate detection — `intels` arrives as a thin {bid_id, tender_id,
    # org_name} list and is enriched lazily as each bid is ingested.
    full_intels: list[dict[str, Any]] = []

    for thin in intels:
        bid_id = thin["bid_id"]
        yield "bid_start", {"bid_id": bid_id, "org_name": thin.get("org_name")}
        await persist.set_bid_status(bid_id, "under_review")

        # ingestion_agent — build bid_doc_intel. Pre-built (tests) is reused as-is;
        # otherwise the agent downloads + extracts the bid PDFs live, here in-stream.
        yield "agent_start", {"bid_id": bid_id, "agent": "ingestion_agent"}
        if "documents" in thin:
            intel = thin
            ing = _ref_result(
                "ingestion_agent",
                {"documents": len(intel.get("documents", [])),
                 "pages": sum(d.get("page_count", 0) for d in intel.get("documents", []))},
            )
        else:
            ing = await ingestion_agent.run(tender_schema, bid_id, None, gemini=gemini)
            intel = ing.data or {
                "bid_id": bid_id, "tender_id": thin.get("tender_id"),
                "org_name": thin.get("org_name"), "quoted_amount": None, "documents": [],
            }
        t_id = intel.get("tender_id") or thin.get("tender_id") or tender_id
        full_intels.append(intel)
        run_id = await persist.agent_run(bid_id, t_id, ing)
        yield "agent_complete", {**ing.summary(), "bid_id": bid_id, "agent_run_id": run_id, "data": ing.raw_output}

        # tender_parser_agent — reference step (schema parsed in Phase 3).
        yield "agent_start", {"bid_id": bid_id, "agent": "tender_parser_agent"}
        tp = await tender_parser_agent.run(tender_schema, bid_id, intel, gemini=gemini)
        run_id = await persist.agent_run(bid_id, t_id, tp)
        yield "agent_complete", {**tp.summary(), "bid_id": bid_id, "agent_run_id": run_id, "data": tp.data}

        # Five specialists, concurrently.
        for mod in SPECIALISTS:
            yield "agent_start", {"bid_id": bid_id, "agent": mod.AGENT_NAME}

        tasks = [
            asyncio.create_task(mod.run(tender_schema, bid_id, intel, gemini=gemini))
            for mod in SPECIALISTS
        ]
        specialists: dict[str, AgentResult] = {}
        for fut in asyncio.as_completed(tasks):
            res: AgentResult = await fut
            specialists[res.agent_name] = res
            run_id = await persist.agent_run(bid_id, t_id, res)
            await persist.citations(run_id, bid_id, t_id, res.claims)
            for c in res.claims:
                yield "claim_emitted", _claim_payload(c, bid_id, run_id)
            yield "agent_complete", {**res.summary(), "bid_id": bid_id, "agent_run_id": run_id}

        price_cites[bid_id] = _price_citation(specialists.get("financial_agent"))

        syn = reasoning_agent.synthesize_bid(tender_schema, intel, specialists)
        syntheses.append(syn)
        for d in syn.disagreements:
            yield "disagreement_detected", d

    # --- cross-bid reasoning -------------------------------------------------
    reasoning_start = time.perf_counter()
    yield "agent_start", {"agent": reasoning_agent.AGENT_NAME, "scope": "cross_bid"}

    cartels = reasoning_agent.detect_cartel(syntheses)
    by_id = {s.bid_id: s for s in syntheses}
    for group in cartels:
        for b in group["bids"]:
            syn = by_id.get(b["bid_id"])
            if not syn:
                continue
            syn.needs_human_review = True
            syn.bid_status = "human_review_required"
            syn.recommended_action = "review"
            cc = reasoning_agent.cartel_citation(syn, group, price_cites.get(syn.bid_id))
            if cc:
                t_id = next((i.get("tender_id") for i in intels if i["bid_id"] == syn.bid_id), tender_id)
                cartel_run = AgentResult(
                    agent_name=reasoning_agent.AGENT_NAME, status="completed",
                    verdict="FLAG", claims=[cc],
                )
                run_id = await persist.agent_run(syn.bid_id, t_id, cartel_run)
                await persist.citations(run_id, syn.bid_id, t_id, [cc])
                yield "claim_emitted", _claim_payload(cc, syn.bid_id, run_id)
        yield "disagreement_detected", group

    # Cross-bid duplicate / proxy submission detection — "same documents, only the
    # name differs". Emits a disagreement_detected + a page-grounded FLAG citation
    # on each bid in the cluster. Does NOT override bid_status — the prior verdict
    # (e.g. reject on eligibility) stands, the duplicate is surfaced as an integrity
    # flag the officer must investigate.
    duplicates = reasoning_agent.detect_duplicate_bidders(full_intels)
    intel_by_id = {i["bid_id"]: i for i in full_intels}
    for group in duplicates:
        bid_ids = [b["bid_id"] for b in group["bids"]]
        names = {b["bid_id"]: b["org_name"] for b in group["bids"]}
        for bid_id in bid_ids:
            intel = intel_by_id.get(bid_id)
            if not intel:
                continue
            others = [names[x] for x in bid_ids if x != bid_id]
            dc = reasoning_agent.duplicate_citation(intel, others, group.get("match_score_pct", 0.0))
            if dc:
                t_id = intel.get("tender_id") or tender_id
                dup_run = AgentResult(
                    agent_name=reasoning_agent.AGENT_NAME, status="completed",
                    verdict="FLAG", claims=[dc],
                )
                run_id = await persist.agent_run(bid_id, t_id, dup_run)
                await persist.citations(run_id, bid_id, t_id, [dc])
                yield "claim_emitted", _claim_payload(dc, bid_id, run_id)
        yield "disagreement_detected", group

    ranking = reasoning_agent.rank_and_recommend(tender_schema, syntheses)

    # Persist final recommendations + scores + bid statuses + tender stamp.
    for syn in syntheses:
        t_id = next((i.get("tender_id") for i in intels if i["bid_id"] == syn.bid_id), tender_id)
        await persist.recommendation(
            syn.bid_id,
            t_id,
            {
                "recommended_action": syn.recommended_action,
                "overall_score": syn.combined_score if syn.combined_score is not None else syn.technical_score,
                "summary": syn.summary,
                "rationale": syn.rationale,
                "generated_by": reasoning_agent.AGENT_NAME,
            },
        )
        await persist.review_scores(syn.bid_id, {
            "technical_score": syn.technical_score,
            "financial_score": syn.financial_score,
            "combined_score": syn.combined_score,
            "review_rank": syn.rank,
        })
        await persist.set_bid_status(syn.bid_id, syn.bid_status, syn.quoted_amount)
    if tender_id:
        await persist.stamp_tender(tender_id)

    elapsed = int((time.perf_counter() - reasoning_start) * 1000)
    yield "agent_complete", {
        "agent": reasoning_agent.AGENT_NAME,
        "status": "completed",
        "verdict": "INFO",
        "claims": sum(len(g["bids"]) for g in cartels),
        "elapsed_ms": elapsed,
    }

    all_disagreements = [d for s in syntheses for d in s.disagreements] + cartels + duplicates
    yield "orchestrator_complete", {
        "tender_id": tender_id,
        "evaluation_method": method,
        "ranking": ranking,
        "disagreements": all_disagreements,
        "human_review_required": [s.bid_id for s in syntheses if s.needs_human_review],
        "recommended_award": next((r["bid_id"] for r in ranking if r["recommended_action"] == "award"), None),
    }
