"""TenderIQ API — FastAPI entrypoint.

Phase 1: foundation only. GET /health + POST /test-gemini (proves Vertex auth).
No agent logic yet.

Run from the /api directory:
    uv run uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

# --- Load env from repo root BEFORE importing anything that reads it. ---
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env.local")
load_dotenv(ROOT / ".env")  # fallback; does not override already-set vars

# google-auth / ADC needs an absolute path to the service-account key, and the
# server may be launched from any cwd. Normalize it here once.
_gac = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if _gac and not os.path.isabs(_gac):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((ROOT / _gac).resolve())

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from services.gemini import GeminiService  # noqa: E402
from routes.tenders import router as tenders_router  # noqa: E402
from routes.bids import router as bids_router  # noqa: E402
from routes.review import router as review_router  # noqa: E402

app = FastAPI(title="TenderIQ API", version="0.1.0")

_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(tenders_router)
app.include_router(bids_router)
app.include_router(review_router)

# Lazily construct the Gemini client so /health works even if Vertex is misconfigured.
_gemini: GeminiService | None = None


def gemini() -> GeminiService:
    global _gemini
    if _gemini is None:
        _gemini = GeminiService()
    return _gemini


class HealthResponse(BaseModel):
    status: str
    service: str
    project: str | None = None
    location: str | None = None


class TestGeminiResponse(BaseModel):
    status: str
    model: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="tenderiq-api",
        project=os.environ.get("GCP_PROJECT_ID"),
        location=os.environ.get("GCP_LOCATION"),
    )


@app.post("/test-gemini", response_model=TestGeminiResponse)
def test_gemini() -> TestGeminiResponse:
    """Round-trips a structured JSON call through Gemini 2.5 Flash on Vertex.

    Proves: ADC auth works, the model is reachable in the configured region, and
    response_schema-constrained JSON comes back parseable.
    """
    prompt = "Return JSON {status: 'ready', model: 'gemini-2.5-flash'}"
    try:
        resp = gemini().generate_flash([prompt], TestGeminiResponse)
    except Exception as e:  # surface the real Vertex error to the caller
        raise HTTPException(status_code=502, detail=f"Gemini call failed: {e}") from e

    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, TestGeminiResponse):
        return parsed
    # Fallback: SDK returned text only — parse the JSON ourselves.
    try:
        return TestGeminiResponse(**json.loads(resp.text))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Unparseable Gemini output: {e}") from e
