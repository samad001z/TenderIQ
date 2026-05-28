"""TenderSchema — the structured extraction target for the Tender Parser Agent.

Every field carries its `source_page` (1-indexed; 0 if not found in the document)
and a verbatim `quote`, so the officer UI can jump the PDF to the exact page and
the extraction is auditable — same philosophy as the Citation contract.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

EvaluationMethod = Literal["L1", "QCBS", "LCS", "unknown"]
MIIClass = Literal["I", "II", "none", "unknown"]


class SourcedText(BaseModel):
    value: str = Field(description="Extracted value; empty string if not present.")
    source_page: int = Field(description="1-indexed page; 0 if not found.")
    quote: str = Field(description="Verbatim supporting text; empty if not found.")


class SourcedNumber(BaseModel):
    value: Optional[float] = Field(description="Numeric value (INR/percent/etc); null if not present.")
    source_page: int = Field(description="1-indexed page; 0 if not found.")
    quote: str = Field(description="Verbatim supporting text; empty if not found.")


class SourcedBool(BaseModel):
    value: bool
    source_page: int = Field(description="1-indexed page; 0 if not found.")
    quote: str = Field(description="Verbatim supporting text; empty if not found.")


class EligibilityCriterion(BaseModel):
    description: str = Field(description="A single mandatory eligibility requirement.")
    source_page: int
    quote: str


class TechnicalCriterion(BaseModel):
    description: str = Field(description="A technical evaluation criterion.")
    weight: Optional[float] = Field(description="Marks/weight assigned, if stated; else null.")
    source_page: int
    quote: str


class QCBSWeights(BaseModel):
    technical: float = Field(description="Technical weight %, 0 if N/A.")
    financial: float = Field(description="Financial weight %, 0 if N/A.")
    source_page: int


class TenderSchema(BaseModel):
    title: SourcedText
    reference_no: SourcedText
    ministry: SourcedText
    department: SourcedText
    value_estimate: SourcedNumber

    evaluation_method: EvaluationMethod = Field(
        description="L1 = lowest price; QCBS = quality & cost based; LCS = least cost selection; unknown."
    )
    evaluation_method_source_page: int
    evaluation_method_quote: str
    qcbs_weights: QCBSWeights = Field(
        description="Technical/financial split for QCBS; zeros if not QCBS."
    )

    eligibility_criteria: list[EligibilityCriterion]
    technical_criteria: list[TechnicalCriterion]

    financial_format: SourcedText = Field(description="How the price/BoQ must be quoted.")
    emd_amount: SourcedNumber = Field(description="Earnest Money Deposit amount (INR).")
    pbg_percentage: SourcedNumber = Field(description="Performance Bank Guarantee, as a percentage.")
    integrity_pact_required: SourcedBool
    ppp_mii_class: MIIClass = Field(
        description="Public Procurement (Preference to Make in India) local-supplier class."
    )
    ppp_mii_source_page: int
    ppp_mii_quote: str
    submission_deadline: SourcedText = Field(description="Bid submission deadline (date/time as written).")
