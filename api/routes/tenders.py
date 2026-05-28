"""Tender ingestion routes: upload, parse (SSE), and fetch."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import tempfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sse_starlette.sse import EventSourceResponse

from services.review_pipeline import DbPersist, stream_review
from services.supabase_client import current_officer, current_user, service_client, signed_url
from services.tender_parser import extract_layout, parse_tender_from_layout

logger = logging.getLogger("tenderiq.tenders")

router = APIRouter(prefix="/api/tenders", tags=["tenders"])

_BUCKET = "tender-docs"


def _safe_name(name: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
    return base or "tender.pdf"


def _sse(event: str, payload: dict) -> dict:
    return {"event": event, "data": json.dumps(payload)}


@router.post("/upload")
def upload_tender(file: UploadFile = File(...), officer: dict = Depends(current_officer)) -> dict:
    """Create a tender record, store the PDF in tender-docs/, return ids."""
    fname = file.filename or "tender.pdf"
    if not fname.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="A PDF file is required")
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    sb = service_client()
    ins = (
        sb.table("tenders")
        .insert(
            {
                "owner_id": officer["id"],
                "title": fname,
                "status": "draft",
                "source_file_name": fname,
                "parse_status": "pending",
            }
        )
        .execute()
    )
    tender_id = ins.data[0]["id"]
    path = f"{tender_id}/{_safe_name(fname)}"

    sb.storage.from_(_BUCKET).upload(path, data, {"content-type": "application/pdf"})
    sb.table("tenders").update({"source_storage_path": path}).eq("id", tender_id).execute()
    sb.table("tender_documents").insert(
        {
            "tender_id": tender_id,
            "file_name": fname,
            "storage_path": path,
            "doc_type": "rfp",
            "uploaded_by": officer["id"],
        }
    ).execute()

    return {"tender_id": tender_id, "storage_path": path, "file_name": fname}


@router.post("/{tender_id}/parse")
async def parse_tender(tender_id: str, officer: dict = Depends(current_officer)):
    """Async ingestion with live SSE progress, persisting layout + schema."""
    officer_id = officer["id"]

    async def gen():
        sb = service_client()
        try:
            res = sb.table("tenders").select("*").eq("id", tender_id).limit(1).execute()
            row = res.data[0] if res.data else None
            if not row or row["owner_id"] != officer_id:
                yield _sse("error", {"message": "Tender not found"})
                return
            path = row.get("source_storage_path")
            if not path:
                yield _sse("error", {"message": "No uploaded file for this tender"})
                return

            yield _sse("progress", {"stage": "downloading", "message": "Downloading PDF from storage…"})
            sb.table("tenders").update({"parse_status": "parsing", "parse_error": None}).eq(
                "id", tender_id
            ).execute()
            pdf_bytes = await asyncio.to_thread(
                lambda: sb.storage.from_(_BUCKET).download(path)
            )

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(pdf_bytes)
            tmp.close()
            try:
                yield _sse("progress", {"stage": "reading", "message": "Reading pages with PyMuPDF…"})
                layout = await asyncio.to_thread(extract_layout, tmp.name)
                yield _sse(
                    "progress",
                    {
                        "stage": "extracting",
                        "message": f"Extracting tender schema from {layout['page_count']} pages…",
                    },
                )
                schema = await asyncio.to_thread(parse_tender_from_layout, layout)
            finally:
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass

            method = schema.get("evaluation_method", "unknown")
            n_elig = len(schema.get("eligibility_criteria") or [])
            yield _sse(
                "progress",
                {"stage": "detecting", "message": f"Detected evaluation method: {method} · {n_elig} eligibility criteria."},
            )

            update = {
                "parsed_layout": layout,
                "parsed_schema": schema,
                "parse_status": "parsed",
                "parse_error": None,
                "parsed_at": datetime.now(timezone.utc).isoformat(),
                "title": (schema.get("title") or {}).get("value") or row["title"],
                "reference_no": (schema.get("reference_no") or {}).get("value") or None,
                "ministry": (schema.get("ministry") or {}).get("value") or None,
                "department": (schema.get("department") or {}).get("value") or None,
                "estimated_value": (schema.get("value_estimate") or {}).get("value"),
                "emd_amount": (schema.get("emd_amount") or {}).get("value"),
            }
            await asyncio.to_thread(
                lambda: sb.table("tenders").update(update).eq("id", tender_id).execute()
            )
            url = await asyncio.to_thread(signed_url, _BUCKET, path, 3600)
            yield _sse(
                "done",
                {
                    "tender_id": tender_id,
                    "schema": schema,
                    "signed_url": url,
                    "page_count": layout["page_count"],
                },
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("Tender parse failed")
            try:
                sb.table("tenders").update(
                    {"parse_status": "failed", "parse_error": str(e)[:500]}
                ).eq("id", tender_id).execute()
            except Exception:
                pass
            yield _sse("error", {"message": f"Parse failed: {e}"})

    return EventSourceResponse(gen())


@router.post("/{tender_id}/review")
async def review_tender(tender_id: str, officer: dict = Depends(current_officer)):
    """Run the 7-agent pipeline over every submitted bid; stream live SSE events.

    Events: review_start, bid_start, agent_start, claim_emitted, agent_complete,
    disagreement_detected, orchestrator_complete (review_error on failure). Persists
    every claim to citations, every agent execution to agent_runs, and the final
    verdicts to recommendations.
    """
    officer_id = officer["id"]

    async def gen():
        sb = service_client()
        try:
            res = sb.table("tenders").select("id, owner_id, parsed_schema").eq("id", tender_id).limit(1).execute()
            row = res.data[0] if res.data else None
            if not row or row["owner_id"] != officer_id:
                yield _sse("review_error", {"message": "Tender not found"})
                return
            schema = row.get("parsed_schema")
            if not schema:
                yield _sse("review_error", {"message": "Tender has not been parsed yet."})
                return

            # The bids to evaluate: submitted (and any left mid-review).
            bids = (
                sb.table("bids")
                .select("id, bidder_id, status")
                .eq("tender_id", tender_id)
                .in_("status", ["submitted", "under_review"])
                .execute()
                .data
            )
            if not bids:
                yield _sse("review_error", {"message": "No submitted bids to review."})
                return

            prof_ids = list({b["bidder_id"] for b in bids})
            profs = sb.table("profiles").select("id, org_name").in_("id", prof_ids).execute().data
            org_by_id = {p["id"]: p["org_name"] for p in profs}
            thin = [
                {"bid_id": b["id"], "tender_id": tender_id, "org_name": org_by_id.get(b["bidder_id"])}
                for b in bids
            ]

            persist = DbPersist(sb, os.environ.get("GEMINI_PRO_MODEL", "gemini-2.5-pro"))
            async for event, payload in stream_review(
                schema, thin, persist=persist, tender_id=tender_id
            ):
                yield _sse(event, payload)
        except Exception as e:  # noqa: BLE001
            logger.exception("Tender review failed")
            yield _sse("review_error", {"message": f"Review failed: {e}"})

    return EventSourceResponse(gen())


@router.get("/{tender_id}/file-url")
def tender_file_url(tender_id: str, user: dict = Depends(current_user)) -> dict:
    """Signed URL for the tender PDF — any authed user if the tender is published, else owner only."""
    sb = service_client()
    res = (
        sb.table("tenders")
        .select("status, owner_id, source_storage_path")
        .eq("id", tender_id)
        .limit(1)
        .execute()
    )
    row = res.data[0] if res.data else None
    if not row or not row.get("source_storage_path"):
        raise HTTPException(status_code=404, detail="Not found")
    if row["status"] != "published" and row["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    return {"signed_url": signed_url("tender-docs", row["source_storage_path"])}


@router.get("/{tender_id}")
def get_tender(tender_id: str, officer: dict = Depends(current_officer)) -> dict:
    sb = service_client()
    res = sb.table("tenders").select("*").eq("id", tender_id).limit(1).execute()
    row = res.data[0] if res.data else None
    if not row or row["owner_id"] != officer["id"]:
        raise HTTPException(status_code=404, detail="Tender not found")
    url = signed_url(_BUCKET, row["source_storage_path"]) if row.get("source_storage_path") else None
    keys = (
        "id", "title", "reference_no", "ministry", "department", "status",
        "estimated_value", "emd_amount", "source_file_name", "parse_status", "parsed_at",
    )
    return {
        "tender": {k: row.get(k) for k in keys},
        "schema": row.get("parsed_schema"),
        "signed_url": url,
    }
