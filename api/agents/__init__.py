"""TenderIQ agent pipeline (Phase 5).

Seven agents evaluate every submitted bid against the tender schema and emit
citation-grounded claims:

  ingestion_agent       -> bid PDFs to page-labeled bid_doc_intel (Phase-3 reuse)
  tender_parser_agent   -> the tender schema (Phase-3 reuse; reference step)
  eligibility_agent     -> mandatory pre-qualification vs the bid
  technical_agent       -> technical scoring + per-criterion claims
  compliance_agent      -> PPP-MII Class-I, Integrity Pact, EMD, OEM MAF, BIS/ISO currency
  financial_agent       -> quoted price + abnormally-low (>20% below estimate) detection
  risk_agent            -> blacklist/debarment (cartel detection is cross-bid, in reasoning)

The reasoning_agent orchestrates: aggregates the specialists per bid, detects
disagreements (Technical PASS vs Compliance FAIL) and cartels, and applies the
tender's L1 / QCBS method to produce the final ranking.

Specialists (and the two reuse agents) share the signature:
    async def run(tender_schema, bid_id, bid_doc_intel, *, gemini=None) -> AgentResult
"""

from __future__ import annotations

from agents import (
    compliance_agent,
    eligibility_agent,
    financial_agent,
    ingestion_agent,
    reasoning_agent,
    risk_agent,
    technical_agent,
    tender_parser_agent,
)
from agents.base import AgentResult

# The five specialists that run (in parallel) on every bid, in display order.
SPECIALISTS = [
    eligibility_agent,
    technical_agent,
    compliance_agent,
    financial_agent,
    risk_agent,
]

__all__ = [
    "AgentResult",
    "SPECIALISTS",
    "ingestion_agent",
    "tender_parser_agent",
    "eligibility_agent",
    "technical_agent",
    "compliance_agent",
    "financial_agent",
    "risk_agent",
    "reasoning_agent",
]
