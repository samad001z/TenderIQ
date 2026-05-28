"""technical_agent — scores the SUBMITTED bid against the tender's technical criteria.

Emits one page-cited claim per technical criterion (PASS/FLAG/FAIL with the bid
evidence) and an overall technical_score (0-100) the reasoning_agent uses for QCBS
weighting. The score is weighted by the marks/weights the tender assigns to each
criterion where stated.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from agents.base import (
    AgentResult,
    bid_pages_parts,
    ms_since,
    overall_verdict,
    run_structured_citation_agent,
    tender_context,
)
from models.agent_io import TechnicalAnalysis
from services.gemini import GeminiService
from shared.citation import Citation

AGENT_NAME = "technical_agent"

# Defensive post-filter. The prompt tells the model to skip index/compliance
# pages, but at temperature 0.1 it still slips into them ~10–15% of runs and
# emits a FAIL on the OEM/EMD/BIS/index quote. We drop any claim whose quote is
# clearly NOT technical content — restoring deterministic verdicts across runs.
_NON_TECHNICAL_QUOTE_MARKERS = (
    "index of enclosed documents",
    "s.no.",
    "annexure",
    "ppp-mii",
    "local content",
    "integrity pact",
    "earnest money deposit",
    "amount remitted",
    "utr reference",
    "oem authorization",
    "oem / manufacturer",
    "manufacturer's authorisation",
    "maf dated",
    "bis / iso",
    "iso/iec 27001",
    "iso 9001",
    "cmmi-dev level",
    "declarations & authorised signature",
    "for and on behalf of",
)


def _is_non_technical_quote(quote: str) -> bool:
    q = (quote or "").lower()
    return any(marker in q for marker in _NON_TECHNICAL_QUOTE_MARKERS)


def _drop_non_technical(claims: list[Citation]) -> tuple[list[Citation], list[dict]]:
    kept: list[Citation] = []
    dropped: list[dict] = []
    for c in claims:
        if _is_non_technical_quote(c.quote):
            dropped.append({
                "claim": c.claim,
                "verdict": c.verdict,
                "page_number": c.page_number,
                "quote": c.quote,
                "reasons": ["claim cites a non-technical page (index/compliance/certification)"],
            })
            continue
        kept.append(c)
    return kept, dropped

_SYSTEM = """You are TenderIQ's Technical Evaluator for Indian government procurement. You are
given a tender's TECHNICAL criteria (some with marks/weights) and a bidder's SUBMITTED bid as
page-labeled text.

For EACH technical criterion, judge how well the bid meets it and emit one claim:
- PASS: the bid clearly meets/exceeds the TECHNICAL requirement (cite the bid page + quote).
- FLAG: partially met / ambiguous / needs clarification.
- FAIL: not met or contradicted by the bid.

SCOPE — ONLY evaluate against the tender's TECHNICAL_CRITERIA listed below. The following
pages of the bid are NOT technical content; ignore them entirely (do not cite them, do not
mark any technical criterion FAIL because of items on these pages):
  • the INDEX / TABLE OF CONTENTS page
  • PPP-MII / Local content certification pages
  • CVC Integrity Pact pages
  • Earnest Money Deposit (EMD) pages
  • OEM / Manufacturer Authorization Letter pages
  • BIS / ISO Certification pages
  • Declarations & Signature pages
A missing OEM authorization is NEVER a technical failure — it is a compliance issue handled
by a separate compliance agent. Cite ONLY technical content (solution architecture,
methodology, team & key personnel, past technical execution). If a technical criterion
cannot be evaluated from the technical pages provided, choose FLAG, not FAIL.

Then compute `technical_score`: a 0-100 overall score. If the criteria carry marks/weights, use
them (weighted average of how well each is met, scaled to 100); otherwise weight equally.

HARD RULES (citation contract):
- page_number MUST be the 1-indexed page in `source_doc` where evidence appears, and `quote` MUST
  be verbatim from that page. Never fabricate a page or quote.
- source_doc MUST be the exact file name from the "=== DOC: ... | PAGE n ===" headers.
- Set tender_clause to the criterion and tender_clause_page to its tender page.
- severity: a failed mandatory technical requirement is 'high'; FLAG 'medium'; PASS 'low'.
  confidence in [0,1]. One claim per criterion, in order."""


def _run_sync(tender_schema: dict[str, Any], intel: dict[str, Any], gemini: GeminiService):
    criteria = tender_schema.get("technical_criteria") or []
    context = [
        "TENDER (for tender_clause references):\n" + tender_context(tender_schema),
        "TECHNICAL CRITERIA TO SCORE (one claim each, in order):\n"
        + "\n".join(
            f"{i+1}. (tender p.{c.get('source_page')}, weight={c.get('weight')}) {c.get('description')}"
            for i, c in enumerate(criteria)
        ),
        *bid_pages_parts(intel),
    ]
    return run_structured_citation_agent(
        AGENT_NAME, _SYSTEM, context, gemini, TechnicalAnalysis
    )


async def run(
    tender_schema: dict[str, Any],
    bid_id: str,
    bid_doc_intel: dict[str, Any],
    *,
    gemini: GeminiService | None = None,
) -> AgentResult:
    start = time.perf_counter()
    g = gemini or GeminiService()
    try:
        obj, valid, rejections, raw = await asyncio.to_thread(
            _run_sync, tender_schema, bid_doc_intel, g
        )
        # Defensive: drop claims that quote non-technical pages (the model
        # occasionally leaks into the index/OEM/EMD/cert pages despite the
        # prompt). Keeps the technical verdict deterministic across runs.
        kept, post_dropped = _drop_non_technical(valid)
        rejections = list(rejections) + post_dropped
        score = float(getattr(obj, "technical_score", 0.0) or 0.0)
        return AgentResult(
            agent_name=AGENT_NAME,
            status="completed",
            verdict=overall_verdict(kept),
            claims=kept,
            elapsed_ms=ms_since(start),
            rejections=rejections,
            raw_output=raw,
            data={"technical_score": round(score, 2)},
        )
    except Exception as e:  # noqa: BLE001
        return AgentResult(
            agent_name=AGENT_NAME,
            status="failed",
            verdict="INFO",
            claims=[],
            elapsed_ms=ms_since(start),
            error=str(e),
        )
