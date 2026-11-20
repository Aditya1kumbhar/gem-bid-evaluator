"""Unit tests for evidence guard quote verification."""

from app.evidence_guard import apply_guard, quote_exists
from app.schemas import ExtractedField, PageText


def test_golden_guard_cases() -> None:
    """Verify golden guard cases: case/whitespace insensitivity and digit alteration failure."""
    page_text = "The bidder must possess 2 years of proven operational experience in IT services."

    # Case & whitespace difference passes
    assert quote_exists("BIDDER  MUST POSSESS   2 years of proven operational experience", page_text) is True

    # Quote with one digit changed fails
    assert quote_exists("bidder must possess 3 years of proven operational experience", page_text) is False


def test_guard_spacing_relaxation() -> None:
    """Verify pass 2 handles broken PDF text layer spacing."""
    broken_pdf_text = "The bid der must submit OEM au thor isation certificate."
    assert quote_exists("bidder must submit OEM authorisation certificate", broken_pdf_text) is True


def test_apply_guard() -> None:
    """Verify apply_guard marks guard_passed correctly across valid and out-of-range pages."""
    pages = [
        PageText(page=1, text="Tenderer turnover must exceed Rs 50 lakh per annum."),
        PageText(page=2, text="OEM authorisation letter attached herewith.")
    ]
    fields = [
        ExtractedField(
            criterion_id="turnover",
            page=1,
            quote="turnover must exceed Rs 50 lakh",
            raw_text="50 lakh",
            value=5000000.0
        ),
        ExtractedField(
            criterion_id="oem_auth",
            page=2,
            quote="OEM authorisation letter attached",
            raw_text="attached",
            value=None
        ),
        ExtractedField(
            criterion_id="invalid_page",
            page=99,
            quote="turnover must exceed Rs 50 lakh",
            raw_text="50 lakh",
            value=5000000.0
        ),
        ExtractedField(
            criterion_id="altered_quote",
            page=1,
            quote="turnover must exceed Rs 90 lakh",
            raw_text="90 lakh",
            value=9000000.0
        ),
    ]

    guarded = apply_guard(fields, pages)
    assert guarded[0].guard_passed is True
    assert guarded[1].guard_passed is True
    assert guarded[2].guard_passed is False  # out of range page
    assert guarded[3].guard_passed is False  # altered quote
