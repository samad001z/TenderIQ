"""PDF -> page images, the foundation of TenderIQ's page-accurate citations.

Each PDF page is rendered to a PIL image at 2x DPI so Gemini reads clean text and
we can cite by 1-indexed page number reliably. `interleave_pages` builds the
[Image, "PAGE 1", Image, "PAGE 2", ...] parts list the agents feed to Gemini.
"""

from __future__ import annotations

from typing import Any, List, Tuple

import fitz  # PyMuPDF
from PIL import Image

# 2x render scale (~144 DPI for a 72-DPI PDF) — clean OCR by the model without
# bloating payloads.
DEFAULT_SCALE = 2.0


def pdf_to_page_images(pdf_path: str, scale: float = DEFAULT_SCALE) -> List[Tuple[int, Image.Image]]:
    """Render every page of `pdf_path` to a PIL image.

    Returns a list of (page_number, image) where page_number is 1-indexed.
    """
    doc = fitz.open(pdf_path)
    try:
        matrix = fitz.Matrix(scale, scale)
        out: List[Tuple[int, Image.Image]] = []
        for index, page in enumerate(doc):
            pix = page.get_pixmap(matrix=matrix)
            mode = "RGBA" if pix.alpha else "RGB"
            img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
            if mode == "RGBA":
                img = img.convert("RGB")
            out.append((index + 1, img))  # 1-indexed page numbers
        return out
    finally:
        doc.close()


def interleave_pages(pages: List[Tuple[int, Image.Image]]) -> List[Any]:
    """Build the page-labeled parts list for a Gemini multimodal call.

    [img1, "PAGE 1", img2, "PAGE 2", ...] — labels INTERLEAVED so the model can
    reliably tag each citation with the correct page number.
    """
    parts: List[Any] = []
    for page_number, image in pages:
        parts.append(image)
        parts.append(f"PAGE {page_number}")
    return parts
