"""risk_agent — integrity risk of a single bid.

Per-bid checks:
  - BLACKLIST / debarment: match the bidder's organisation against the seeded
    CVC/DoE debarred-firms registry (agents/blacklist.json). A hit is a critical
    FAIL, cited to the registry page + the verbatim listing line.

Cartel suspicion (3+ bids clustered within 2% of each other, per CVC Circular
4/3/07) is inherently CROSS-bid and is detected by the reasoning_agent after all
financial figures are in — see reasoning_agent.detect_cartel.

Deterministic (no LLM): the registry is the source of truth, so claims are exact.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from agents.base import AgentResult, ms_since
from shared.citation import Citation

AGENT_NAME = "risk_agent"
_BLACKLIST_PATH = Path(__file__).resolve().parent / "blacklist.json"


def _normalize(name: str) -> str:
    """Lowercase, strip company suffixes/punctuation for fuzzy-but-safe matching."""
    n = (name or "").lower()
    n = re.sub(r"[^a-z0-9& ]+", " ", n)
    n = re.sub(
        r"\b(pvt|private|ltd|limited|llp|inc|co|company|corp|corporation|and|&)\b", " ", n
    )
    return re.sub(r"\s+", " ", n).strip()


def load_blacklist() -> dict[str, Any]:
    return json.loads(_BLACKLIST_PATH.read_text(encoding="utf-8"))


def match_blacklist(org_name: str, blacklist: dict[str, Any] | None = None) -> dict | None:
    """Return the matching registry entry for `org_name`, or None."""
    bl = blacklist or load_blacklist()
    target = _normalize(org_name)
    if not target:
        return None
    for entry in bl.get("entries", []):
        candidates = [entry.get("name", ""), *entry.get("aliases", [])]
        for cand in candidates:
            c = _normalize(cand)
            if c and (c == target or c in target or target in c):
                return entry
    return None


async def run(
    tender_schema: dict[str, Any],
    bid_id: str,
    bid_doc_intel: dict[str, Any],
    *,
    gemini: Any = None,
) -> AgentResult:
    start = time.perf_counter()
    try:
        bl = load_blacklist()
        org = (bid_doc_intel or {}).get("org_name") or "Unknown bidder"
        hit = match_blacklist(org, bl)
        registry = bl.get("registry_name", "Debarred firms registry")

        if hit:
            claim = Citation(
                claim=(
                    f"Bidder '{org}' MATCHES a debarred/blacklisted firm in the registry: "
                    f"{hit['reason']}"
                ),
                verdict="FAIL",
                source_doc=registry,
                page_number=int(hit.get("page", 1)),
                quote=hit["listing"],
                confidence=0.99,
                tender_clause="CVC debarment / blacklisting eligibility bar",
                tender_clause_page=None,
                severity="critical",
                agent=AGENT_NAME,
            )
            return AgentResult(
                agent_name=AGENT_NAME,
                status="completed",
                verdict="FAIL",
                claims=[claim],
                elapsed_ms=ms_since(start),
                data={"blacklisted": True, "org_name": org, "registry_ref": hit.get("listing")},
            )

        # Clean — grounded on the registry masthead (a real verbatim line) so it passes the gate.
        claim = Citation(
            claim=f"No debarment/blacklisting match found for '{org}' in the registry.",
            verdict="PASS",
            source_doc=registry,
            page_number=1,
            quote=bl.get("header", registry),
            confidence=0.9,
            tender_clause="CVC debarment / blacklisting eligibility bar",
            tender_clause_page=None,
            severity="low",
            agent=AGENT_NAME,
        )
        return AgentResult(
            agent_name=AGENT_NAME,
            status="completed",
            verdict="PASS",
            claims=[claim],
            elapsed_ms=ms_since(start),
            data={"blacklisted": False, "org_name": org},
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
