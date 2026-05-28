"""reasoning_agent — the orchestrator.

Unlike the specialists it does not emit page-grounded claims of its own (it
aggregates the specialists' already-cited claims), so it is not a run()-shaped
agent. It exposes three pure functions the review pipeline drives:

  synthesize_bid(...)   -> per-bid rollup + DISAGREEMENT detection
  detect_cartel(...)    -> cross-bid cartel suspicion (CVC Circular 4/3/07)
  rank_and_recommend(...) -> apply L1 / QCBS among eligibility-passed bids

DISAGREEMENT RULE (core of the product): if Technical says PASS but Compliance
says FAIL for the same bid, the orchestrator REFUSES to recommend it — it parks
the bid in 'human_review_required' and surfaces the two conflicting claims.

A blacklist hit or an eligibility FAIL is a hard disqualification (reject). A
cartel cluster also forces human review for every bid in the cluster.
"""

from __future__ import annotations

import itertools
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from agents.base import AgentResult
from shared.citation import Citation

AGENT_NAME = "reasoning_agent"

CARTEL_CLUSTER_PCT = 0.02  # 3+ bids within 2% of each other
CARTEL_MIN_BIDS = 3
_DEFAULT_QCBS = (70.0, 30.0)  # technical, financial — used if the tender states no weights

# Duplicate-bid detection — Jaccard on character-level shingles. Tuned for the
# "same documents, different name" case: when one entity submits via multiple
# proxies, the substantive prose stays identical but the org/contact names differ.
# A 0.85 threshold means at least 85% of 15-char shingles are shared.
DUPLICATE_JACCARD_THRESHOLD = 0.85
_SHINGLE_K = 15
# Pages of the technical PDF that carry the substantive content (cover/index/sign
# pages excluded — these would dilute the similarity score with chrome).
_DUPLICATE_PAGE_RANGE = (3, 12)


def _verdict(result: AgentResult | None) -> str:
    return result.verdict if result else "INFO"


def _claim_dict(c: Citation) -> dict:
    return {
        "claim": c.claim,
        "verdict": c.verdict,
        "agent": c.agent,
        "source_doc": c.source_doc,
        "page_number": c.page_number,
        "quote": c.quote,
        "severity": c.severity,
    }


def _first(claims: list[Citation], verdict: str) -> Citation | None:
    return next((c for c in claims if c.verdict == verdict), None)


@dataclass
class BidSynthesis:
    bid_id: str
    org_name: str
    quoted_amount: float | None
    technical_score: float | None
    verdicts: dict[str, str]
    blacklisted: bool
    eligibility_pass: bool
    responsive: bool  # eligible + compliant + technically acceptable + not blacklisted
    needs_human_review: bool
    disagreements: list[dict] = field(default_factory=list)
    recommended_action: str | None = None  # award | shortlist | reject | review
    bid_status: str = "evaluated"  # under_review | evaluated | human_review_required | rejected
    rank: int | None = None
    financial_score: float | None = None
    combined_score: float | None = None
    summary: str = ""
    rationale: str = ""


def synthesize_bid(
    tender_schema: dict[str, Any],
    intel: dict[str, Any],
    specialists: dict[str, AgentResult],
) -> BidSynthesis:
    """Roll up the five specialist results for one bid and detect disagreements."""
    elig = specialists.get("eligibility_agent")
    tech = specialists.get("technical_agent")
    comp = specialists.get("compliance_agent")
    fin = specialists.get("financial_agent")
    risk = specialists.get("risk_agent")

    verdicts = {
        "eligibility": _verdict(elig),
        "technical": _verdict(tech),
        "compliance": _verdict(comp),
        "financial": _verdict(fin),
        "risk": _verdict(risk),
    }
    blacklisted = bool((risk.data or {}).get("blacklisted")) if risk and risk.data else False
    eligibility_pass = verdicts["eligibility"] != "FAIL"
    quoted = (fin.data or {}).get("quoted_total_inr") if fin and fin.data else None
    if quoted is None:
        quoted = intel.get("quoted_amount")
    technical_score = (tech.data or {}).get("technical_score") if tech and tech.data else None

    s = BidSynthesis(
        bid_id=intel.get("bid_id", ""),
        org_name=intel.get("org_name", "Unknown bidder"),
        quoted_amount=quoted,
        technical_score=technical_score,
        verdicts=verdicts,
        blacklisted=blacklisted,
        eligibility_pass=eligibility_pass,
        responsive=False,
        needs_human_review=False,
    )

    tech_claims = tech.claims if tech else []
    comp_claims = comp.claims if comp else []

    # --- decision tree -----------------------------------------------------
    if blacklisted:
        risk_fail = _first(risk.claims if risk else [], "FAIL")
        s.recommended_action = "reject"
        s.bid_status = "rejected"
        s.summary = f"REJECT — {s.org_name} is debarred/blacklisted."
        s.rationale = risk_fail.claim if risk_fail else "Bidder matches the debarred-firms registry."
        return s

    if not eligibility_pass:
        elig_fail = _first(elig.claims if elig else [], "FAIL")
        s.recommended_action = "reject"
        s.bid_status = "rejected"
        s.summary = f"REJECT — {s.org_name} fails a mandatory eligibility criterion."
        s.rationale = elig_fail.claim if elig_fail else "One or more eligibility criteria not met."
        return s

    # THE disagreement: technical raised no hard objection (PASS or FLAG) but compliance FAIL.
    # The spec example is "Technical PASS, Compliance FAIL"; we broaden to FLAG so that a
    # technical evaluator who marked a criterion ambiguous (not FAIL) still surfaces the
    # conflict with a hard compliance fail — the officer needs to see both.
    if verdicts["technical"] in ("PASS", "FLAG") and verdicts["compliance"] == "FAIL":
        tech_pass = _first(tech_claims, "PASS") or _first(tech_claims, "FLAG")
        comp_fail = _first(comp_claims, "FAIL")
        conflicting = [
            _claim_dict(x) for x in (tech_pass, comp_fail) if x is not None
        ]
        s.needs_human_review = True
        s.recommended_action = "review"
        s.bid_status = "human_review_required"
        s.disagreements.append(
            {
                "type": "technical_vs_compliance",
                "bid_id": s.bid_id,
                "org_name": s.org_name,
                "note": (
                    "Technical evaluation PASSED but Compliance FAILED — the orchestrator "
                    "refuses to recommend automatically and routes this bid to human review."
                ),
                "conflicting_claims": conflicting,
            }
        )
        s.summary = f"HUMAN REVIEW — {s.org_name}: technically strong but non-compliant."
        s.rationale = (
            "Technical PASS conflicts with a Compliance FAIL "
            f"({comp_fail.claim if comp_fail else 'compliance issue'}). "
            "Refusing to recommend; needs an officer's call."
        )
        return s

    # Other hard non-responsive cases.
    if verdicts["compliance"] == "FAIL":
        c = _first(comp_claims, "FAIL")
        s.recommended_action = "reject"
        s.bid_status = "rejected"
        s.summary = f"REJECT — {s.org_name}: non-responsive on compliance."
        s.rationale = c.claim if c else "Mandatory compliance item missing."
        return s

    if verdicts["technical"] == "FAIL":
        t = _first(tech_claims, "FAIL")
        s.recommended_action = "reject"
        s.bid_status = "rejected"
        s.summary = f"REJECT — {s.org_name}: fails a mandatory technical requirement."
        s.rationale = t.claim if t else "Technical requirement not met."
        return s

    # Abnormally low (>20% below estimate, CVC) — do not auto-recommend; seek justification.
    if verdicts["financial"] == "FAIL":
        fin_fail = _first(fin.claims if fin else [], "FAIL")
        s.needs_human_review = True
        s.recommended_action = "review"
        s.bid_status = "human_review_required"
        s.disagreements.append(
            {
                "type": "abnormally_low_bid",
                "bid_id": s.bid_id,
                "org_name": s.org_name,
                "note": (
                    "Financial bid flagged abnormally low (>20% below the estimate, CVC norms) — "
                    "refusing to auto-recommend; a written price justification is required."
                ),
                "conflicting_claims": [_claim_dict(fin_fail)] if fin_fail else [],
            }
        )
        s.summary = f"HUMAN REVIEW — {s.org_name}: abnormally low bid."
        s.rationale = fin_fail.claim if fin_fail else "Abnormally low bid (>20% below estimate)."
        return s

    # Responsive — eligible for ranking. Final action set by rank_and_recommend.
    s.responsive = True
    s.bid_status = "evaluated"
    s.summary = f"RESPONSIVE — {s.org_name}: passes eligibility, technical and compliance."
    s.rationale = "Eligible for financial ranking."
    return s


def detect_cartel(syntheses: list[BidSynthesis]) -> list[dict]:
    """Groups of >=3 bids whose quoted amounts cluster within CARTEL_CLUSTER_PCT.

    Per CVC Circular 4/3/07 (2007) on cartel formation / bid rigging.
    """
    priced = [s for s in syntheses if s.quoted_amount and s.quoted_amount > 0]
    priced.sort(key=lambda s: s.quoted_amount)  # type: ignore[arg-type]
    groups: list[dict] = []
    used: set[str] = set()
    for i, anchor in enumerate(priced):
        if anchor.bid_id in used:
            continue
        cluster = [
            s for s in priced[i:] if s.quoted_amount <= anchor.quoted_amount * (1 + CARTEL_CLUSTER_PCT)
        ]
        if len(cluster) >= CARTEL_MIN_BIDS:
            for s in cluster:
                used.add(s.bid_id)
            lo = min(s.quoted_amount for s in cluster)
            hi = max(s.quoted_amount for s in cluster)
            spread = round((hi - lo) / lo * 100, 2) if lo else 0.0
            groups.append(
                {
                    "type": "cartel_suspicion",
                    "spread_pct": spread,
                    "threshold_pct": CARTEL_CLUSTER_PCT * 100,
                    "note": (
                        f"{len(cluster)} bids cluster within {spread}% (≤2%) — possible cartel / "
                        "bid-rigging per CVC Circular 4/3/07. Bids routed to human review."
                    ),
                    "bids": [
                        {"bid_id": s.bid_id, "org_name": s.org_name, "quoted_amount": s.quoted_amount}
                        for s in cluster
                    ],
                }
            )
    return groups


def cartel_citation(s: BidSynthesis, group: dict, price_cite: Citation | None) -> Citation | None:
    """A FLAG citation for a cartel-clustered bid, grounded on its own price line."""
    if price_cite is None:
        return None
    others = [b for b in group["bids"] if b["bid_id"] != s.bid_id]
    others_txt = ", ".join(f"{o['org_name']} ₹{o['quoted_amount']:,.0f}" for o in others)
    return Citation(
        claim=(
            f"Quoted ₹{s.quoted_amount:,.0f} clusters within {group['spread_pct']}% of {len(others)} "
            f"other bids ({others_txt}) — possible cartel/bid-rigging per CVC Circular 4/3/07."
        ),
        verdict="FLAG",
        source_doc=price_cite.source_doc,
        page_number=price_cite.page_number,
        quote=price_cite.quote,
        confidence=0.8,
        tender_clause="CVC Circular 4/3/07 — cartel / bid-rigging",
        tender_clause_page=None,
        severity="high",
        agent=AGENT_NAME,
    )


def _bid_text(intel: dict[str, Any]) -> str:
    """Concatenate the substantive technical pages, normalised (lowercased + collapsed
    whitespace, with the bidder's own org name + contact name swapped out — so two
    submissions with identical prose but different bidder identities still match)."""
    docs = intel.get("documents") or []
    tech = next((d for d in docs if d.get("doc_type") == "technical"), None)
    if not tech:
        return ""
    lo, hi = _DUPLICATE_PAGE_RANGE
    text = " ".join(
        (p.get("text") or "")
        for p in tech.get("pages") or []
        if lo <= p.get("page_number", 0) <= hi
    ).lower()
    text = re.sub(r"\s+", " ", text)
    for name in (intel.get("org_name"), intel.get("contact_name")):
        if name:
            text = text.replace(name.lower(), "<bidder>")
    return text.strip()


def _shingles(text: str, k: int = _SHINGLE_K) -> set[str]:
    if len(text) < k:
        return set()
    return {text[i:i + k] for i in range(len(text) - k + 1)}


def detect_duplicate_bidders(
    intels: list[dict[str, Any]],
    threshold: float = DUPLICATE_JACCARD_THRESHOLD,
) -> list[dict]:
    """Group bids whose substantive content is ≥`threshold` Jaccard-similar after
    normalising out bidder/contact names.

    Returns one entry per cluster of ≥2 bids. Used to flag "same documents, only
    the name differs" — i.e. shell / proxy bidding, a serious integrity issue
    under GFR and the CVC integrity-pact regime.
    """
    sh: dict[str, set[str]] = {}
    for intel in intels:
        text = _bid_text(intel)
        sh[intel["bid_id"]] = _shingles(text)

    ids = list(sh.keys())
    parent = {b: b for b in ids}

    def find(b: str) -> str:
        while parent[b] != b:
            parent[b] = parent[parent[b]]
            b = parent[b]
        return b

    pair_sims: dict[tuple[str, str], float] = {}
    for a, b in itertools.combinations(ids, 2):
        sa, sb = sh[a], sh[b]
        if not sa or not sb:
            continue
        sim = len(sa & sb) / len(sa | sb)
        pair_sims[(a, b)] = sim
        if sim >= threshold:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

    clusters: dict[str, list[str]] = defaultdict(list)
    for b in ids:
        clusters[find(b)].append(b)

    intel_by_id = {i["bid_id"]: i for i in intels}
    groups: list[dict] = []
    for cluster in clusters.values():
        if len(cluster) < 2:
            continue
        # Compute the minimum pairwise similarity inside the cluster as a
        # conservative "match score" we can show the officer.
        sims = []
        for x, y in itertools.combinations(cluster, 2):
            key = (x, y) if (x, y) in pair_sims else (y, x)
            sims.append(pair_sims.get(key, 0.0))
        min_sim = round(min(sims) * 100, 1) if sims else 0.0
        names = [intel_by_id[bid_id].get("org_name") for bid_id in cluster]
        groups.append({
            "type": "duplicate_bidders",
            "kind": "exact" if min_sim >= 99.0 else "near",
            "match_score_pct": min_sim,
            "threshold_pct": round(threshold * 100, 1),
            "note": (
                f"{len(cluster)} bids share substantially identical content "
                f"({min_sim}% similarity after normalising bidder names) — possible shell / proxy "
                "submission. Both bids surfaced for officer scrutiny."
            ),
            "bids": [
                {
                    "bid_id": bid_id,
                    "org_name": intel_by_id[bid_id].get("org_name"),
                    "quoted_amount": intel_by_id[bid_id].get("quoted_amount"),
                }
                for bid_id in cluster
            ],
        })
    return groups


def duplicate_citation(
    intel: dict[str, Any],
    other_org_names: list[str],
    match_score_pct: float,
) -> Citation | None:
    """Page-grounded duplicate-flag citation for one bid in a duplicate group.

    Cited from the bidder-profile page of THIS bid's own technical PDF — the
    distinctive identity content. The claim names the other bidder(s) in the
    cluster and the match score, so the audit trail explains the flag.
    """
    docs = intel.get("documents") or []
    tech = next((d for d in docs if d.get("doc_type") == "technical"), None)
    if not tech:
        return None
    # Prefer the bidder-profile page; fall back to first text-bearing page.
    pages = tech.get("pages") or []
    page = next((p for p in pages if p.get("page_number") == 3 and (p.get("text") or "").strip()), None)
    if page is None:
        page = next((p for p in pages if (p.get("text") or "").strip()), None)
    if page is None:
        return None
    quote = next(
        (ln.strip() for ln in (page.get("text") or "").splitlines() if ln.strip()),
        "",
    )
    if not quote:
        return None
    others = ", ".join(other_org_names) or "another bid"
    return Citation(
        claim=(
            f"Bid content matches {others} at {match_score_pct}% similarity after "
            f"normalising bidder names — possible duplicate / proxy / shell submission. "
            "Investigate identity, ownership and authorised-signatory linkage before any award."
        ),
        verdict="FLAG",
        source_doc=tech["file_name"],
        page_number=page["page_number"],
        quote=quote,
        confidence=0.92,
        tender_clause="Integrity check — duplicate / proxy submission",
        tender_clause_page=None,
        severity="high",
        agent=AGENT_NAME,
    )


def rank_and_recommend(
    tender_schema: dict[str, Any], syntheses: list[BidSynthesis]
) -> list[dict]:
    """Apply the tender's evaluation method to the responsive bids; build the ranking.

    L1 / LCS: lowest quoted price among eligibility-passed wins.
    QCBS: highest weighted (technical, financial) score wins.
    Mutates each responsive synthesis (rank, scores, recommended_action) and returns
    a sorted ranking table.
    """
    method = (tender_schema.get("evaluation_method") or "unknown").upper()
    eligible = [s for s in syntheses if s.responsive and not s.needs_human_review]

    if method == "QCBS":
        priced = [s for s in eligible if s.quoted_amount and s.quoted_amount > 0]
        min_price = min((s.quoted_amount for s in priced), default=None)
        weights = tender_schema.get("qcbs_weights") or {}
        tech_w = float(weights.get("technical") or 0) or _DEFAULT_QCBS[0]
        fin_w = float(weights.get("financial") or 0) or _DEFAULT_QCBS[1]
        for s in eligible:
            ts = s.technical_score if s.technical_score is not None else 0.0
            if s.quoted_amount and min_price:
                s.financial_score = round(min_price / s.quoted_amount * 100, 2)
            else:
                s.financial_score = 0.0
            s.combined_score = round((tech_w * ts + fin_w * s.financial_score) / 100, 2)
        ranked = sorted(eligible, key=lambda s: (s.combined_score or 0), reverse=True)
    else:  # L1 / LCS / unknown -> lowest price
        ranked = sorted(
            eligible,
            key=lambda s: (s.quoted_amount is None, s.quoted_amount if s.quoted_amount else float("inf")),
        )

    for idx, s in enumerate(ranked, start=1):
        s.rank = idx
        s.recommended_action = "award" if idx == 1 else "shortlist"
        if idx == 1:
            s.summary = f"RECOMMEND AWARD — {s.org_name} ({method} rank L1)."
        else:
            s.summary = f"SHORTLIST — {s.org_name} ({method} rank L{idx})."

    # Full table: eligible ranked first, then human-review, then rejected.
    others = [s for s in syntheses if s not in eligible]
    others.sort(key=lambda s: 0 if s.needs_human_review else 1)
    table: list[dict] = []
    for s in [*ranked, *others]:
        table.append(
            {
                "rank": s.rank,
                "bid_id": s.bid_id,
                "org_name": s.org_name,
                "quoted_amount": s.quoted_amount,
                "technical_score": s.technical_score,
                "financial_score": s.financial_score,
                "combined_score": s.combined_score,
                "recommended_action": s.recommended_action,
                "bid_status": s.bid_status,
                "needs_human_review": s.needs_human_review,
                "summary": s.summary,
            }
        )
    return table
