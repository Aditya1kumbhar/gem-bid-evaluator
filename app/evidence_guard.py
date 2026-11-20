"""Evidence guard for verifying extracted quotes against PDF page text."""

from typing import List
from app.pdf_text import normalize
from app.schemas import ExtractedField, PageText


def quote_exists(quote: str, page_text: str) -> bool:
    """Verify quote exists in page text via strict substring and space-relaxed passes."""
    if not quote or not page_text:
        return False
    norm_quote = normalize(quote)
    norm_page = normalize(page_text)
    if not norm_quote:
        return False

    # Pass 1: Direct substring check on normalized strings
    if norm_quote in norm_page:
        return True

    # Pass 2: Relaxed substring check without spaces (fixes broken PDF text spacing)
    spaceless_quote = norm_quote.replace(" ", "")
    spaceless_page = norm_page.replace(" ", "")
    return spaceless_quote in spaceless_page


def apply_guard(fields: List[ExtractedField], pages: List[PageText]) -> List[ExtractedField]:
    """Verify each extracted field's quote against the cited page text."""
    page_map = {p.page: p.text for p in pages}
    for field in fields:
        if field.page in page_map:
            field.guard_passed = quote_exists(field.quote, page_map[field.page])
        else:
            field.guard_passed = False
    return fields
