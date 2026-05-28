"""tender_parser_agent — Phase-3 reuse.

The tender's structured schema is parsed ONCE at ingestion time
(services.tender_parser.parse_tender_from_layout, persisted to
tenders.parsed_schema) and handed to the review pipeline as `tender_schema`.

In the per-bid pipeline this agent is therefore a thin reference step: it
confirms the schema is present and surfaces the evaluation method the
reasoning_agent will apply. It conforms to the uniform run() signature so the
orchestrator can treat all agents uniformly, but it does no LLM work and emits
no citations (the schema's own field-level source_page/quote grounding was
established in Phase 3).
"""

from __future__ import annotations

import time
from typing import Any

from agents.base import AgentResult, ms_since

AGENT_NAME = "tender_parser_agent"


async def run(
    tender_schema: dict[str, Any],
    bid_id: str,
    bid_doc_intel: dict[str, Any] | None = None,
    *,
    gemini: Any = None,
) -> AgentResult:
    start = time.perf_counter()
    schema = tender_schema or {}
    if not schema:
        return AgentResult(
            agent_name=AGENT_NAME,
            status="failed",
            verdict="INFO",
            claims=[],
            elapsed_ms=ms_since(start),
            error="Tender has not been parsed (tenders.parsed_schema is empty).",
        )
    method = schema.get("evaluation_method", "unknown")
    return AgentResult(
        agent_name=AGENT_NAME,
        status="completed",
        verdict="INFO",
        claims=[],
        elapsed_ms=ms_since(start),
        data={
            "evaluation_method": method,
            "qcbs_weights": schema.get("qcbs_weights"),
            "eligibility_criteria": len(schema.get("eligibility_criteria") or []),
            "technical_criteria": len(schema.get("technical_criteria") or []),
        },
    )
