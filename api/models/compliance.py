"""Pre-submission compliance check output — flags issues in the bidder's OWN bid docs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ComplianceFinding(BaseModel):
    claim: str = Field(description="The compliance observation, phrased helpfully for the bidder.")
    verdict: Literal["PASS", "FAIL", "FLAG", "INFO"] = Field(
        description="PASS = present & correct; FAIL = required item missing; FLAG = present but "
        "weak/needs attention; INFO = note."
    )
    category: str = Field(description="e.g. 'OEM authorization', 'Certificate', 'Signature', 'EMD'.")
    source_doc: str = Field(description="Bid document filename the finding refers to.")
    page_number: int = Field(description="Page in the bid doc; 0 if the item is MISSING entirely.")
    quote: str = Field(description="Verbatim supporting text from the bid doc; '' if missing.")
    severity: Literal["low", "medium", "high", "critical"]


class ComplianceReport(BaseModel):
    findings: list[ComplianceFinding]
