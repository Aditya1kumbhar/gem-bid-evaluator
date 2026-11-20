"""Unit tests for PDF text extraction and normalization."""

import io
from pathlib import Path
import pytest
from reportlab.pdfgen import canvas

from app.pdf_text import extract_pages, has_text_layer, normalize
from app.schemas import PageText


def test_normalize_quotes_and_whitespace() -> None:
    """Verify quote conversions and whitespace collapsing."""
    raw = '  “Special Quote” and ‘Single Quote’ \n\t with   spaces   '
    expected = '"special quote" and \'single quote\' with spaces'
    assert normalize(raw) == expected


def test_has_text_layer() -> None:
    """Verify threshold of 200 non-whitespace characters."""
    short_pages = [PageText(page=1, text="Hello world!")]
    assert has_text_layer(short_pages) is False

    long_text = "Standard procurement text clause. " * 10
    long_pages = [PageText(page=1, text=long_text)]
    assert has_text_layer(long_pages) is True


def test_extract_pages_in_memory() -> None:
    """Verify extract_pages on an in-memory generated PDF."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, "Page 1 Content: Bid Evaluation")
    c.showPage()
    c.drawString(100, 750, "Page 2 Content: Null and Void Conditions")
    c.showPage()
    c.save()

    pdf_bytes = buf.getvalue()
    pages = extract_pages(pdf_bytes)
    assert len(pages) == 2
    assert pages[0].page == 1
    assert "Page 1 Content" in pages[0].text
    assert pages[1].page == 2
    assert "Null and Void" in pages[1].text


HERO_PDF_PATH = Path("fixtures/GEM-2026-B-7945477-C5-corrigendum.pdf")


@pytest.mark.skipif(not HERO_PDF_PATH.is_file(), reason="Hero PDF not yet placed by user in fixtures/")
def test_hero_pdf_golden_spec() -> None:
    """Verify hero PDF has 3 pages and its text contains 'null and void' (or 'null & void')."""
    pdf_bytes = HERO_PDF_PATH.read_bytes()
    pages = extract_pages(pdf_bytes)
    assert len(pages) == 3
    full_text = " ".join(p.text for p in pages).lower()
    assert "null & void" in full_text or "null and void" in full_text
