"""Unit tests for matrix building, CSV export, and HTML table generation."""

from app.matrix import build_matrix, to_csv, to_html
from app.schemas import Criterion, CriterionResult, RuleType, Verdict


def test_build_matrix_and_exports() -> None:
    """Verify matrix dimensions, CSV content, and HTML table styling."""
    crit1 = Criterion(
        id="exp_orders",
        title="Experience Orders",
        rule_type=RuleType.MIN_COUNT.value,
        source_doc="doc.pdf",
        source_page=1,
        source_quote="2 orders",
    )
    crit2 = Criterion(
        id="oem_auth",
        title="OEM Authorisation",
        rule_type=RuleType.OEM_OR_AUTHORISED.value,
        source_doc="doc.pdf",
        source_page=1,
        source_quote="OEM auth",
    )
    criteria = [crit1, crit2]

    results = [
        CriterionResult(bidder_name="Bidder A", criterion_id="exp_orders", verdict=Verdict.PASS, reason="Passed"),
        CriterionResult(bidder_name="Bidder A", criterion_id="oem_auth", verdict=Verdict.PASS, reason="Passed"),
        CriterionResult(bidder_name="Bidder B", criterion_id="exp_orders", verdict=Verdict.FAIL, reason="Failed"),
        CriterionResult(bidder_name="Bidder B", criterion_id="oem_auth", verdict=Verdict.REVIEW, reason="Review"),
    ]

    bidder_names = ["Bidder A", "Bidder B"]
    matrix = build_matrix(criteria, results)

    assert len(matrix) == 2
    assert matrix[0] == ["Experience Orders", "PASS", "FAIL"]
    assert matrix[1] == ["OEM Authorisation", "PASS", "REVIEW"]

    # Verify CSV export
    csv_str = to_csv(matrix, bidder_names)
    assert "Criterion,Bidder A,Bidder B" in csv_str
    assert "Experience Orders,PASS,FAIL" in csv_str
    assert "OEM Authorisation,PASS,REVIEW" in csv_str

    # Verify HTML export
    html_str = to_html(matrix, bidder_names)
    assert "<table" in html_str
    assert "Bidder A" in html_str
    assert "Bidder B" in html_str
    assert "#d4edda" in html_str  # PASS green
    assert "#f8d7da" in html_str  # FAIL red
    assert "#fff3cd" in html_str  # REVIEW amber
