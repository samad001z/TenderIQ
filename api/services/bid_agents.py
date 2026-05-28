"""Bidder-side AI agents (Gemini 2.5 Pro, in-stack).

- check_eligibility: bidder capability profile vs the tender's eligibility criteria.
- check_compliance: reviews the bidder's OWN bid PDF against tender requirements and
  flags missing/weak items with page numbers from the bid doc (the "AI-as-friend" moment).
"""

from __future__ import annotations

import json
from typing import Any

from models.compliance import ComplianceReport
from models.eligibility import EligibilityReport
from services.gemini import GeminiService

_MAX_CHARS_PER_PAGE = 12000

_ELIG_SYSTEM = """You are TenderIQ's eligibility pre-checker for Indian government tenders.
Given a BIDDER PROFILE (JSON) and the tender's ELIGIBILITY CRITERIA (JSON list, each with
description, source_page, quote), decide for EACH criterion:
- PASS: the profile data clearly satisfies it (cite the value in `reason`).
- FAIL: the profile data clearly does NOT satisfy it (e.g. turnover/experience below the bar).
- FLAG: it requires a document or proof not derivable from the profile (e.g. a specific
  certificate, signed declaration, past-experience proof) — i.e. "you'll need to attach this".
- INFO: informational only.
For each result set `tender_page` = the criterion's source_page and `quote` = its verbatim text.
Be fair and precise. Return one result per criterion, in order."""

_COMPLY_SYSTEM = """You are TenderIQ's pre-submission compliance reviewer, acting as a HELPFUL
ally to the bidder (not a gatekeeper). You are given the bidder's OWN bid document as
page-labeled text ("=== PAGE n ===") and a summary of the tender's requirements.

Identify supporting items the tender expects (e.g. OEM/manufacturer authorization letters,
certifications named in eligibility such as CMMI/ISO, a signed CVC Integrity Pact, EMD
instrument/proof, audited financials, no-blacklisting self-declaration, local-content/MII
certificate). For each:
- PASS: present in the bid — set page_number to where it appears and quote the line.
- FAIL: required but MISSING from the bid — set page_number 0, quote "", and phrase `claim`
  helpfully ("Add an OEM authorization letter — it's required but not found in your bid.").
- FLAG: present but weak/ambiguous.
Set a sensible `category` and `severity`. Only report items relevant to THIS tender. Never invent
a page number; cite the exact page where you found supporting text."""


def check_eligibility(
    capability: dict[str, Any], criteria: list[dict[str, Any]], gemini: GeminiService | None = None
) -> dict[str, Any]:
    parts = [
        _ELIG_SYSTEM,
        "BIDDER PROFILE:\n" + json.dumps(capability, ensure_ascii=False, default=str),
        "ELIGIBILITY CRITERIA:\n" + json.dumps(criteria, ensure_ascii=False),
    ]
    resp = (gemini or GeminiService()).generate_pro(parts, EligibilityReport, temperature=0.1)
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, EligibilityReport):
        return parsed.model_dump()
    return EligibilityReport(**json.loads(resp.text)).model_dump()


def _requirements_summary(tender_schema: dict[str, Any]) -> str:
    s = tender_schema or {}
    elig = "; ".join(c.get("description", "") for c in (s.get("eligibility_criteria") or []))
    tech = "; ".join(c.get("description", "") for c in (s.get("technical_criteria") or []))
    return json.dumps(
        {
            "eligibility": elig,
            "technical": tech,
            "financial_format": (s.get("financial_format") or {}).get("value"),
            "emd": (s.get("emd_amount") or {}).get("value"),
            "pbg_percent": (s.get("pbg_percentage") or {}).get("value"),
            "integrity_pact_required": (s.get("integrity_pact_required") or {}).get("value"),
            "ppp_mii_class": s.get("ppp_mii_class"),
        },
        ensure_ascii=False,
        default=str,
    )


def check_compliance(
    layout: dict[str, Any],
    tender_schema: dict[str, Any],
    file_name: str,
    gemini: GeminiService | None = None,
) -> dict[str, Any]:
    parts: list[str] = [
        _COMPLY_SYSTEM,
        f"BID DOCUMENT: {file_name}",
        "TENDER REQUIREMENTS:\n" + _requirements_summary(tender_schema),
        "--- BID DOCUMENT PAGES ---",
    ]
    for page in layout["pages"]:
        parts.append(f"=== PAGE {page['page_number']} ===\n{(page['text'] or '')[:_MAX_CHARS_PER_PAGE]}")
    resp = (gemini or GeminiService()).generate_pro(parts, ComplianceReport, temperature=0.1)
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, ComplianceReport):
        return parsed.model_dump()
    return ComplianceReport(**json.loads(resp.text)).model_dump()
