"""ingestion_agent — turns a bid's stored PDFs into `bid_doc_intel`.

Reuses the Phase-3 PyMuPDF text extractor (services.tender_parser.extract_layout).
This is the data step the five specialist agents consume: it downloads each
bid_document from the bidder-docs bucket, extracts page-labeled text, and bundles
it with the bidder identity + quoted amount the orchestrator needs.

`bid_doc_intel` shape:
    {
      "bid_id", "tender_id", "bidder_id", "org_name",
      "quoted_amount": float | None,        # from bids.quoted_amount (may be None)
      "documents": [
        {"doc_type", "file_name", "page_count",
         "pages": [{"page_number": int, "text": str}, ...]}
      ],
    }
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import time
from typing import Any

from agents.base import AgentResult, ms_since
from services.supabase_client import service_client
from services.tender_parser import extract_layout

AGENT_NAME = "ingestion_agent"
_BUCKET = "bidder-docs"


def build_intel(bid_id: str) -> dict[str, Any]:
    """Download + extract every document for a bid. Synchronous (wrap in to_thread)."""
    sb = service_client()
    bid_rows = (
        sb.table("bids")
        .select("id, tender_id, bidder_id, quoted_amount")
        .eq("id", bid_id)
        .limit(1)
        .execute()
        .data
    )
    if not bid_rows:
        raise ValueError(f"Bid {bid_id} not found")
    bid = bid_rows[0]

    prof = (
        sb.table("profiles").select("org_name").eq("id", bid["bidder_id"]).limit(1).execute().data
    )
    org_name = (prof[0]["org_name"] if prof else None) or "Unknown bidder"

    docs = (
        sb.table("bid_documents")
        .select("file_name, storage_path, doc_type")
        .eq("bid_id", bid_id)
        .execute()
        .data
    )

    documents: list[dict[str, Any]] = []
    for d in docs:
        pdf_bytes = sb.storage.from_(_BUCKET).download(d["storage_path"])
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        try:
            tmp.write(pdf_bytes)
            tmp.close()
            layout = extract_layout(tmp.name)
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
        documents.append(
            {
                "doc_type": d["doc_type"],
                "file_name": d["file_name"],
                "page_count": layout["page_count"],
                "pages": [
                    {"page_number": p["page_number"], "text": p["text"]} for p in layout["pages"]
                ],
            }
        )

    return {
        "bid_id": bid_id,
        "tender_id": bid["tender_id"],
        "bidder_id": bid["bidder_id"],
        "org_name": org_name,
        "quoted_amount": bid.get("quoted_amount"),
        "documents": documents,
    }


async def run(
    tender_schema: dict[str, Any],
    bid_id: str,
    bid_doc_intel: dict[str, Any] | None = None,
    *,
    gemini: Any = None,
) -> AgentResult:
    """Produce bid_doc_intel for `bid_id`. The result's `.data` IS the intel.

    Unlike the specialists, ingestion PRODUCES bid_doc_intel rather than consuming
    it — so an incoming `bid_doc_intel` is accepted (and reused) but optional.
    """
    start = time.perf_counter()
    try:
        intel = bid_doc_intel or await asyncio.to_thread(build_intel, bid_id)
        n_docs = len(intel.get("documents", []))
        n_pages = sum(d.get("page_count", 0) for d in intel.get("documents", []))
        return AgentResult(
            agent_name=AGENT_NAME,
            status="completed",
            verdict="INFO",
            claims=[],
            elapsed_ms=ms_since(start),
            data=intel,
            raw_output={"documents": n_docs, "pages": n_pages, "org_name": intel.get("org_name")},
        )
    except Exception as e:  # noqa: BLE001
        return AgentResult(
            agent_name=AGENT_NAME,
            status="failed",
            verdict="INFO",
            claims=[],
            elapsed_ms=ms_since(start),
            error=str(e),
        )
