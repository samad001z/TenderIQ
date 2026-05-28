"""Seed the 3 synthetic bidder users + submitted bids on the Phase-6 demo tender.

Idempotent: re-runs upsert profiles, reuse the existing auth users, replace any
existing bid_documents (storage + table) and re-upload the PDFs. Target tender is
the published, parsed System Integrator tender (Package B).

Run:  uv run python scripts/seed_synthetic_bids.py [tender_id]
Pre-req: scripts/generate_synthetic_bids.py has produced the 6 PDFs in
         tests/synthetic_bids/.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env.local")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # /api on path

from scripts.generate_synthetic_bids import PERSONAS  # noqa: E402
from supabase import create_client  # noqa: E402

URL = os.environ["SUPABASE_URL"]
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
PASSWORD = "TenderIQ#2026"  # matches the Phase-2 seed convention
DEFAULT_TENDER = "24941876-6111-44af-bbff-e9cd793805c9"  # System Integrator — Package B
BUCKET = "bidder-docs"
BIDS_DIR = ROOT / "tests" / "synthetic_bids"

sb = create_client(URL, KEY)
admin_auth = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}


def _find_user(email: str) -> dict | None:
    """Supabase admin: GET /auth/v1/admin/users → list; pick by email."""
    r = httpx.get(f"{URL}/auth/v1/admin/users", headers=admin_auth, params={"per_page": 200})
    r.raise_for_status()
    body = r.json()
    users = body.get("users") if isinstance(body, dict) else body
    for u in users or []:
        if (u.get("email") or "").lower() == email.lower():
            return u
    return None


def ensure_user(email: str, full_name: str) -> str:
    """Create the bidder auth user (email-confirmed) or return the existing id."""
    existing = _find_user(email)
    if existing:
        return existing["id"]
    body = {
        "email": email, "password": PASSWORD, "email_confirm": True,
        "user_metadata": {"role": "bidder", "full_name": full_name},
    }
    r = httpx.post(f"{URL}/auth/v1/admin/users", headers=admin_auth, json=body, timeout=30.0)
    r.raise_for_status()
    return r.json()["id"]


def _certifications_for(persona) -> list[str]:
    """Build the profile-level certification list from cert numbers in the persona.
    These are the public-facing labels shown on the bidder profile, not the full
    issuing-body details rendered inside the bid PDFs."""
    out: list[str] = []
    if persona.iso_9001_cert_no:
        out.append(f"ISO 9001:2015 — Cert. {persona.iso_9001_cert_no} (valid until 14-Aug-2027)")
    if persona.iso_27001_cert_no:
        out.append(f"ISO/IEC 27001:2022 — Cert. {persona.iso_27001_cert_no} (valid until 02-Mar-2027)")
    if persona.cmmi_appraisal_id:
        out.append(f"CMMI-DEV Level 5 — Appraisal {persona.cmmi_appraisal_id} (valid until 11-Oct-2027)")
    if persona.bis_licence_no:
        out.append(f"BIS Standard Mark Licence {persona.bis_licence_no} (valid until 07-Feb-2027)")
    return out


def upsert_profile(user_id: str, persona) -> None:
    sb.table("profiles").upsert({
        "id": user_id,
        "role": "bidder",
        "full_name": persona.contact_name,
        "email": persona.bidder_email,
        "org_name": persona.org_name,
        # Phase-4 bidder capability fields (used by the bidder eligibility pre-check).
        "annual_turnover": persona.turnover_inr_cr * 1_00_00_000,  # crore → ₹
        "years_in_business": persona.years_experience,
        "mse_status": False,
        "certifications": _certifications_for(persona),
        "onboarding_complete": True,
    }, on_conflict="id").execute()


def ensure_bid(tender_id: str, user_id: str, quoted_amount: int) -> str:
    """Upsert the bid row (unique on (tender_id, bidder_id)) and return its id."""
    rows = (
        sb.table("bids").select("id")
        .eq("tender_id", tender_id).eq("bidder_id", user_id).limit(1).execute().data
    )
    fresh = {
        "status": "submitted",
        "quoted_amount": quoted_amount,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        # Reset prior-run scoring so re-seeds are a true clean slate.
        "technical_score": None, "financial_score": None,
        "combined_score": None, "review_rank": None,
    }
    if rows:
        bid_id = rows[0]["id"]
        sb.table("bids").update(fresh).eq("id", bid_id).execute()
        return bid_id
    ins = sb.table("bids").insert({
        "tender_id": tender_id, "bidder_id": user_id, **fresh,
    }).execute()
    return ins.data[0]["id"]


def replace_bid_doc(bid_id: str, user_id: str, doc_type: str, local_pdf: Path) -> None:
    """Re-upload technical/financial PDF (cleans prior storage + table row).
    Uses upsert so re-seeds overwrite cleanly; the bucket's `remove` call is
    silently no-op'd in some configurations, which collides with the next upload."""
    path = f"{bid_id}/{doc_type}.pdf"
    sb.storage.from_(BUCKET).upload(
        path,
        local_pdf.read_bytes(),
        {"content-type": "application/pdf", "upsert": "true"},
    )
    sb.table("bid_documents").delete().eq("bid_id", bid_id).eq("doc_type", doc_type).execute()
    sb.table("bid_documents").insert({
        "bid_id": bid_id,
        "file_name": local_pdf.name,
        "storage_path": path,
        "doc_type": doc_type,
        "uploaded_by": user_id,
    }).execute()


def clear_prior_review_artifacts(bid_id: str) -> None:
    """Drop any agent_runs / citations / recommendations from earlier review runs.

    Phase 5 left this as a known follow-up: re-running a review would otherwise
    accumulate. The seed is a clean slate for Phase 6.
    """
    sb.table("citations").delete().eq("bid_id", bid_id).execute()
    sb.table("recommendations").delete().eq("bid_id", bid_id).execute()
    sb.table("agent_runs").delete().eq("bid_id", bid_id).execute()


def main():
    tender_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TENDER
    tender = sb.table("tenders").select("id, title, status, parse_status").eq("id", tender_id).limit(1).execute().data
    if not tender or tender[0]["status"] != "published" or tender[0]["parse_status"] != "parsed":
        raise SystemExit(f"Tender {tender_id} must be published + parsed (got {tender})")
    print(f"Seeding {len(PERSONAS)} bids on tender {tender_id} — {tender[0]['title'][:60]}…\n")

    for p in PERSONAS:
        tech_pdf = BIDS_DIR / f"{p.slug}_technical.pdf"
        fin_pdf = BIDS_DIR / f"{p.slug}_financial.pdf"
        if not (tech_pdf.exists() and fin_pdf.exists()):
            raise SystemExit(f"Missing PDFs for {p.slug} — run generate_synthetic_bids.py first")

        user_id = ensure_user(p.bidder_email, p.contact_name)
        upsert_profile(user_id, p)
        bid_id = ensure_bid(tender_id, user_id, p.quoted_total_inr)
        clear_prior_review_artifacts(bid_id)
        replace_bid_doc(bid_id, user_id, "technical", tech_pdf)
        replace_bid_doc(bid_id, user_id, "financial", fin_pdf)
        print(f"  ✔ {p.org_name:28} bid={bid_id}  quoted=₹{p.quoted_total_inr:,}")

    print(f"\nDone. To trigger the review, sign in as the tender owner and POST /api/tenders/{tender_id}/review.")


if __name__ == "__main__":
    main()
