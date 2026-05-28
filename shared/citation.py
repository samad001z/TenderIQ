"""
TenderIQ — Citation contract (Phase 0 spec, NON-NEGOTIABLE).

Every AI-emitted claim MUST conform to this schema. It is passed to Gemini as a
`response_schema` (via `Citation.model_json_schema()`) so the model returns
structured, auditable output.

ENFORCEMENT (handled by the orchestrator, not this model — kept permissive here
so malformed output can be RECEIVED, then rejected + logged):
  - Reject + re-run any Citation with `page_number <= 0`
  - Reject + re-run any Citation with empty/whitespace `quote`
  - Rejections are logged to `agent_runs.rejections`

Keep `shared/citation.ts` in sync with this file by hand.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Verdict = Literal["PASS", "FAIL", "FLAG", "INFO"]
Severity = Literal["low", "medium", "high", "critical"]


class Citation(BaseModel):
    """A single auditable claim emitted by an agent, tied to verbatim source text."""

    claim: str = Field(..., description="Human-readable assertion.")
    verdict: Verdict = Field(..., description="PASS | FAIL | FLAG | INFO.")
    source_doc: str = Field(..., description="Source filename the quote is drawn from.")
    page_number: int = Field(..., description="1-indexed page number in source_doc.")
    quote: str = Field(..., description="Exact, verbatim text from the source page.")
    confidence: float = Field(..., description="Model confidence, 0.0-1.0.")
    tender_clause: Optional[str] = Field(
        None, description="Referenced tender clause, if applicable."
    )
    tender_clause_page: Optional[int] = Field(
        None, description="1-indexed page of the referenced tender clause, if applicable."
    )
    severity: Severity = Field(..., description="low | medium | high | critical.")
    agent: str = Field(..., description="Identifier of the agent that emitted this.")


class CitationList(BaseModel):
    """Wrapper for multi-citation agent output (Gemini returns a JSON object root)."""

    citations: list[Citation] = Field(default_factory=list)


def is_valid_citation(c: Citation) -> bool:
    """Orchestrator gate: True if the citation passes the hard contract checks."""
    return c.page_number > 0 and bool(c.quote.strip())


def rejection_reasons(c: Citation) -> list[str]:
    """Return human-readable reasons a citation fails the contract (for logging)."""
    reasons: list[str] = []
    if c.page_number <= 0:
        reasons.append(f"page_number <= 0 (got {c.page_number})")
    if not c.quote.strip():
        reasons.append("empty quote")
    return reasons
