"""compliance_agent — statutory/process compliance of the SUBMITTED bid.

Checks the bid against the mandatory procurement-compliance items and emits a
page-cited Citation for each:
  - PPP-MII (Make-in-India) Class-I local-content declaration/certificate, when the
    tender restricts to Class-I (>=50% local content).
  - CVC Integrity Pact — signed, when required.
  - EMD (Earnest Money Deposit) — instrument/proof for the tendered amount.
  - OEM / manufacturer authorization letters (MAF) for quoted equipment.
  - BIS / ISO certifications named by the tender, and whether they are CURRENT
    (not expired as of the submission deadline).

FAIL = required but missing/expired/unsigned; FLAG = present but weak/ambiguous;
PASS = present and in order. Every claim cites a real bid page + verbatim quote.
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

AGENT_NAME = "compliance_agent"

_SYSTEM = """You are TenderIQ's Compliance Evaluator, an expert in Indian public-procurement
statutory requirements (GFR 2017, CVC guidelines, PPP-MII Order 2017 as amended, BIS/ISO).
You are given the tender requirements and a bidder's SUBMITTED bid as page-labeled text.

Evaluate the bid against EACH of these mandatory items that apply to this tender and emit
one claim per item:
1. PPP-MII Class-I — if the tender's ppp_mii_class is "I", the bid MUST contain a
   self-certification / certificate of >=50% local content. PASS if present, FAIL if absent.
2. CVC Integrity Pact — if integrity_pact_required is true, the bid MUST contain the signed
   Integrity Pact. FAIL if missing or unsigned.
3. EMD — the bid must enclose an EMD instrument/proof (BG / DD / online) for the tendered EMD
   amount, or a valid MSE/exemption claim. FAIL if neither is present.
4. OEM / Manufacturer Authorization (MAF) — for quoted branded equipment, an OEM authorization
   letter must be enclosed. FLAG/FAIL if expected but missing.
5. BIS / ISO certifications named in the tender — present AND current (not expired before the
   submission deadline). FAIL if missing; FLAG if present but expired/expiring.

HARD RULES (citation contract):
- page_number MUST be the 1-indexed page in `source_doc` where evidence appears; `quote` MUST be
  verbatim from that page. For an item judged MISSING you still cannot fabricate a page — instead
  cite the bid's index/checklist/cover page where the item should have been listed and quote that
  line as evidence of its absence. Never invent a page number or quote.
- source_doc MUST be the exact file name from the "=== DOC: ... | PAGE n ===" headers.
- Set tender_clause to the requirement and tender_clause_page to its tender page when known.
- severity: missing Integrity Pact / EMD / Class-I cert = 'critical' or 'high'; expired cert =
  'high'; weak/ambiguous = 'medium'; in order = 'low'. confidence in [0,1].
- Only emit claims for items RELEVANT to this tender."""


def _run_sync(tender_schema: dict[str, Any], intel: dict[str, Any], gemini: GeminiService):
    context = [
        "TENDER REQUIREMENTS:\n" + tender_context(tender_schema),
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
