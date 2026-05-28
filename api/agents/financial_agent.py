"""financial_agent — extracts the bid's quoted price and flags abnormally low bids.

Two parts:
1. LLM extraction: locate the bidder's total quoted price in the financial bid / BoQ
   and emit a page-cited Citation for it (page + verbatim quote of the priced total).
2. Deterministic CVC rule: if the quoted total is MORE THAN 20% BELOW the tender's
   estimated value, flag it as "abnormally low" (CVC guidance — such bids warrant a
   written price justification before award). The flag Citation is grounded on the SAME
   page + quote as the extracted price, so it passes the citation gate.

L1 ranking (lowest among eligibility-passed) is cross-bid and lives in reasoning_agent;
this agent reports one bid's number + low-bid flag.
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
from models.agent_io import FinancialAnalysis
from services.gemini import GeminiService
from shared.citation import Citation

AGENT_NAME = "financial_agent"

# CVC norm used across the product: a bid >20% below the estimate is "abnormally low".
ABNORMAL_LOW_THRESHOLD = 0.20

_SYSTEM = """You are TenderIQ's Financial Evaluator for Indian government procurement. You are
given the tender's financial format + estimated value and a bidder's SUBMITTED financial bid /
BoQ as page-labeled text.

Tasks:
1. Locate the bidder's TOTAL QUOTED PRICE (the grand total / evaluated price in INR, inclusive
   as the tender requires). Put it in `quoted_total_inr` (a number, no commas/symbols). If no
   priced total can be found, set it to null.
2. Emit at least one claim citing that price: verdict INFO (or FLAG if the price is unclear/
   conditional), with page_number = the 1-indexed page of the financial doc where the total
   appears and `quote` = the verbatim price line.

HARD RULES (citation contract):
- page_number MUST be > 0 and refer to the page in `source_doc` where the figure appears;
  `quote` MUST be the verbatim text of that line. Never fabricate a page or quote.
- source_doc MUST be the exact file name from the "=== DOC: ... | PAGE n ===" headers.
- Set tender_clause to the financial-format requirement and tender_clause_page to its tender page.
- confidence in [0,1]. Do NOT compute whether the bid is abnormally low — that is done downstream."""


def _estimate(tender_schema: dict[str, Any]) -> float | None:
    v = (tender_schema.get("value_estimate") or {}).get("value")
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _run_sync(tender_schema: dict[str, Any], intel: dict[str, Any], gemini: GeminiService):
    context = [
        "TENDER (estimated value + financial format):\n" + tender_context(tender_schema),
        *bid_pages_parts(intel),
    ]
    return run_structured_citation_agent(
        AGENT_NAME, _SYSTEM, context, gemini, FinancialAnalysis
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

        quoted = getattr(obj, "quoted_total_inr", None)
        if quoted is None:  # fall back to the value the bidder declared at submission
            quoted = bid_doc_intel.get("quoted_amount")
        try:
            quoted = float(quoted) if quoted is not None else None
        except (TypeError, ValueError):
            quoted = None

        estimate = _estimate(tender_schema)
        abnormally_low = False
        pct_below = None
        if quoted is not None and estimate and estimate > 0:
            pct_below = round((estimate - quoted) / estimate * 100, 2)
            abnormally_low = quoted < (1 - ABNORMAL_LOW_THRESHOLD) * estimate

        # Ground the abnormally-low FAIL on the same page+quote as the extracted price.
        price_cite = next((c for c in valid if c.page_number > 0), None)
        if abnormally_low and price_cite is not None:
            valid.append(
                Citation(
                    claim=(
                        f"Quoted total ₹{quoted:,.0f} is {pct_below}% below the tender's estimated "
                        f"value ₹{estimate:,.0f} — ABNORMALLY LOW (>20% below estimate per CVC "
                        f"norms). Seek a written price justification before any award."
                    ),
                    verdict="FAIL",
                    source_doc=price_cite.source_doc,
                    page_number=price_cite.page_number,
                    quote=price_cite.quote,
                    confidence=0.95,
                    tender_clause="Estimated tender value (abnormally-low-bid check)",
                    tender_clause_page=(tender_schema.get("value_estimate") or {}).get("source_page"),
                    severity="high",
                    agent=AGENT_NAME,
                )
            )

        return AgentResult(
            agent_name=AGENT_NAME,
            status="completed",
            verdict=overall_verdict(valid),
            claims=valid,
            elapsed_ms=ms_since(start),
            rejections=rejections,
            raw_output=raw,
            data={
                "quoted_total_inr": quoted,
                "estimate_inr": estimate,
                "pct_below_estimate": pct_below,
                "abnormally_low": abnormally_low,
            },
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
