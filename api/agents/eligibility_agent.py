"""eligibility_agent — does the SUBMITTED bid prove each mandatory pre-qualification?

Officer-side counterpart of the bidder's eligibility pre-check. For every
eligibility criterion in the tender_schema it looks for proof IN THE BID and
emits a Citation:
  - PASS: the bid contains evidence satisfying the criterion (cite bid page + quote).
  - FAIL: the bid clearly fails it (e.g. turnover/experience below the bar) — cite
    the bid page+quote that shows the shortfall.
  - FLAG: a required proof appears missing/ambiguous in the bid.
Each claim references the tender criterion via tender_clause + tender_clause_page.
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
    run_citation_agent,
    tender_context,
)
from services.gemini import GeminiService

AGENT_NAME = "eligibility_agent"

_SYSTEM = """You are TenderIQ's Eligibility Evaluator for Indian government procurement
(GFR 2017 / CPPP / GeM). You are given a tender's MANDATORY eligibility criteria and a
bidder's SUBMITTED bid as page-labeled text.

For EACH eligibility criterion, decide whether the bid proves it and emit one claim:
- verdict PASS: the bid contains evidence that clearly satisfies the criterion. THIS IS
  THE DEFAULT when the requirement is met.
- verdict FAIL: choose ONLY when the bid explicitly states a value that violates the
  criterion (e.g. turnover ₹18 cr where the bar is ₹25 cr; CMMI Level 3 where Level 5
  is required). Cite the violating figure.
- verdict FLAG: the required proof is missing/ambiguous in the bid, or needs manual
  verification (e.g. a certificate referenced but not attached).

NUMERICAL COMPARISON GUIDANCE (read carefully — Indian crore numbers are easy to misread):
- For "X ≥ threshold" criteria, PASS when any shown value equals or EXCEEDS the threshold.
  ₹27 crore is far ABOVE a ₹3 crore minimum, not below it.
- For "at least N projects of value ≥ V" criteria, count every project whose value clearly
  meets V. If a bid lists three projects of ₹52cr / ₹27cr / ₹21cr against a ₹3cr bar, ALL
  THREE qualify — do not invert the comparison.
- When in doubt about a numerical comparison, choose PASS, never FAIL.

HARD RULES (citation contract):
- page_number MUST be the 1-indexed page in `source_doc` where your evidence appears, and
  `quote` MUST be copied verbatim from that page. Never invent a page or quote.
- source_doc MUST be the exact file name shown in the "=== DOC: ... | PAGE n ===" headers.
- Set tender_clause to the criterion text and tender_clause_page to its tender page.
- severity: FAIL on a mandatory criterion is 'high' or 'critical'; FLAG 'medium'; PASS 'low'.
- confidence in [0,1]. Emit exactly one claim per criterion, in order."""


def _run_sync(tender_schema: dict[str, Any], intel: dict[str, Any], gemini: GeminiService):
    criteria = tender_schema.get("eligibility_criteria") or []
    context = [
        "TENDER (for tender_clause references):\n" + tender_context(tender_schema),
        "ELIGIBILITY CRITERIA TO CHECK (one claim each, in order):\n"
        + "\n".join(
            f"{i+1}. (tender p.{c.get('source_page')}) {c.get('description')}"
            for i, c in enumerate(criteria)
        ),
        *bid_pages_parts(intel),
    ]
    return run_citation_agent(AGENT_NAME, _SYSTEM, context, gemini)


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
        valid, rejections, raw = await asyncio.to_thread(
            _run_sync, tender_schema, bid_doc_intel, g
        )
        return AgentResult(
            agent_name=AGENT_NAME,
            status="completed",
            verdict=overall_verdict(valid),
            claims=valid,
            elapsed_ms=ms_since(start),
            rejections=rejections,
            raw_output=raw,
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
