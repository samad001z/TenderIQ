"""E2E bidder flow: token -> ensure bid -> eligibility (SSE) -> upload docs ->
compliance (SSE) -> submit.

  uv run python scripts/e2e_bid.py [email] [tender_id]
Uses fixtures/sample_tender.pdf as a stand-in for the technical/financial bid.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import httpx

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env.local")
URL = os.environ["SUPABASE_URL"]
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
API = "http://127.0.0.1:8000"
PDF = Path(__file__).resolve().parent.parent / "fixtures" / "sample_tender.pdf"

email = sys.argv[1] if len(sys.argv) > 1 else "bidder.orbit@tenderiq.test"
tender = sys.argv[2] if len(sys.argv) > 2 else "bc0b042a-acb1-4ad9-891d-a331a19e4a6f"

tok = httpx.post(
    f"{URL}/auth/v1/token?grant_type=password",
    headers={"apikey": KEY, "Content-Type": "application/json"},
    json={"email": email, "password": "TenderIQ#2026"},
).json()["access_token"]
auth = {"Authorization": f"Bearer {tok}"}


def stream(path: str, label: str):
    print(f"— {label} —")
    event = None
    with httpx.stream("POST", f"{API}{path}", headers=auth, timeout=600) as r:
        for line in r.iter_lines():
            if line.startswith("event:"):
                event = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                d = json.loads(line.split(":", 1)[1].strip())
                if event == "progress":
                    print("   …", d["message"])
                elif event == "result":
                    if "criterion" in d:
                        print(f"   [{d['verdict']:4}] p.{d['tender_page']}  {d['criterion'][:50]} — {d['reason'][:60]}")
                    else:
                        loc = f"p.{d['page_number']}" if d.get("page_number") else "MISSING"
                        print(f"   [{d['verdict']:4}] {d['category'][:24]:24} {loc:8} {d['claim'][:55]}")
                elif event == "done":
                    print("   DONE", d)
                elif event == "error":
                    print("   ERR", d)


bid = httpx.post(f"{API}/api/bids/ensure", headers=auth, json={"tender_id": tender}).json()
print(f"✔ {email}  bid={bid}")
bid_id = bid["bid_id"]

stream(f"/api/bids/{bid_id}/eligibility-check", "eligibility")

print("— upload technical + financial —")
for dt in ("technical", "financial"):
    with open(PDF, "rb") as f:
        r = httpx.post(
            f"{API}/api/bids/{bid_id}/documents",
            headers=auth,
            data={"doc_type": dt},
            files={"file": (f"bid_{dt}.pdf", f, "application/pdf")},
            timeout=120,
        )
    print(f"   {dt}: {r.status_code} {r.json()}")

stream(f"/api/bids/{bid_id}/compliance-check", "compliance")

print("— submit —")
print("   ", httpx.post(f"{API}/api/bids/{bid_id}/submit", headers=auth).json())
