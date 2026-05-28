"""Shared plumbing for the 7-agent officer-review pipeline.

Every agent exports:

    async def run(tender_schema, bid_id, bid_doc_intel, *, gemini=None) -> AgentResult

`AgentResult` is the uniform return type (agent_name, status, verdict, claims[],
elapsed_ms) plus the extras the orchestrator/persistence layer needs.

THE CITATION GATE (Phase 0 contract, non-negotiable):
  - Every claim MUST have page_number > 0 and a non-empty verbatim quote.
  - `run_citation_agent` enforces this: any claim that fails is REJECTED and the
    agent is RE-RUN (bounded) with a corrective instruction. Rejections are
    returned so the orchestrator can log them to agent_runs.rejections.

`bid_doc_intel` is what ingestion_agent produces — see ingestion_agent.build_intel
for the shape. It carries the bidder's documents as page-labeled text so claims
can cite (source_doc, page_number) back to a real page.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Sequence

# Import the shared Citation contract. `shared/` sits at the repo root (one level
# above /api); main.py runs with /api on sys.path, so add the parent for `shared`.
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from shared.citation import (  # noqa: E402
    Citation,
    CitationList,
    is_valid_citation,
    rejection_reasons,
)
from services.gemini import GeminiService  # noqa: E402

_MAX_CHARS_PER_PAGE = 12000


@dataclass
class AgentResult:
    """Uniform output of every agent in the review pipeline."""

    agent_name: str
    status: str  # 'completed' | 'failed'
    verdict: str  # overall agent verdict: PASS | FAIL | FLAG | INFO
    claims: list[Citation] = field(default_factory=list)
    elapsed_ms: int = 0
    # --- extras consumed by the orchestrator / persistence (not in the minimal contract) ---
    rejections: list[dict] = field(default_factory=list)  # [{claim, page_number, quote, reasons}]
    raw_output: dict | None = None  # what the model returned, per attempt — audit trail
    error: str | None = None
    data: dict | None = None  # agent-specific structured extras (intel, score, quoted_amount)

    def summary(self) -> dict[str, Any]:
        """Compact dict for SSE agent_complete payloads."""
        return {
            "agent": self.agent_name,
            "status": self.status,
            "verdict": self.verdict,
            "claims": len(self.claims),
            "rejections": len(self.rejections),
            "elapsed_ms": self.elapsed_ms,
            "error": self.error,
        }


def ms_since(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


# ---------------------------------------------------------------------------
# Bid + tender context builders (the prompt material every specialist shares)
# ---------------------------------------------------------------------------
def bid_pages_parts(intel: dict[str, Any], max_chars: int = _MAX_CHARS_PER_PAGE) -> list[str]:
    """Page-labeled bid text. The model must cite source_doc + page_number from these.

    Two docs (technical/financial) restart page numbering, so source_doc disambiguates.
    """
    parts: list[str] = [
        "--- BIDDER SUBMISSION ---",
        "Cite every claim with the exact `source_doc` (file name) and `page_number` shown "
        "below, and copy the supporting text verbatim into `quote`.",
    ]
    for doc in intel.get("documents", []):
        for pg in doc.get("pages", []):
            text = (pg.get("text") or "")[:max_chars]
            parts.append(
                f"=== DOC: {doc['file_name']} | PAGE {pg['page_number']} ===\n{text}"
            )
    return parts


def _sourced(field: dict | None) -> dict:
    field = field or {}
    return {
        "value": field.get("value"),
        "tender_page": field.get("source_page"),
        "quote": field.get("quote"),
    }


def tender_context(tender_schema: dict[str, Any]) -> str:
    """A compact, page-referenced view of the tender requirements (for tender_clause refs)."""
    s = tender_schema or {}
    return json.dumps(
        {
            "title": _sourced(s.get("title")),
            "reference_no": _sourced(s.get("reference_no")),
            "evaluation_method": s.get("evaluation_method"),
            "value_estimate_inr": _sourced(s.get("value_estimate")),
            "eligibility_criteria": s.get("eligibility_criteria") or [],
            "technical_criteria": s.get("technical_criteria") or [],
            "financial_format": _sourced(s.get("financial_format")),
            "emd_amount_inr": _sourced(s.get("emd_amount")),
            "pbg_percentage": _sourced(s.get("pbg_percentage")),
            "integrity_pact_required": _sourced(s.get("integrity_pact_required")),
            "ppp_mii_class": s.get("ppp_mii_class"),
            "ppp_mii_quote": s.get("ppp_mii_quote"),
            "ppp_mii_source_page": s.get("ppp_mii_source_page"),
            "submission_deadline": _sourced(s.get("submission_deadline")),
        },
        ensure_ascii=False,
        default=str,
    )


# ---------------------------------------------------------------------------
# Citation parsing, gating, and the rerun-on-missing-page runner
# ---------------------------------------------------------------------------
def parse_schema(resp: Any, schema: type) -> Any:
    """Return a `schema` instance from a Gemini response (parsed or raw JSON text)."""
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, schema):
        return parsed
    return schema(**json.loads(resp.text))


def parse_citation_list(resp: Any) -> list[Citation]:
    return list(parse_schema(resp, CitationList).citations)


def gate_citations(
    citations: Sequence[Citation], agent_name: str
) -> tuple[list[Citation], list[dict]]:
    """Split into (valid, rejections) per the Citation contract. Stamps `agent`."""
    valid: list[Citation] = []
    rejections: list[dict] = []
    for c in citations:
        c.agent = agent_name
        if is_valid_citation(c):
            valid.append(c)
        else:
            rejections.append(
                {
                    "claim": c.claim,
                    "page_number": c.page_number,
                    "quote": c.quote,
                    "reasons": rejection_reasons(c),
                }
            )
    return valid, rejections


def overall_verdict(claims: Sequence[Citation]) -> str:
    """Worst-wins rollup: FAIL > FLAG > PASS > INFO."""
    verdicts = {c.verdict for c in claims}
    if "FAIL" in verdicts:
        return "FAIL"
    if "FLAG" in verdicts:
        return "FLAG"
    if "PASS" in verdicts:
        return "PASS"
    return "INFO"


_RERUN_NOTE = """SOME OF YOUR CLAIMS WERE REJECTED.
The following claim(s) violated the citation contract — each claim MUST have a
page_number > 0 (the 1-indexed page in the named source_doc) AND a non-empty
`quote` copied verbatim from that page.

Re-emit the COMPLETE set of claims. For every claim you keep, ground it in a real
page_number and verbatim quote from the bidder submission above. If you cannot
ground a claim in an actual page + quote, DROP it entirely — do not fabricate a
page number or a quote.

Rejected claims:
"""


def run_structured_citation_agent(
    agent_name: str,
    system: str,
    context_parts: list[str],
    gemini: GeminiService,
    schema: type,
    *,
    max_reruns: int = 1,
    temperature: float = 0.1,
) -> tuple[Any, list[Citation], list[dict], dict]:
    """Drive an agent whose response `schema` carries a `citations: list[Citation]`.

    Gates the citations and RE-RUNS (bounded) if any claim lacks page+quote, per the
    contract. Returns (last_parsed_obj, valid_claims, all_rejections, raw_output).
    `raw_output` records each attempt for the agent_runs audit trail. Synchronous —
    wrap in asyncio.to_thread.
    """
    base_parts: list[Any] = [system, *context_parts]

    def _call(parts: list[Any]) -> tuple[Any, list[Citation], list[dict]]:
        resp = gemini.generate_pro(parts, schema, temperature=temperature)
        obj = parse_schema(resp, schema)
        cites = list(getattr(obj, "citations", []) or [])
        v, r = gate_citations(cites, agent_name)
        return obj, v, r

    obj, valid, rejections = _call(base_parts)
    raw: dict[str, Any] = {"attempt_1": obj.model_dump()}
    all_rejections = list(rejections)
    attempt = 1
    while rejections and attempt <= max_reruns:
        note = _RERUN_NOTE + json.dumps(rejections, ensure_ascii=False)
        obj, valid, rejections = _call([*base_parts, note])
        attempt += 1
        raw[f"attempt_{attempt}"] = obj.model_dump()
        all_rejections.extend(rejections)

    return obj, valid, all_rejections, raw


def run_citation_agent(
    agent_name: str,
    system: str,
    context_parts: list[str],
    gemini: GeminiService,
    *,
    max_reruns: int = 1,
    temperature: float = 0.1,
) -> tuple[list[Citation], list[dict], dict]:
    """CitationList specialisation of run_structured_citation_agent.

    Returns (valid_claims, all_rejections, raw_output).
    """
    _obj, valid, rejections, raw = run_structured_citation_agent(
        agent_name, system, context_parts, gemini, CitationList,
        max_reruns=max_reruns, temperature=temperature,
    )
    return valid, rejections, raw
