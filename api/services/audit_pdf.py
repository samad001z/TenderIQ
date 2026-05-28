"""CAG-style audit PDF — the officer's signed record of the AI review.

Each PDF carries: cover & metadata, executive summary, ranked recommendation,
disagreement/cartel callouts (if any), per-bid agent-by-agent claims with their
page citations, and a sign-off block (name + designation + date) for the officer
in charge. Generated with reportlab so it prints cleanly to any PDF reader.

The Citation contract is the audit grid: every claim in this report has
page_number > 0 and a verbatim quote — the orchestrator has rejected anything
that doesn't (see agent_runs.rejections, also surfaced in the appendix).
"""
from __future__ import annotations

import io
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import KeepTogether, PageBreak

# Match the synthetic-bid generator: register a Unicode-aware TTF so ₹ survives.
_FR, _FB, _FI = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
_CAND = (
    [("Arial", r"C:\Windows\Fonts\arial.ttf"),
     ("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"),
     ("Arial-Italic", r"C:\Windows\Fonts\ariali.ttf")]
    if platform.system() == "Windows"
    else [("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
          ("DejaVu-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
          ("DejaVu-Italic", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf")]
)
_present = [(n, p) for n, p in _CAND if Path(p).exists()]
if len(_present) >= 3:
    try:
        for n, p in _present:
            pdfmetrics.registerFont(TTFont(n, p))
        fam = _present[0][0]
        pdfmetrics.registerFontFamily(fam, normal=fam, bold=f"{fam}-Bold", italic=f"{fam}-Italic")
        _FR, _FB, _FI = fam, f"{fam}-Bold", f"{fam}-Italic"
    except Exception:
        pass


# --- Design-token palette --------------------------------------------------
_OBSIDIAN = colors.HexColor("#0B0D0F")
_GOLD = colors.HexColor("#C8A14A")
_CREAM = colors.HexColor("#F5F1E8")
_MUTED = colors.HexColor("#5E646B")
_INK = colors.HexColor("#1C2024")
_RULE = colors.HexColor("#C0C6CE")
_FAINT = colors.HexColor("#F6F2E3")
_HEAD = colors.HexColor("#E8E2CF")
_VERDICT = {
    "PASS": colors.HexColor("#1F7A36"),
    "FAIL": colors.HexColor("#B0341A"),
    "FLAG": colors.HexColor("#A77824"),
    "INFO": colors.HexColor("#345D9F"),
}
_ACTION = {
    "award":     colors.HexColor("#1F7A36"),
    "shortlist": colors.HexColor("#345D9F"),
    "review":    colors.HexColor("#A77824"),
    "reject":    colors.HexColor("#B0341A"),
}


def _styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=_FB,
                             fontSize=20, leading=24, spaceAfter=8, textColor=_OBSIDIAN),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=_FB,
                             fontSize=13.5, leading=17, spaceBefore=12, spaceAfter=6, textColor=_OBSIDIAN),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName=_FB,
                             fontSize=11, leading=14, spaceBefore=8, spaceAfter=2, textColor=_OBSIDIAN),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName=_FR,
                               fontSize=10.5, leading=14.5, spaceAfter=4, textColor=_INK),
        "muted": ParagraphStyle("muted", parent=base["BodyText"], fontName=_FI,
                                fontSize=9.5, leading=13, textColor=_MUTED),
        "mono": ParagraphStyle("mono", parent=base["BodyText"], fontName="Courier",
                               fontSize=9, leading=12, textColor=_MUTED),
        "quote": ParagraphStyle("quote", parent=base["BodyText"], fontName=_FI,
                                fontSize=10, leading=14, leftIndent=10, textColor=_INK),
        "claim": ParagraphStyle("claim", parent=base["BodyText"], fontName=_FR,
                                fontSize=10, leading=13.5, textColor=_INK),
        "footer": ParagraphStyle("footer", parent=base["BodyText"], fontName=_FR,
                                 fontSize=8.5, leading=11, textColor=_MUTED, alignment=1),
    }


def _kv(label: str, value: str, s) -> Table:
    t = Table([[label, value]], colWidths=[5.6 * cm, 11.2 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, 0), _FB),
        ("FONTNAME", (1, 0), (1, 0), _FR),
        ("FONTSIZE", (0, 0), (-1, -1), 10.5),
        ("TEXTCOLOR", (0, 0), (0, 0), _OBSIDIAN),
        ("TEXTCOLOR", (1, 0), (1, 0), _INK),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _verdict_pill(verdict: str, s) -> Paragraph:
    c = _VERDICT.get(verdict, _INK)
    return Paragraph(
        f'<b><font color="{c.hexval()}">{verdict}</font></b>', s["body"]
    )


def _inr(n: Any) -> str:
    try:
        amount = int(n)
    except (TypeError, ValueError):
        return "—"
    digits = str(amount)[::-1]
    parts = [digits[:3]]
    rest = digits[3:]
    while rest:
        parts.append(rest[:2])
        rest = rest[2:]
    return "₹" + ",".join(parts)[::-1]


def _on_page(canvas, doc):
    """Footer with TenderIQ + page number on every page."""
    canvas.saveState()
    canvas.setFont(_FR, 8.5)
    canvas.setFillColor(_MUTED)
    canvas.drawString(1.8 * cm, 1.0 * cm, "TenderIQ — AI Bid Review Audit Report")
    canvas.drawRightString(A4[0] - 1.8 * cm, 1.0 * cm, f"Page {doc.page}")
    canvas.setStrokeColor(_GOLD)
    canvas.setLineWidth(0.8)
    canvas.line(1.8 * cm, 1.25 * cm, A4[0] - 1.8 * cm, 1.25 * cm)
    canvas.restoreState()


def build_pdf(payload: dict[str, Any]) -> bytes:
    s = _styles()
    flow: list = []
    officer = payload.get("officer") or {}
    tender = payload.get("tender") or {}
    ranking = payload.get("ranking") or []
    bids = payload.get("bids") or []
    disagreements = payload.get("disagreements") or []

    # ---- Cover -----------------------------------------------------------
    flow.append(Paragraph("AUDIT REPORT", s["h1"]))
    flow.append(Paragraph("AI-assisted bid review · TenderIQ", s["muted"]))
    flow.append(Spacer(1, 18))
    flow.append(_kv("Tender title:", tender.get("title") or "—", s))
    flow.append(_kv("Reference number:", tender.get("reference_no") or "—", s))
    flow.append(_kv("Ministry / Department:", " / ".join(
        x for x in (tender.get("ministry"), tender.get("department")) if x) or "—", s))
    flow.append(_kv("Estimated value:", _inr(tender.get("estimated_value")), s))
    flow.append(_kv("Evaluation method:", str(tender.get("evaluation_method") or "—").upper(), s))
    flow.append(_kv("Bids evaluated:", str(len(bids)), s))
    flow.append(_kv("Report generated:", payload.get("generated_at") or "—", s))
    flow.append(Spacer(1, 18))

    # ---- Executive summary ---------------------------------------------
    flow.append(Paragraph("EXECUTIVE SUMMARY", s["h2"]))
    award_row = next((r for r in ranking if r.get("recommended_action") == "award"), None)
    if award_row:
        flow.append(Paragraph(
            f"<b>Recommendation: award to {award_row.get('org_name')}</b> "
            f"(rank L1, quoted {_inr(award_row.get('quoted_amount'))}).",
            s["body"]))
    if any(r.get("needs_human_review") for r in ranking):
        flow.append(Paragraph(
            "<b><font color='#B0341A'>HUMAN REVIEW REQUIRED</font></b> on one or more bids — "
            "the orchestrator detected disagreements / cartel suspicion and refuses to auto-recommend "
            "those bids. See the disagreement section below.",
            s["body"]))
    if not award_row and any(r.get("recommended_action") == "review" for r in ranking):
        flow.append(Paragraph(
            "<b><font color='#B0341A'>NO BID RECOMMENDED FOR AWARD</font></b> — every bid was "
            "either ineligible, non-responsive, or routed to human review.",
            s["body"]))

    # ---- Ranking table -------------------------------------------------
    flow.append(Paragraph("RANKING", s["h2"]))
    rows = [["Rank", "Bidder", "Action", "Quoted (₹)", "Tech", "Fin", "Combined", "Status"]]
    for r in ranking:
        rank_label = f"L{r['rank']}" if r.get("rank") else "—"
        rows.append([
            rank_label,
            r.get("org_name") or "—",
            (r.get("recommended_action") or "—").upper(),
            _inr(r.get("quoted_amount")),
            f"{r['technical_score']:.1f}" if r.get("technical_score") is not None else "—",
            f"{r['financial_score']:.1f}" if r.get("financial_score") is not None else "—",
            f"{r['combined_score']:.2f}" if r.get("combined_score") is not None else "—",
            r.get("bid_status") or "—",
        ])
    t = Table(rows, colWidths=[1.2 * cm, 5.2 * cm, 2.4 * cm, 2.7 * cm, 1.5 * cm, 1.5 * cm, 1.9 * cm, 2.2 * cm])
    style = [
        ("FONTNAME", (0, 0), (-1, -1), _FR),
        ("FONTNAME", (0, 0), (-1, 0), _FB),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BACKGROUND", (0, 0), (-1, 0), _HEAD),
        ("BOX", (0, 0), (-1, -1), 0.5, _RULE),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, _RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (3, 1), (6, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]
    for i, r in enumerate(ranking, start=1):
        action = (r.get("recommended_action") or "").lower()
        if action in _ACTION:
            style.append(("TEXTCOLOR", (2, i), (2, i), _ACTION[action]))
            style.append(("FONTNAME", (2, i), (2, i), _FB))
    t.setStyle(TableStyle(style))
    flow.append(t)

    # ---- Disagreements -------------------------------------------------
    if disagreements:
        flow.append(Paragraph("DISAGREEMENTS DETECTED", s["h2"]))
        for d in disagreements:
            kind = d.get("type", "disagreement").replace("_", " ").upper()
            who = d.get("org_name") or ""
            head = f"⚡ {kind}" + (f" — {who}" if who else "")
            flow.append(Paragraph(f"<b><font color='#B0341A'>{head}</font></b>", s["body"]))
            note = d.get("note") or ""
            if note:
                flow.append(Paragraph(note, s["body"]))
            for c in d.get("conflicting_claims") or []:
                flow.append(Paragraph(
                    f"  ↳ [<b>{c.get('verdict')}</b>] {c.get('agent')}: {c.get('claim')}", s["claim"]))
                if c.get("source_doc"):
                    flow.append(Paragraph(
                        f"     <font color='#5E646B'>cited from</font> {c['source_doc']} · p.{c.get('page_number')}",
                        s["mono"]))
            for b in d.get("bids") or []:
                flow.append(Paragraph(
                    f"  ↳ {b['org_name']} ({_inr(b['quoted_amount'])})", s["claim"]))
            flow.append(Spacer(1, 6))

    # ---- Per-bid sections ---------------------------------------------
    for b in bids:
        flow.append(PageBreak())
        flow.append(Paragraph(f"BID — {b.get('org_name')}", s["h1"]))
        action = (b.get("recommended_action") or "—").upper()
        col = _ACTION.get((b.get("recommended_action") or "").lower(), _INK)
        flow.append(Paragraph(
            f"<b>Recommendation: <font color='{col.hexval()}'>{action}</font></b> · "
            f"status: {b.get('bid_status') or '—'} · quoted: {_inr(b.get('quoted_amount'))}",
            s["body"]))
        if b.get("summary"):
            flow.append(Paragraph(b["summary"], s["body"]))
        if b.get("rationale"):
            flow.append(Paragraph(f"<i>{b['rationale']}</i>", s["muted"]))

        # per-agent claims
        for ag in b.get("agents") or []:
            verdict = ag.get("verdict") or "INFO"
            flow.append(Paragraph(
                f"{ag.get('agent','').upper()} · <font color='{_VERDICT.get(verdict, _INK).hexval()}'>{verdict}</font>",
                s["h3"]))
            claims = ag.get("claims") or []
            if not claims:
                flow.append(Paragraph("(no citations emitted)", s["muted"]))
                continue
            rows = [["Verdict", "Sev.", "Claim & Citation"]]
            for c in claims:
                cite_line = f"<font color='#5E646B'>{c.get('source_doc','')} · p.{c.get('page_number')}</font>"
                quote = (c.get("quote") or "").strip().replace("\n", " ")
                if len(quote) > 280:
                    quote = quote[:280].rstrip() + "…"
                cell = Paragraph(
                    f"{c.get('claim','')}<br/>{cite_line}<br/>"
                    f"<font name='{_FI}'>“{quote}”</font>",
                    s["claim"]
                )
                rows.append([c.get("verdict",""), c.get("severity",""), cell])
            tbl = Table(rows, colWidths=[1.6 * cm, 1.6 * cm, 13.8 * cm])
            tstyle = [
                ("FONTNAME", (0, 0), (-1, -1), _FR),
                ("FONTNAME", (0, 0), (-1, 0), _FB),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), _HEAD),
                ("BOX", (0, 0), (-1, -1), 0.4, _RULE),
                ("INNERGRID", (0, 0), (-1, -1), 0.2, _RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
            for i, c in enumerate(claims, start=1):
                v = c.get("verdict")
                if v in _VERDICT:
                    tstyle.append(("TEXTCOLOR", (0, i), (0, i), _VERDICT[v]))
                    tstyle.append(("FONTNAME", (0, i), (0, i), _FB))
            tbl.setStyle(TableStyle(tstyle))
            flow.append(KeepTogether([tbl, Spacer(1, 6)]))

    # ---- Sign-off ------------------------------------------------------
    flow.append(PageBreak())
    flow.append(Paragraph("OFFICER SIGN-OFF", s["h1"]))
    flow.append(Paragraph(
        "I have reviewed the above AI-assisted analysis. Every claim above is grounded in a "
        "page-cited verbatim quote from the bidder's own submission (or, for the cartel/blacklist "
        "checks, from the seeded registry). My final decision is recorded below.",
        s["body"]))
    flow.append(Spacer(1, 18))
    flow.append(_kv("Officer name:", officer.get("full_name") or "_____________________________________", s))
    flow.append(_kv("Designation:", officer.get("role") or "Procurement Officer", s))
    flow.append(_kv("Ministry / Department:",
                    " / ".join(x for x in (officer.get("ministry"), officer.get("department")) if x) or "—", s))
    flow.append(_kv("Date:", datetime.now(timezone.utc).strftime("%d-%b-%Y"), s))
    flow.append(Spacer(1, 28))
    flow.append(Paragraph("Signature: ________________________________________________", s["body"]))
    flow.append(Spacer(1, 10))
    flow.append(Paragraph(
        "This report was generated automatically by TenderIQ and signed off in print. The underlying "
        "agent runs, citations and recommendation are persisted in the audit database (tables: "
        "agent_runs, citations, recommendations) and may be reproduced on request.",
        s["muted"]))

    # ---- Render --------------------------------------------------------
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=2.0 * cm,
        title=f"TenderIQ Audit Report — {tender.get('title','')[:80]}",
        author="TenderIQ",
    )
    doc.build(flow, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()
