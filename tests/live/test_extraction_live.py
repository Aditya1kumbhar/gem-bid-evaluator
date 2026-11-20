"""Live extraction tests against Gemini using the hero corrigendum."""

import os
from pathlib import Path
import pytest
from app.gemini_client import extract_criteria, extract_void_list
from app.pdf_text import extract_pages

RUN_LIVE = os.environ.get("RUN_LIVE") == "1"
HERO_PDF = Path("fixtures/GEM-2026-B-7945477-C5-corrigendum.pdf")

pytestmark = pytest.mark.skipif(
    not RUN_LIVE,
    reason="Live Gemini tests skipped unless RUN_LIVE=1",
)


def test_extract_void_list_live() -> None:
    """Verify live extraction returns exactly 14 null-and-void disclaimer items."""
    assert HERO_PDF.is_file(), f"Hero PDF missing at {HERO_PDF}"
    pages = extract_pages(HERO_PDF.read_bytes())
    void_list = extract_void_list(pages, HERO_PDF.name)

    assert len(void_list) == 14
    for idx, item in enumerate(void_list, start=1):
        assert item.index == idx
        assert item.text
        assert item.source_page in (2, 3)


def test_extract_criteria_live() -> None:
    """Verify live extraction extracts exp_orders with rule_type MIN_COUNT and threshold 2."""
    assert HERO_PDF.is_file(), f"Hero PDF missing at {HERO_PDF}"
    pages = extract_pages(HERO_PDF.read_bytes())
    criteria = extract_criteria(pages, HERO_PDF.name)

    crit_map = {c.id: c for c in criteria}
    assert "exp_orders" in crit_map, f"Criteria extracted: {list(crit_map.keys())}"

    exp = crit_map["exp_orders"]
    assert exp.rule_type == "MIN_COUNT"
    assert exp.threshold == 2
    assert exp.source_page == 2
