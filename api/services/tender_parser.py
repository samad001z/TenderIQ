"""Tender Parser Agent — extracts a structured TenderSchema from a tender PDF.

Pipeline:
  1. extract_layout(pdf) -> per-page text + detected tables (PyMuPDF). This is the
     raw grounding we persist to tenders.parsed_layout.
  2. parse_tender_from_layout(layout) -> feeds page-labeled text to Gemini 2.5 Pro
     with response_schema=TenderSchema, returning the structured tenders.parsed_schema.

CPPP tenders are born-digital, so labeled text extraction is accurate and cheap
(handles 60 pages comfortably). Image rendering (pdf_pages) stays available for
scanned docs / the evaluator agents.
"""

from __future__ import annotations

import logging
from typing import Any

import fitz  # PyMuPDF

from models.tender_schema import TenderSchema
from services.gemini import GeminiService

logger = logging.getLogger("tenderiq.tender_parser")

# Guard against a pathological page dumping the whole prompt budget.
_MAX_CHARS_PER_PAGE = 16000

_SYSTEM = """You are TenderIQ's Tender Parser, an expert in Indian government \
procurement (GFR 2017, CPPP/GeM, CVC integrity pact, PPP-MII order).

You are given a tender document as page-labeled text. Each page begins with a line \
"=== PAGE n ===". Extract a structured schema.

HARD RULES:
- For every field set source_page to the 1-indexed page number where you found it, \
and quote with the exact verbatim text from that page that supports it.
- If a field is genuinely absent, use value "" (or null for numbers), source_page 0, \
and quote "". Never invent a page number or a quote.
- quotes must be copied character-for-character from the page text. Do not paraphrase.

DOMAIN GUIDANCE:
- evaluation_method: L1 = lowest priced technically-qualified bid; QCBS = combined \
quality-and-cost score with weights; LCS = least cost among those meeting a quality \
threshold. If QCBS, fill qcbs_weights (technical % + financial %); otherwise zeros.
- eligibility_criteria: each MANDATORY pre-qualification requirement (turnover, past \
experience, registrations, certifications) as a separate item.
- technical_criteria: scored technical evaluation parameters; include marks/weight if stated.
- emd_amount: Earnest Money Deposit in INR. pbg_percentage: Performance Bank/Security \
Guarantee as a percent. integrity_pact_required: whether a CVC integrity pact must be signed.
- ppp_mii_class: the Make-in-India local-supplier class the tender restricts to \
(Class I local content >=50%, Class II 20-50%, else 'none' if open, 'unknown' if unclear).
- submission_deadline: the bid submission closing date/time, as written.
"""


def extract_layout(pdf_path: str) -> dict[str, Any]:
    """Per-page text + detected tables — the raw grounding (tenders.parsed_layout)."""
    doc = fitz.open(pdf_path)
    try:
        pages: list[dict[str, Any]] = []
        for index, page in enumerate(doc):
            text = page.get_text("text") or ""
            tables: list[list[list[str | None]]] = []
            try:
                found = page.find_tables()
                for table in found.tables:
                    tables.append(table.extract())
            except Exception:  # find_tables is best-effort
                pass
            pages.append({"page_number": index + 1, "text": text, "tables": tables})
        return {"page_count": len(pages), "pages": pages}
    finally:
        doc.close()


def _build_parts(layout: dict[str, Any]) -> list[str]:
    parts: list[str] = [_SYSTEM]
    for page in layout["pages"]:
        text = (page["text"] or "")[:_MAX_CHARS_PER_PAGE]
        parts.append(f"=== PAGE {page['page_number']} ===\n{text}")
    return parts


def parse_tender_from_layout(
    layout: dict[str, Any], gemini: GeminiService | None = None
) -> dict[str, Any]:
    """Run the extraction. Returns the TenderSchema as a dict (tenders.parsed_schema)."""
    parts = _build_parts(layout)
    service = gemini or GeminiService()
    resp = service.generate_pro(parts, TenderSchema, temperature=0.1)

    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, TenderSchema):
        return parsed.model_dump()
    # Fallback: parse the raw JSON text.
    import json

    return TenderSchema(**json.loads(resp.text)).model_dump()
