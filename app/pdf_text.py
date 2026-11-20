"""PDF text extraction and normalisation utilities."""

import io
import re
from typing import List
import pypdf
from app.schemas import PageText


def normalize(text: str) -> str:
    """Normalize text by converting quotes, collapsing whitespace, and lowercasing."""
    if not text:
        return ""
    # Convert curly single/double quotes and angle quotes to straight quotes
    replacements = {
        "\u201c": '"', "\u201d": '"', "\u00ab": '"', "\u00bb": '"',
        "\u2018": "'", "\u2019": "'", "`": "'"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.lower()
    return re.sub(r"\s+", " ", text).strip()


def extract_pages(pdf_bytes: bytes) -> List[PageText]:
    """Extract 1-based indexed text pages from raw PDF bytes."""
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    pages: List[PageText] = []
    for idx, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        pages.append(PageText(page=idx + 1, text=page_text))
    return pages


def has_text_layer(pages: List[PageText]) -> bool:
    """Return True if total non-whitespace characters across pages is at least 200."""
    total_chars = sum(len(re.sub(r"\s", "", p.text)) for p in pages)
    return total_chars >= 200
