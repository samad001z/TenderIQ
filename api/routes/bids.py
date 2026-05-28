"""Bidder-side routes: ensure bid, eligibility pre-check (SSE), upload docs,
compliance check (SSE), submit."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import tempfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from services.bid_agents import check_compliance, check_eligibility
from services.supabase_client import current_bidder, service_client
from services.tender_parser import extract_layout

logger = logging.getLogger("tenderiq.bids")
router = APIRouter(prefix="/api/bids", tags=["bids"])

_BUCKET = "bidder-docs"
_DOC_TYPES = {"technical", "financial"}


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "bid.pdf"


def _sse(event: str, payload: dict) -> dict:
    return {"event": event, "data": json.dumps(payload)}


def _bid_or_404(sb, bid_id: str, bidder_id: str) -> dict:
    res = sb.table("bids").select("*").eq("id", bid_id).limit(1).execute()
    row = res.data[0] if res.data else None
    if not row or row["bidder_id"] != bidder_id:
        raise HTTPException(status_code=404, detail="Bid not found")
    return row


class EnsureBidBody(BaseModel):
    tender_id: str


@router.post("/ensure")
def ensure_bid(body: EnsureBidBody, bidder: dict = Depends(current_bidder)) -> dict:
    """Get-or-create the bidder's draft bid for a published tender."""
    sb = service_client()
    t = sb.table("tenders").select("id, status").eq("id", body.tender_id).limit(1).execute().data
    if not t or t[0]["status"] != "published":
        raise HTTPException(status_code=404, detail="Tender not available")
    existing = (
        sb.table("bids")
        .select("id, status")
        .eq("tender_id", body.tender_id)
        .eq("bidder_id", bidder["id"])
        .limit(1)
        .execute()
        .data
    )
    if existing:
        return {"bid_id": existing[0]["id"], "status": existing[0]["status"]}
    ins = (
        sb.table("bids")
        .insert({"tender_id": body.tender_id, "bidder_id": bidder["id"], "status": "draft"})
        .execute()
    )
    return {"bid_id": ins.data[0]["id"], "status": "draft"}


@router.post("/{bid_id}/eligibility-check")
async def eligibility_check(bid_id: str, bidder: dict = Depends(current_bidder)):
    bidder_id = bidder["id"]

    async def gen():
        sb = service_client()
        try:
            bid = _bid_or_404(sb, bid_id, bidder_id)
            tender = (
                sb.table("tenders").select("parsed_schema").eq("id", bid["tender_id"]).limit(1).execute().data
            )
            schema = (tender[0]["parsed_schema"] if tender else None) or {}
            criteria = schema.get("eligibility_criteria") or []
            prof = (
                sb.table("profiles")
                .select("org_name, annual_turnover, years_in_business, mse_status, certifications, gst_number, pan_number")
                .eq("id", bidder_id)
                .limit(1)
                .execute()
                .data
            )
            p = prof[0] if prof else {}
            capability = {
                "organisation": p.get("org_name"),
                "annual_turnover_inr": p.get("annual_turnover"),
                "years_in_business": p.get("years_in_business"),
                "is_micro_small_enterprise": p.get("mse_status"),
                "certifications": p.get("certifications"),
                "gst": p.get("gst_number"),
                "pan": p.get("pan_number"),
            }

            yield _sse("progress", {"message": "Loading your company profile…"})
            if not criteria:
                yield _sse("done", {"total": 0, "fail": 0})
                return
            yield _sse("progress", {"message": f"Checking {len(criteria)} eligibility criteria…"})

            report = await asyncio.to_thread(check_eligibility, capability, criteria)
            results = report.get("results") or []
            for r in results:
                yield _sse("result", r)
                await asyncio.sleep(0.35)  # progressive reveal
            fails = sum(1 for r in results if r.get("verdict") == "FAIL")
            yield _sse("done", {"total": len(results), "fail": fails})
        except Exception as e:  # noqa: BLE001
            logger.exception("eligibility check failed")
            yield _sse("error", {"message": f"Eligibility check failed: {e}"})

    return EventSourceResponse(gen())


@router.post("/{bid_id}/documents")
def upload_bid_doc(
    bid_id: str,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    bidder: dict = Depends(current_bidder),
) -> dict:
    if doc_type not in _DOC_TYPES:
        raise HTTPException(status_code=400, detail="doc_type must be 'technical' or 'financial'")
    fname = file.filename or f"{doc_type}.pdf"
    if not fname.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="A PDF file is required")
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    sb = service_client()
    _bid_or_404(sb, bid_id, bidder["id"])
    path = f"{bid_id}/{doc_type}.pdf"
    try:
        sb.storage.from_(_BUCKET).remove([path])  # allow re-upload
    except Exception:
        pass
    sb.storage.from_(_BUCKET).upload(path, data, {"content-type": "application/pdf"})
    # one bid_document per (bid, doc_type)
    sb.table("bid_documents").delete().eq("bid_id", bid_id).eq("doc_type", doc_type).execute()
    sb.table("bid_documents").insert(
        {
            "bid_id": bid_id,
            "file_name": fname,
            "storage_path": path,
            "doc_type": doc_type,
            "uploaded_by": bidder["id"],
        }
    ).execute()
    return {"ok": True, "doc_type": doc_type, "file_name": fname}


@router.post("/{bid_id}/compliance-check")
async def compliance_check(bid_id: str, bidder: dict = Depends(current_bidder)):
    bidder_id = bidder["id"]

    async def gen():
        sb = service_client()
        try:
            bid = _bid_or_404(sb, bid_id, bidder_id)
            docs = (
                sb.table("bid_documents")
                .select("file_name, storage_path, doc_type")
                .eq("bid_id", bid_id)
                .execute()
                .data
            )
            technical = next((d for d in docs if d["doc_type"] == "technical"), None)
            if not technical:
                yield _sse("error", {"message": "Upload your technical bid first."})
                return
            tender = (
                sb.table("tenders").select("parsed_schema").eq("id", bid["tender_id"]).limit(1).execute().data
            )
            schema = (tender[0]["parsed_schema"] if tender else None) or {}

            yield _sse("progress", {"message": "Downloading your technical bid…"})
            pdf_bytes = await asyncio.to_thread(
                lambda: sb.storage.from_(_BUCKET).download(technical["storage_path"])
            )
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(pdf_bytes)
            tmp.close()
            try:
                yield _sse("progress", {"message": "Reading your bid…"})
                layout = await asyncio.to_thread(extract_layout, tmp.name)
                yield _sse(
                    "progress",
                    {"message": f"Reviewing {layout['page_count']} pages against tender requirements…"},
                )
                report = await asyncio.to_thread(
                    check_compliance, layout, schema, technical["file_name"]
                )
            finally:
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass

            findings = report.get("findings") or []
            for f in findings:
                yield _sse("result", f)
                await asyncio.sleep(0.35)
            missing = sum(1 for f in findings if f.get("verdict") == "FAIL")
            yield _sse("done", {"total": len(findings), "missing": missing})
        except Exception as e:  # noqa: BLE001
            logger.exception("compliance check failed")
            yield _sse("error", {"message": f"Compliance check failed: {e}"})

    return EventSourceResponse(gen())


@router.post("/{bid_id}/submit")
def submit_bid(bid_id: str, bidder: dict = Depends(current_bidder)) -> dict:
    sb = service_client()
    _bid_or_404(sb, bid_id, bidder["id"])
    docs = sb.table("bid_documents").select("doc_type").eq("bid_id", bid_id).execute().data
    types = {d["doc_type"] for d in docs}
    if not _DOC_TYPES.issubset(types):
        raise HTTPException(status_code=400, detail="Upload both a technical and a financial bid first")
    sb.table("bids").update(
        {"status": "submitted", "submitted_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", bid_id).execute()
    return {"status": "submitted"}
