"""End-to-end: officer token -> upload PDF -> parse (SSE) -> print parsed_schema.

  uv run python scripts/e2e_parse.py fixtures/sample_tender.pdf

Reads SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY from the loaded env (root .env.local).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import httpx

sys.stdout.reconfigure(encoding="utf-8")  # Windows console prints ₹ / ✔

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env.local")

URL = os.environ["SUPABASE_URL"]
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
API = os.environ.get("TENDERIQ_API", "http://127.0.0.1:8000")
EMAIL = os.environ.get("OFFICER_EMAIL", "officer@tenderiq.test")
PASSWORD = os.environ.get("OFFICER_PASSWORD", "TenderIQ#2026")


def main(pdf_path: str) -> None:
    # 1) officer access token
    r = httpx.post(
        f"{URL}/auth/v1/token?grant_type=password",
        headers={"apikey": KEY, "Content-Type": "application/json"},
        json={"email": EMAIL, "password": PASSWORD},
        timeout=30,
    )
    r.raise_for_status()
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    print(f"✔ signed in as {EMAIL}")

    # 2) upload
    name = os.path.basename(pdf_path)
    with open(pdf_path, "rb") as f:
        up = httpx.post(
            f"{API}/api/tenders/upload",
            headers=auth,
            files={"file": (name, f, "application/pdf")},
            timeout=120,
        )
    up.raise_for_status()
    tender_id = up.json()["tender_id"]
    print(f"✔ uploaded → tender_id {tender_id}")

    # 3) parse (SSE)
    print("— parsing —")
    event = None
    with httpx.stream("POST", f"{API}/api/tenders/{tender_id}/parse", headers=auth, timeout=600) as resp:
        for line in resp.iter_lines():
            if not line:
                continue
            if line.startswith("event:"):
                event = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = json.loads(line.split(":", 1)[1].strip())
                if event == "progress":
                    print(f"   … {data['message']}")
                elif event == "error":
                    print(f"   ✗ {data['message']}")
                elif event == "done":
                    print(f"\n=== parsed_schema (tender {data['tender_id']}, {data['page_count']} pages) ===")
                    print(json.dumps(data["schema"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fixtures/sample_tender.pdf")
