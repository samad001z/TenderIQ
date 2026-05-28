"""E2E officer review: officer token -> POST /api/tenders/{id}/review (SSE) -> print log.

Runs the REAL pipeline (Gemini 2.5 Pro + Supabase persistence) against every
submitted bid on a tender. Requires the API running on :8000 and a parsed tender
with submitted bids.

  uv run python scripts/e2e_review.py [tender_id] [officer_email]

Default tender is the seeded published "System Integrator" tender.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env.local")
URL = os.environ["SUPABASE_URL"]
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
API = "http://127.0.0.1:8000"

tender = sys.argv[1] if len(sys.argv) > 1 else "bc0b042a-acb1-4ad9-891d-a331a19e4a6f"
email = sys.argv[2] if len(sys.argv) > 2 else "officer@tenderiq.test"

tok = httpx.post(
    f"{URL}/auth/v1/token?grant_type=password",
    headers={"apikey": KEY, "Content-Type": "application/json"},
    json={"email": email, "password": "TenderIQ#2026"},
).json()["access_token"]
auth = {"Authorization": f"Bearer {tok}"}

print(f"— review tender {tender} as {email} —")
event = None
with httpx.stream("POST", f"{API}/api/tenders/{tender}/review", headers=auth, timeout=1200) as r:
    for line in r.iter_lines():
        if line.startswith("event:"):
            event = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            d = json.loads(line.split(":", 1)[1].strip())
            if event == "review_start":
                print(f"▶ START method={d['evaluation_method']} bids={d['bids']}")
            elif event == "bid_start":
                print(f"\n── {d.get('org_name')} ({d['bid_id']}) ──")
            elif event == "agent_start":
                print(f"   ▷ {d['agent']}")
            elif event == "claim_emitted":
                print(f"      • [{d['verdict']:4}] {d['agent']:18} {d['source_doc']} p.{d['page_number']}  «{d['quote'][:50]}»")
            elif event == "agent_complete":
                rej = f" rej={d['rejections']}" if d.get("rejections") else ""
                print(f"   ◁ {d['agent']:18} {d.get('status','')} verdict={d.get('verdict','-')} claims={d.get('claims',0)}{rej} {d.get('elapsed_ms',0)}ms")
            elif event == "disagreement_detected":
                names = d.get("org_name") or ", ".join(b.get("org_name", "") for b in (d.get("bids") or []))
                print(f"   ⚠ DISAGREEMENT [{d['type']}] {names}: {d.get('note', '')}")
            elif event == "orchestrator_complete":
                print(f"\n■ COMPLETE award={d.get('recommended_award')} human_review={d.get('human_review_required')}")
                for row in d["ranking"]:
                    rank = f"L{row['rank']}" if row["rank"] else "—"
                    print(f"   {rank:>3} {row['recommended_action'] or '—':9} {row['org_name']:28} ₹{row['quoted_amount'] or 0:,.0f} [{row['bid_status']}]")
            elif event == "review_error":
                print("   ERR", d)
