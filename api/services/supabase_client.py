"""Supabase access for the FastAPI backend.

- `service_client()` uses the SERVICE ROLE key -> bypasses RLS (the backend is the
  privileged actor). Reused across requests.
- `current_officer` is a FastAPI dependency that validates the caller's Supabase
  access token against GoTrue and requires role == 'officer'.
"""

from __future__ import annotations

import os
from functools import lru_cache

import httpx
from fastapi import Header, HTTPException
from supabase import Client, create_client


def _url() -> str:
    return os.environ["SUPABASE_URL"]


def _service_key() -> str:
    return os.environ["SUPABASE_SERVICE_ROLE_KEY"]


@lru_cache(maxsize=1)
def service_client() -> Client:
    return create_client(_url(), _service_key())


def verify_token(token: str) -> dict | None:
    """Return the GoTrue user for a Supabase access token, or None if invalid."""
    try:
        resp = httpx.get(
            f"{_url()}/auth/v1/user",
            headers={"apikey": _service_key(), "Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
    except httpx.HTTPError:
        return None
    if resp.status_code != 200:
        return None
    return resp.json()


def _authed(authorization: str | None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def current_user(authorization: str | None = Header(default=None)) -> dict:
    """Dependency: any authenticated user. Returns {id, email, role}."""
    user = _authed(authorization)
    return {
        "id": user["id"],
        "email": user.get("email"),
        "role": (user.get("user_metadata") or {}).get("role"),
    }


def current_officer(authorization: str | None = Header(default=None)) -> dict:
    u = current_user(authorization)
    if u["role"] != "officer":
        raise HTTPException(status_code=403, detail="Officer access required")
    return u


def current_bidder(authorization: str | None = Header(default=None)) -> dict:
    u = current_user(authorization)
    if u["role"] != "bidder":
        raise HTTPException(status_code=403, detail="Bidder access required")
    return u


def signed_url(bucket: str, path: str, expires_in: int = 3600) -> str | None:
    """Create a signed URL for a private storage object (handles SDK key variants)."""
    res = service_client().storage.from_(bucket).create_signed_url(path, expires_in)
    if isinstance(res, dict):
        return res.get("signedURL") or res.get("signedUrl") or res.get("signed_url")
    return None
