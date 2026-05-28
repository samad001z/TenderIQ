"""Eligibility pre-check output (bidder capability vs tender criteria)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EligibilityVerdict(BaseModel):
    criterion: str = Field(description="The eligibility criterion being checked.")
    verdict: Literal["PASS", "FAIL", "FLAG", "INFO"] = Field(
        description="PASS = bidder clearly meets it; FAIL = clearly does not; FLAG = needs a "
        "document/manual proof; INFO = informational."
    )
    reason: str = Field(description="Short explanation referencing the bidder's profile data.")
    tender_page: int = Field(description="Page in the tender where this criterion appears.")
    quote: str = Field(description="Verbatim criterion text from the tender.")


class EligibilityReport(BaseModel):
    results: list[EligibilityVerdict]
