"""Structured response schemas for agents that emit a number alongside citations.

Both wrap the shared Citation contract in a `citations` list (so the base
gate/rerun runner can enforce page+quote) and add one extra structured field the
reasoning_agent needs for ranking.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from pydantic import BaseModel, Field

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from shared.citation import Citation  # noqa: E402


class TechnicalAnalysis(BaseModel):
    """technical_agent output: an overall technical score + per-criterion citations."""

    technical_score: float = Field(
        description="Overall technical evaluation score 0-100 (weighted across the tender's "
        "technical criteria, using the marks/weights stated where available)."
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="One claim per technical criterion, each citing the bid page + quote.",
    )


class FinancialAnalysis(BaseModel):
    """financial_agent output: the extracted quoted total + price citations."""

    quoted_total_inr: Optional[float] = Field(
        description="The bidder's total quoted price in INR, as extracted from the financial "
        "bid / BoQ. null if no priced total could be located."
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="At least the price-line citation (page + verbatim quote of the quoted total).",
    )
