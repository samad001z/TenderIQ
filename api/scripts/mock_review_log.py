"""Hermetic demo of the Phase-5 review pipeline — prints the SSE event log.

No Vertex, no Supabase: a FakeGemini returns canned (but contract-valid) structured
outputs and NullPersist swallows writes. This exercises the REAL orchestration
(services.review_pipeline.stream_review + the real reasoning_agent + the real,
deterministic risk_agent against blacklist.json), so the event log is exactly what
the live /api/tenders/{id}/review endpoint emits.

Run:  uv run python scripts/mock_review_log.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # /api on path

from models.agent_io import FinancialAnalysis, TechnicalAnalysis  # noqa: E402
from services.review_pipeline import NullPersist, stream_review  # noqa: E402
from shared.citation import Citation, CitationList  # noqa: E402

# --- a QCBS tender (mirrors the seeded "System Integrator" tender: est ₹8.5cr) ---
QCBS_TENDER: dict[str, Any] = {
    "evaluation_method": "QCBS",
    "qcbs_weights": {"technical": 70, "financial": 30, "source_page": 4},
    "value_estimate": {"value": 85_000_000, "source_page": 1, "quote": "Estimated value ₹8.5 crore"},
    "eligibility_criteria": [
        {"description": "Average annual turnover ≥ ₹15 cr over 3 FYs", "source_page": 2, "quote": "turnover not less than ₹15 crore"},
        {"description": "≥ 5 years experience in system-integration projects", "source_page": 2, "quote": "minimum five years experience"},
    ],
    "technical_criteria": [
        {"description": "Solution architecture & approach", "weight": 40, "source_page": 4, "quote": "Solution architecture — 40 marks"},
        {"description": "Team strength & key-personnel CVs", "weight": 30, "source_page": 4, "quote": "Key personnel — 30 marks"},
    ],
    "financial_format": {"value": "Item-wise BoQ, all-inclusive", "source_page": 3, "quote": "all-inclusive BoQ"},
    "emd_amount": {"value": 850_000, "source_page": 1, "quote": "EMD of ₹8,50,000"},
    "pbg_percentage": {"value": 10, "source_page": 7, "quote": "PBG @ 10%"},
    "integrity_pact_required": {"value": True, "source_page": 7, "quote": "Integrity Pact is mandatory"},
    "ppp_mii_class": "I",
    "ppp_mii_quote": "restricted to Class-I local suppliers",
    "ppp_mii_source_page": 8,
    "submission_deadline": {"value": "2026-06-15 15:00", "source_page": 2, "quote": "due by 15.06.2026"},
}
L1_TENDER = {**QCBS_TENDER, "evaluation_method": "L1"}


# --- canned per-bid agent outputs -------------------------------------------
def C(spec, verdict, page, claim, quote, severity, clause=None, clause_page=None) -> Citation:
    return Citation(
        claim=claim, verdict=verdict, source_doc=spec["file_name"], page_number=page,
        quote=quote, confidence=0.92, tender_clause=clause, tender_clause_page=clause_page,
        severity=severity, agent="",
    )


def _pass_eligibility(spec):
    return [
        ("PASS", 5, "Turnover ₹62 cr (FY24) exceeds the ₹15 cr bar.", "Annual turnover FY2023-24: ₹62,00,00,000", "low"),
        ("PASS", 6, "11 years of SI experience — meets the 5-year minimum.", "Incorporated 2014; 11 years in systems integration", "low"),
    ]


def _pass_compliance(spec):
    return [
        ("PASS", 12, "PPP-MII Class-I self-certification (≥50% local content) enclosed.", "We certify local content of 62% (Class-I).", "low"),
        ("PASS", 14, "CVC Integrity Pact signed by the authorised signatory.", "Integrity Pact signed and witnessed.", "low"),
        ("PASS", 2, "EMD of ₹8.5 lakh enclosed as an online instrument.", "EMD ₹8,50,000 paid vide UTR …4471", "low"),
    ]


def _tech(score, ok=True):
    claims = [
        ("PASS" if ok else "FAIL", 18, "Microservices architecture maps to all functional modules.", "Solution architecture: 9 microservices …", "low" if ok else "high"),
        ("PASS", 22, "Three PMP-certified leads with relevant CVs attached.", "Key personnel: 3 PMP-certified project leads", "low"),
    ]
    return {"score": score, "claims": claims}


def _fin(quoted):
    return {"quoted": quoted, "claims": [("INFO", 3, f"Total quoted price ₹{quoted:,.0f} (all-inclusive).", f"Grand Total: ₹{quoted:,.0f}", "low")]}


def bid(bid_id, org, slug, *, eligibility, technical, compliance, financial, bad_first=None):
    return {
        "bid_id": bid_id, "org_name": org, "file_name": f"{slug}_bid.pdf",
        "eligibility": eligibility, "technical": technical, "compliance": compliance,
        "financial": financial, "bad_first": bad_first,
    }


class FakeResp:
    def __init__(self, obj):
        self.parsed = obj
        self.text = obj.model_dump_json()


class FakeGemini:
    """Routes by org marker (in the bid pages) + response schema + system marker."""

    def __init__(self, bids):
        self.bids = {b["org_name"]: b for b in bids}

    def _cites(self, spec, items, rerun, kind):
        cites = [C(spec, *it) for it in items]
        # Demonstrate the citation gate: emit ONE claim missing page+quote on the first
        # attempt; the orchestrator rejects it and the rerun returns a clean set.
        if not rerun and spec.get("bad_first") == kind:
            cites = [C(spec, "FLAG", 0, "Past-performance certificate referenced but not located.", "", "medium")] + cites
        return CitationList(citations=cites)

    def generate_pro(self, parts, schema, temperature: float = 0.1):
        blob = "\n".join(p for p in parts if isinstance(p, str))
        rerun = "SOME OF YOUR CLAIMS WERE REJECTED" in blob
        org = next((o for o in self.bids if o in blob), None)
        spec = self.bids.get(org, {})
        if schema is TechnicalAnalysis:
            t = spec.get("technical", {"score": 0, "claims": []})
            return FakeResp(TechnicalAnalysis(technical_score=t["score"], citations=[C(spec, *it) for it in t["claims"]]))
        if schema is FinancialAnalysis:
            f = spec.get("financial", {"quoted": None, "claims": []})
            return FakeResp(FinancialAnalysis(quoted_total_inr=f["quoted"], citations=[C(spec, *it) for it in f["claims"]]))
        if "Eligibility Evaluator" in blob:
            return FakeResp(self._cites(spec, spec.get("eligibility", []), rerun, "eligibility"))
        if "Compliance Evaluator" in blob:
            return FakeResp(self._cites(spec, spec.get("compliance", []), rerun, "compliance"))
        return FakeResp(CitationList(citations=[]))

    generate_flash = generate_pro


def make_intel(spec, tender_id):
    return {
        "bid_id": spec["bid_id"], "tender_id": tender_id, "bidder_id": spec["bid_id"],
        "org_name": spec["org_name"], "quoted_amount": spec["financial"]["quoted"],
        "documents": [
            {
                "doc_type": "technical", "file_name": spec["file_name"], "page_count": 1,
                "pages": [{"page_number": 1, "text": f"Bidder: {spec['org_name']}. Combined technical & financial proposal."}],
            }
        ],
    }


# --- the three scenarios -----------------------------------------------------
def scenario_a():
    bids = [
        bid("A1", "Meridian Infra Pvt Ltd", "meridian",
            eligibility=_pass_eligibility(None), technical=_tech(88), compliance=_pass_compliance(None),
            financial=_fin(76_000_000), bad_first="eligibility"),
        bid("A2", "Orbit Engineering LLP", "orbit",
            eligibility=_pass_eligibility(None), technical=_tech(82), compliance=_pass_compliance(None),
            financial=_fin(80_000_000)),
        bid("A3", "Galaxy Constructions Pvt Ltd", "galaxy",  # debarred in blacklist.json
            eligibility=_pass_eligibility(None), technical=_tech(85), compliance=_pass_compliance(None),
            financial=_fin(82_000_000)),
    ]
    return ("A — QCBS: ranking + blacklist + citation-gate rerun", QCBS_TENDER, bids)


def scenario_b():
    comp_fail = [
        ("PASS", 12, "PPP-MII Class-I certificate enclosed.", "Local content 55% (Class-I).", "low"),
        ("FAIL", 2, "EMD instrument NOT enclosed — bid is non-responsive on EMD.", "Checklist item 4 (EMD): — left blank —", "critical"),
    ]
    bids = [
        bid("B1", "Meridian Infra Pvt Ltd", "meridian",
            eligibility=_pass_eligibility(None), technical=_tech(90), compliance=_pass_compliance(None),
            financial=_fin(78_000_000)),
        bid("B2", "Orbit Engineering LLP", "orbit",
            eligibility=_pass_eligibility(None), technical=_tech(84), compliance=comp_fail,
            financial=_fin(79_000_000)),  # Technical PASS but Compliance FAIL -> DISAGREEMENT
        bid("B3", "Apex Digital Pvt Ltd", "apex",
            eligibility=_pass_eligibility(None), technical=_tech(80), compliance=_pass_compliance(None),
            financial=_fin(64_000_000)),  # 24.7% below ₹8.5cr estimate -> ABNORMALLY LOW
    ]
    return ("B — QCBS: technical-vs-compliance disagreement + abnormally-low bid", QCBS_TENDER, bids)


def scenario_c():
    bids = [
        bid("C1", "Coastal Infra Ltd", "coastal",
            eligibility=_pass_eligibility(None), technical=_tech(83), compliance=_pass_compliance(None),
            financial=_fin(80_500_000)),
        bid("C2", "Highland Builders Pvt Ltd", "highland",
            eligibility=_pass_eligibility(None), technical=_tech(81), compliance=_pass_compliance(None),
            financial=_fin(81_000_000)),
        bid("C3", "Summit Engineering Co", "summit",
            eligibility=_pass_eligibility(None), technical=_tech(82), compliance=_pass_compliance(None),
            financial=_fin(81_800_000)),  # all 3 within 1.6% -> CARTEL (CVC 4/3/07)
    ]
    return ("C — L1: cartel suspicion (3 bids within 2%)", L1_TENDER, bids)


# --- pretty SSE printer ------------------------------------------------------
def fmt(event: str, p: dict) -> str:
    if event == "review_start":
        return f"  ▶ REVIEW START · method={p['evaluation_method']} · {p['bids']} bids"
    if event == "bid_start":
        return f"\n  ── BID {p['org_name']} ({p['bid_id']}) ──"
    if event == "agent_start":
        sc = " [cross-bid]" if p.get("scope") == "cross_bid" else ""
        return f"     ▷ {p['agent']:<20} start{sc}"
    if event == "claim_emitted":
        return (f"        • [{p['verdict']:<4}] {p['agent']:<18} "
                f"{p['source_doc']} p.{p['page_number']}  «{p['quote'][:46]}»")
    if event == "agent_complete":
        rej = f" rej={p['rejections']}" if p.get("rejections") else ""
        return f"     ◁ {p['agent']:<20} {p.get('status',''):<9} verdict={p.get('verdict','-'):<4} claims={p.get('claims',0)}{rej} {p.get('elapsed_ms',0)}ms"
    if event == "disagreement_detected":
        head = f"     ⚠ DISAGREEMENT [{p['type']}] {p.get('org_name','')}".rstrip()
        lines = [head, f"        {p['note']}"]
        for c in p.get("conflicting_claims", []):
            lines.append(f"          ↳ [{c['verdict']}] {c['agent']}: {c['claim'][:70]}")
        for b in p.get("bids", []):
            lines.append(f"          ↳ {b['org_name']} ₹{b['quoted_amount']:,.0f}")
        return "\n".join(lines)
    if event == "orchestrator_complete":
        lines = ["\n  ■ ORCHESTRATOR COMPLETE",
                 f"     method={p['evaluation_method']}  award={p.get('recommended_award')}  "
                 f"human_review={p.get('human_review_required')}"]
        lines.append("     RANKING:")
        for r in p["ranking"]:
            rank = f"L{r['rank']}" if r["rank"] else " —"
            amt = f"₹{r['quoted_amount']:,.0f}" if r["quoted_amount"] else "—"
            extra = f" combined={r['combined_score']}" if r.get("combined_score") is not None else ""
            lines.append(f"       {rank:>3}  {r['recommended_action'] or '—':<9} {r['org_name']:<28} {amt:>14}  [{r['bid_status']}]{extra}")
        return "\n".join(lines)
    return f"     {event}: {p}"


async def run_scenario(title, tender, bid_specs):
    print("\n" + "=" * 92)
    print(f"SCENARIO {title}")
    print("=" * 92)
    intels = [make_intel(b, "tender-demo") for b in bid_specs]
    gem = FakeGemini(bid_specs)
    async for event, payload in stream_review(
        tender, intels, gemini=gem, persist=NullPersist(), tender_id="tender-demo"
    ):
        print(fmt(event, payload))


async def main():
    for sc in (scenario_a, scenario_b, scenario_c):
        title, tender, bids = sc()
        await run_scenario(title, tender, bids)


if __name__ == "__main__":
    asyncio.run(main())
