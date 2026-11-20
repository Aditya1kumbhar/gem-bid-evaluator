"""Live ATC legality classification tests against the four golden clauses."""

import os
from pathlib import Path
import time
from typing import List
import pytest

from app.atc_flag import flag_clause
from app.gemini_client import extract_void_list
from app.pdf_text import extract_pages
from app.schemas import AtcClause, VoidListItem

RUN_LIVE = os.environ.get("RUN_LIVE") == "1"
HERO_PDF = Path("fixtures/GEM-2026-B-7945477-C5-corrigendum.pdf")

pytestmark = pytest.mark.skipif(
    not RUN_LIVE,
    reason="Live Gemini tests skipped unless RUN_LIVE=1",
)


@pytest.fixture(scope="module")
def hero_void_list() -> List[VoidListItem]:
    """Extract and cache the 14-item void list from the hero corrigendum."""
    assert HERO_PDF.is_file(), f"Hero PDF missing at {HERO_PDF}"
    pages = extract_pages(HERO_PDF.read_bytes())
    void_list = extract_void_list(pages, HERO_PDF.name)
    assert len(void_list) == 14
    return void_list


def test_hero_clause_4_returns_review(hero_void_list: List[VoidListItem]) -> None:
    """Verify hero clause 4 (IITs/NITs or any govt org) returns REVIEW due to ambiguity."""
    clause = AtcClause(
        source_doc=HERO_PDF.name,
        source_page=2,
        text="Provide at least two orders for the same quoted item issued by any of the IITs, NITs or any other government organization.",
    )
    flag = flag_clause(clause, hero_void_list)
    time.sleep(3)
    assert flag.verdict == "REVIEW"
    assert flag.matched_void_index == 8


def test_tender_fee_clause_returns_flag(hero_void_list: List[VoidListItem]) -> None:
    """Verify synthetic tender fee clause returns FLAG under Disclaimer item 11."""
    clause = AtcClause(
        source_doc="synthetic_fee.pdf",
        source_page=1,
        text="The bidder shall pay a tender fee of Rs 5,000 with the bid",
    )
    flag = flag_clause(clause, hero_void_list)
    time.sleep(3)
    assert flag.verdict == "FLAG"
    assert flag.matched_void_index == 11


def test_brand_clause_returns_flag(hero_void_list: List[VoidListItem]) -> None:
    """Verify synthetic brand restriction clause returns FLAG under Disclaimer item 2."""
    clause = AtcClause(
        source_doc="synthetic_brand.pdf",
        source_page=1,
        text="Only HP make laptops will be accepted",
    )
    flag = flag_clause(clause, hero_void_list)
    time.sleep(3)
    assert flag.verdict == "FLAG"
    assert flag.matched_void_index == 2


def test_escalation_matrix_clause_returns_clear(hero_void_list: List[VoidListItem]) -> None:
    """Verify synthetic escalation matrix clause returns CLEAR as it is permissible."""
    clause = AtcClause(
        source_doc="synthetic_escalation.pdf",
        source_page=1,
        text="The bidder must provide an escalation matrix for service support",
    )
    flag = flag_clause(clause, hero_void_list)
    time.sleep(3)
    assert flag.verdict == "CLEAR"
    assert flag.matched_void_index is None
