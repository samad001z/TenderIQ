"""Officer-side review-result endpoints (Phase 6).

  GET /api/bids/{bid_id}/page-highlight  — PNG of a bid page with the citation
                                            quote highlighted in gold.
  GET /api/tenders/{id}/audit-pdf        — CAG-style signed audit PDF.
  GET /api/tenders/{id}/review-summary   — JSON snapshot of the persisted review
                                            (for re-opening the matrix after a refresh).

All officer-only; access is gated on the officer OWNING the tender (the bid's
tender for page-highlight, the tender directly for audit-pdf/summary).
"""
from __future__ import annotations

import logging
import os
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from services.audit_pdf import build_pdf as build_audit_pdf
from services.page_highlight import highlight_page
from services.supabase_client import current_officer, service_client

logger = logging.getLogger("tenderiq.review")
router = APIRouter(tags=["review"])

_BIDDER_BUCKET = "bidder-docs"


# ---------------------------------------------------------------------------
# Helpers — authorise officer access to a bid / tender
# ---------------------------------------------------------------------------
def _officer_owns_bid(sb, bid_id: str, officer_id: str) -> dict:
    rows = (
        sb.table("bids")
        .select("id, tender_id, bidder_id, quoted_amount, status")
        .eq("id", bid_id).limit(1).execute().data
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Bid not found")
    bid = rows[0]
    t = sb.table("tenders").select("id, owner_id").eq("id", bid["tender_id"]).limit(1).execute().data
    if not t or t[0]["owner_id"] != officer_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return bid


def _officer_owns_tender(sb, tender_id: str, officer_id: str) -> dict:
    rows = sb.table("tenders").select("*").eq("id", tender_id).limit(1).execute().data
    if not rows or rows[0]["owner_id"] != officer_id:
        raise HTTPException(status_code=404, detail="Tender not found")
    return rows[0]


# ---------------------------------------------------------------------------
# GET /api/bids/{bid_id}/page-highlight
# ---------------------------------------------------------------------------
@router.get("/api/bids/{bid_id}/page-highlight")
def page_highlight(
    bid_id: str,
    source_doc: str = Query(..., description="Bid document file name (matches bid_documents.file_name)."),
    page: int = Query(..., ge=1),
    quote: str = Query("", description="Verbatim quote to highlight on the page; '' draws no rectangle."),
    officer: dict = Depends(current_officer),
) -> Response:
    sb = service_client()
    _officer_owns_bid(sb, bid_id, officer["id"])
    docs = (
        sb.table("bid_documents")
        .select("storage_path, file_name, doc_type")
        .eq("bid_id", bid_id).execute().data
    )
    doc = next((d for d in docs if d["file_name"] == source_doc), None)
    if not doc:
        # Risk-agent citations cite the (non-PDF) registry — there's nothing to render.
        raise HTTPException(status_code=404, detail=f"No bid document named '{source_doc}'")

    pdf_bytes = sb.storage.from_(_BIDDER_BUCKET).download(doc["storage_path"])
    res = highlight_page(pdf_bytes, page, quote)
    return Response(
        content=res.png,
        media_type="image/png",
        headers={
            "Cache-Control": "private, max-age=300",
            "X-Highlight-Matched": "1" if res.matched else "0",
            "X-Page-Count": str(res.page_count),
        },
    )


# ---------------------------------------------------------------------------
# GET /api/tenders/{id}/review-summary  — JSON snapshot for the matrix view
# ---------------------------------------------------------------------------
def _ranking_from_db(bids: list[dict], recs_by_bid: dict[str, dict]) -> list[dict]:
    """Reconstruct the orchestrator's ranking table from persisted scores."""
    ranking: list[dict] = []
    for b in bids:
        rec = recs_by_bid.get(b["id"]) or {}
        ranking.append({
            "rank": b.get("review_rank"),
            "bid_id": b["id"],
            "org_name": b.get("org_name"),
            "quoted_amount": b.get("quoted_amount"),
            "technical_score": b.get("technical_score"),
            "financial_score": b.get("financial_score"),
            "combined_score": b.get("combined_score"),
            "recommended_action": rec.get("recommended_action"),
            "bid_status": b.get("status"),
            "needs_human_review": b.get("status") == "human_review_required",
            "summary": rec.get("summary"),
            "rationale": rec.get("rationale"),
        })
    # Sort: ranked (rank asc) first, then human-review, then others.
    def _key(r):
        if r["rank"] is not None:
            return (0, r["rank"], 0)
        if r["needs_human_review"]:
            return (1, 0, 0)
        return (2, 0, 0)
    ranking.sort(key=_key)
    return ranking


@router.get("/api/tenders/{tender_id}/review-summary")
def review_summary(tender_id: str, officer: dict = Depends(current_officer)) -> dict:
    sb = service_client()
    tender = _officer_owns_tender(sb, tender_id, officer["id"])

    bids_raw = (
        sb.table("bids")
        .select("id, bidder_id, status, quoted_amount, submitted_at, "
                "technical_score, financial_score, combined_score, review_rank")
        .eq("tender_id", tender_id).execute().data
    )
    if not bids_raw:
        return {"tender_id": tender_id, "reviewed": False, "bids": []}
    bidder_ids = list({b["bidder_id"] for b in bids_raw})
    profs = sb.table("profiles").select("id, org_name").in_("id", bidder_ids).execute().data
    org_by_id = {p["id"]: p["org_name"] for p in profs}
    for b in bids_raw:
        b["org_name"] = org_by_id.get(b["bidder_id"]) or "Unknown bidder"

    bid_ids = [b["id"] for b in bids_raw]
    recs = (
        sb.table("recommendations")
        .select("bid_id, recommended_action, overall_score, summary, rationale, generated_by, created_at")
        .in_("bid_id", bid_ids).execute().data
    )
    # If multiple recommendations exist for a bid (re-runs), keep the most recent.
    recs.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    recs_by_bid: dict[str, dict] = {}
    for r in recs:
        recs_by_bid.setdefault(r["bid_id"], r)

    cites = (
        sb.table("citations")
        .select("bid_id, agent, claim, verdict, source_doc, page_number, quote, confidence, "
                "tender_clause, tender_clause_page, severity, created_at")
        .in_("bid_id", bid_ids).order("created_at").execute().data
    )
    by_bid_agent: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for c in cites:
        by_bid_agent[c["bid_id"]][c["agent"]].append(c)

    bids_out: list[dict] = []
    for b in bids_raw:
        agents_grouped = by_bid_agent.get(b["id"], {})
        # Per-agent verdict rollup (worst-wins) on the persisted citations.
        def _roll(claims: list[dict]) -> str:
            verdicts = {c["verdict"] for c in claims}
            for v in ("FAIL", "FLAG", "PASS", "INFO"):
                if v in verdicts:
                    return v
            return "INFO"
        agents = [
            {"agent": a, "verdict": _roll(claims), "claims": claims}
            for a, claims in sorted(agents_grouped.items())
        ]
        bids_out.append({
            "bid_id": b["id"],
            "org_name": b["org_name"],
            "bid_status": b["status"],
            "quoted_amount": b["quoted_amount"],
            "technical_score": b["technical_score"],
            "financial_score": b["financial_score"],
            "combined_score": b["combined_score"],
            "review_rank": b["review_rank"],
            "recommended_action": (recs_by_bid.get(b["id"]) or {}).get("recommended_action"),
            "summary": (recs_by_bid.get(b["id"]) or {}).get("summary"),
            "rationale": (recs_by_bid.get(b["id"]) or {}).get("rationale"),
            "agents": agents,
        })

    ranking = _ranking_from_db(bids_raw, recs_by_bid)

    return {
        "tender_id": tender_id,
        "tender": {
            "id": tender_id, "title": tender.get("title"),
            "reference_no": tender.get("reference_no"),
            "ministry": tender.get("ministry"), "department": tender.get("department"),
            "estimated_value": tender.get("estimated_value"),
            "evaluation_method": (tender.get("parsed_schema") or {}).get("evaluation_method"),
            "last_reviewed_at": tender.get("last_reviewed_at"),
        },
        "reviewed": tender.get("last_reviewed_at") is not None,
        "ranking": ranking,
        "bids": bids_out,
        "recommended_award": next(
            (r["bid_id"] for r in ranking if r["recommended_action"] == "award"), None
        ),
        "human_review_required": [r["bid_id"] for r in ranking if r["needs_human_review"]],
    }


# ---------------------------------------------------------------------------
# GET /api/tenders/{id}/audit-pdf
# ---------------------------------------------------------------------------
@router.get("/api/tenders/{tender_id}/audit-pdf")
def audit_pdf(tender_id: str, officer: dict = Depends(current_officer)) -> Response:
    sb = service_client()
    tender = _officer_owns_tender(sb, tender_id, officer["id"])
    if not tender.get("last_reviewed_at"):
        raise HTTPException(status_code=409, detail="Tender has not been reviewed yet")

    # Reuse the JSON snapshot the matrix view consumes.
    summary = review_summary(tender_id, officer)

    # Gather disagreements from each bid's claim set (we surface tech-vs-comp here;
    # cartel/abnormally-low are captured in their citations and rationale fields).
    disagreements: list[dict] = []
    for b in summary["bids"]:
        if b["bid_status"] != "human_review_required":
            continue
        agents = {a["agent"]: a for a in b["agents"]}
        tech_pass = next((c for c in (agents.get("technical_agent") or {}).get("claims", []) if c["verdict"] == "PASS"), None)
        comp_fail = next((c for c in (agents.get("compliance_agent") or {}).get("claims", []) if c["verdict"] == "FAIL"), None)
        if tech_pass and comp_fail:
            disagreements.append({
                "type": "technical_vs_compliance",
                "org_name": b["org_name"],
                "note": "Technical PASS conflicts with a Compliance FAIL — orchestrator routed this bid to human review.",
                "conflicting_claims": [tech_pass, comp_fail],
            })

    bids_for_pdf = []
    for b in summary["bids"]:
        bids_for_pdf.append({
            **b,
            "agents": b["agents"],
        })

    prof_rows = (
        sb.table("profiles")
        .select("full_name, ministry, department, role")
        .eq("id", officer["id"]).limit(1).execute().data
    )
    prof = prof_rows[0] if prof_rows else {}
    payload: dict[str, Any] = {
        "officer": {
            "full_name": prof.get("full_name") or officer.get("email") or officer["id"],
            "role": "Procurement Officer",
            "ministry": prof.get("ministry"),
            "department": prof.get("department"),
        },
        "tender": summary["tender"],
        "ranking": summary["ranking"],
        "bids": bids_for_pdf,
        "disagreements": disagreements,
        "generated_at": datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M UTC"),
    }
    pdf = build_audit_pdf(payload)
    filename = f"audit-{tender_id[:8]}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
