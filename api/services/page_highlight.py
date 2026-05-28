"""Server-side page highlighting for citations.

The native browser PDF viewer (used elsewhere in the UI) can't draw a JS overlay,
so when the officer clicks a citation we render that page to a PNG with PyMuPDF
and stroke a translucent gold rectangle over the bounding box(es) of the quoted
text. This is the "gold rectangle over the bbox" promised by the Phase-6 spec —
real rects from page.search_for, not a fake overlay.

Robust to LLM paraphrase: if the verbatim quote isn't found, we progressively
truncate the search string until something matches; if nothing matches at all,
we still return the page (no rectangle) so the officer at least sees the page.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Iterable

import fitz  # PyMuPDF
from PIL import Image, ImageDraw

# Gold from the design tokens (#C8A14A). Translucent fill + solid stroke.
_GOLD_FILL = (200, 161, 74, 90)
_GOLD_STROKE = (200, 161, 74, 230)
_ZOOM = 2.0  # 2x render → ~144 DPI


@dataclass
class HighlightResult:
    png: bytes
    page_count: int
    matched: bool   # True if at least one rectangle was drawn
    used_text: str  # what we ultimately searched for (debugging aid)


def _normalize(s: str) -> str:
    """Collapse whitespace; normalize curly quotes / dashes."""
    if not s:
        return ""
    s = s.replace(" ", " ")
    s = re.sub(r"[‘’‚‛]", "'", s)
    s = re.sub(r"[“”„‟]", '"', s)
    s = re.sub(r"[–—]", "-", s)
    return re.sub(r"\s+", " ", s).strip()


def _candidates(quote: str) -> Iterable[str]:
    """Search strings to try, from most-specific to least. Stops yielding very short ones."""
    q = _normalize(quote)
    if not q:
        return
    yield q
    # Drop leading/trailing punctuation
    yield q.strip('.,;:()[]"\'')
    # Progressive prefixes (head of the quote tends to be the recognizable phrase)
    for n in (200, 140, 100, 80, 60, 45, 35, 25):
        if len(q) > n:
            yield q[:n]
    # First-N words variants
    words = q.split()
    for n in (10, 8, 6, 5, 4):
        if len(words) > n:
            yield " ".join(words[:n])


def find_rects(page: fitz.Page, quote: str) -> tuple[list[fitz.Rect], str]:
    """Try progressively-looser searches for `quote` on `page`. Returns (rects, used_text)."""
    for cand in _candidates(quote):
        try:
            rects = page.search_for(cand, quads=False)
        except Exception:
            rects = []
        if rects:
            return rects, cand
    return [], ""


def highlight_page(pdf_bytes: bytes, page_number: int, quote: str) -> HighlightResult:
    """Render `page_number` (1-indexed) as PNG with gold rectangles over the quote."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        idx = max(1, min(page_number, doc.page_count)) - 1
        page = doc[idx]
        rects, used = find_rects(page, quote)

        pix = page.get_pixmap(matrix=fitz.Matrix(_ZOOM, _ZOOM), alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("RGBA")
        if rects:
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            for r in rects:
                box = (r.x0 * _ZOOM - 2, r.y0 * _ZOOM - 2, r.x1 * _ZOOM + 2, r.y1 * _ZOOM + 2)
                draw.rectangle(box, fill=_GOLD_FILL, outline=_GOLD_STROKE, width=3)
            img = Image.alpha_composite(img, overlay)

        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG", optimize=True)
        return HighlightResult(
            png=buf.getvalue(),
            page_count=doc.page_count,
            matched=bool(rects),
            used_text=used,
        )
    finally:
        doc.close()
