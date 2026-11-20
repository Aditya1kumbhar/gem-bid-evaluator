"""End-to-end offline API integration tests with monkeypatched AI extraction."""

import io
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from reportlab.pdfgen import canvas

from app.main import app
from app.schemas import (
    AtcClause,
    AtcFlag,
    BidderEvidence,
    Criterion,
    DocumentPresent,
    ExtractedField,
    RuleType,
    VoidListItem,
)

client = TestClient(app)


def _make_dummy_pdf(text: str = "Sample GeM Procurement Document") -> bytes:
    """Generate a minimal valid PDF in memory."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, text)
    c.showPage()
    c.save()
    return buf.getvalue()


@pytest.fixture
def mock_gemini(monkeypatch):
    """Monkeypatch gemini_client functions with offline fixture data."""
    fixture_criteria = [
        Criterion(
            id="exp_orders",
            title="Past Experience Orders",
            rule_type=RuleType.MIN_COUNT.value,
            threshold=2,
            unit="orders",
            source_doc="GEM-2026-B-7945477-C5-corrigendum.pdf",
            source_page=2,
            source_quote="Provide at least two orders",
        ),
        Criterion(
            id="oem_authorisation",
            title="OEM Authorisation",
            rule_type=RuleType.OEM_OR_AUTHORISED.value,
            source_doc="GEM-2026-B-7945477-C5-corrigendum.pdf",
            source_page=1,
            source_quote="Authorisation Form /Certificate with OEM",
        ),
    ]

    fixture_void_list = [
        VoidListItem(
            index=2,
            text="Mandating procurement of / from specific Brand / Make / Model / Manufacturer / Dealer except in case of Single Bid / Proprietary Article Certificate (PAC) Buying.",
            source_page=2,
            source_quote="Mandating procurement...",
        ),
        VoidListItem(
            index=8,
            text="Seeking experience from specific organization / department / institute only or from foreign / export experience.",
            source_page=2,
            source_quote="Seeking experience...",
        ),
    ]

    fixture_atc_clauses = [
        AtcClause(
            source_doc="corrigendum.pdf",
            source_page=2,
            text="Provide at least two orders for the same quoted item issued by any of the IITs, NITs or any other government organization.",
        )
    ]

    monkeypatch.setattr("app.gemini_client.extract_criteria", lambda pages, doc_name: fixture_criteria)
    monkeypatch.setattr("app.gemini_client.extract_void_list", lambda pages, doc_name: fixture_void_list)
    monkeypatch.setattr("app.gemini_client.extract_atc_clauses", lambda pages, doc_name: fixture_atc_clauses)
    monkeypatch.setattr(
        "app.gemini_client.classify_atc_clause",
        lambda clause, void_list, hints=None: AtcFlag(
            clause_text=clause.text,
            clause_quote="IITs, NITs",
            matched_void_index=8,
            reason="Ambiguous institute requirement",
            verdict="REVIEW",
            void_quote="seeking experience from specific organization",
        ),
    )

    def _mock_evidence(pages, bidder_name, criteria):
        page_text = pages[0].text if pages else "No text"
        return BidderEvidence(
            bidder_name=bidder_name,
            documents_present=[
                DocumentPresent(doc_type="OEM authorisation", page=1, quote="OEM Auth")
            ],
            fields=[
                ExtractedField(
                    criterion_id="exp_orders",
                    disputed=False,
                    guard_passed=True,
                    page=1,
                    quote=page_text,
                    raw_text="2 orders",
                    value=2,
                )
            ],
        )

    monkeypatch.setattr("app.gemini_client.extract_bidder_evidence", _mock_evidence)


def test_tenders_and_bidders_upload() -> None:
    """Verify document upload validation, page counting, and bidder pack registration."""
    pdf1 = _make_dummy_pdf("Main Bid Content Page")
    pdf2 = _make_dummy_pdf("Corrigendum Content Page")

    # Reject non-PDF upload
    bad_resp = client.post(
        "/tenders",
        files=[("files", ("bad.txt", b"plain text", "text/plain"))],
    )
    assert bad_resp.status_code == 400
    assert "Only PDF files are accepted" in bad_resp.json()["detail"]

    # Upload main bid first, then corrigendum
    resp = client.post(
        "/tenders",
        files=[
            ("files", ("main_bid.pdf", pdf1, "application/pdf")),
            ("files", ("corrigendum.pdf", pdf2, "application/pdf")),
        ],
    )
    assert resp.status_code == 200
    data = resp.json()
    tender_id = data["tender_id"]
    assert len(data["documents"]) == 2
    assert data["total_pages"] == 2

    # Add bidder pack
    bidder_pdf = _make_dummy_pdf("Bidder Alpha Technical Credentials")
    b_resp = client.post(
        f"/tenders/{tender_id}/bidders",
        data={"name": "Bidder Alpha"},
        files=[("files", ("evidence.pdf", bidder_pdf, "application/pdf"))],
    )
    assert b_resp.status_code == 200
    assert b_resp.json()["bidder_name"] == "Bidder Alpha"

    # Add bidder to unknown tender returns 404
    missing_resp = client.post(
        "/tenders/unknown_id/bidders",
        data={"name": "Ghost"},
        files=[("files", ("evidence.pdf", bidder_pdf, "application/pdf"))],
    )
    assert missing_resp.status_code == 404


def test_e2e_evaluation_cache_and_exports(mock_gemini, tmp_path, monkeypatch) -> None:
    """Verify full evaluation pipeline, replay cache, CSV export, and HTML report."""
    monkeypatch.setattr("app.jobs.CACHE_DIR", tmp_path / "cache")
    pdf1 = _make_dummy_pdf("Main Bid Terms")
    pdf2 = _make_dummy_pdf("Corrigendum Terms")
    evidence_pdf = _make_dummy_pdf("Provide at least two orders")

    # 1. Create tender & bidder
    t_resp = client.post(
        "/tenders",
        files=[
            ("files", ("main.pdf", pdf1, "application/pdf")),
            ("files", ("corrigendum.pdf", pdf2, "application/pdf")),
        ],
    )
    tender_id = t_resp.json()["tender_id"]

    client.post(
        f"/tenders/{tender_id}/bidders",
        data={"name": "Bidder Alpha"},
        files=[("files", ("evidence.pdf", evidence_pdf, "application/pdf"))],
    )

    # 2. Evaluate (First run -> cached=False)
    eval_resp = client.post(f"/tenders/{tender_id}/evaluate")
    assert eval_resp.status_code == 200
    res = eval_resp.json()
    assert res["degraded"] is False
    assert res["cached"] is False
    assert len(res["criteria"]) == 2
    assert len(res["results"]) == 2

    # 3. Evaluate again (Second run -> cached=True)
    cached_resp = client.post(f"/tenders/{tender_id}/evaluate")
    assert cached_resp.status_code == 200
    assert cached_resp.json()["cached"] is True

    # 4. Matrix CSV download
    csv_resp = client.get(f"/tenders/{tender_id}/matrix.csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "attachment" in csv_resp.headers["content-disposition"]
    assert "Criterion,Bidder Alpha" in csv_resp.text

    # 5. HTML Report view
    html_resp = client.get(f"/tenders/{tender_id}/report")
    assert html_resp.status_code == 200
    assert "text/html" in html_resp.headers["content-type"]
    assert "BidParakh Tender Evaluation Report" in html_resp.text
    assert "Bidder Alpha" in html_resp.text


def test_degraded_path_never_returns_500(monkeypatch) -> None:
    """Verify that unexpected AI exceptions gracefully degrade to 200 with REVIEW verdicts."""
    from app.gemini_client import ExtractionError

    def _failing_extract(*args, **kwargs):
        raise ExtractionError("API quota exhausted or network error")

    monkeypatch.setattr("app.gemini_client.extract_criteria", _failing_extract)
    monkeypatch.setattr("app.config.is_ai_configured", lambda: True)

    pdf = _make_dummy_pdf("Tender content")
    t_resp = client.post(
        "/tenders",
        files=[("files", ("tender.pdf", pdf, "application/pdf"))],
    )
    tender_id = t_resp.json()["tender_id"]
    client.post(
        f"/tenders/{tender_id}/bidders",
        data={"name": "DegradedBidder"},
        files=[("files", ("doc.pdf", pdf, "application/pdf"))],
    )

    eval_resp = client.post(f"/tenders/{tender_id}/evaluate")
    assert eval_resp.status_code == 200  # NEVER 500!
    data = eval_resp.json()
    assert data["degraded"] is True
    assert "ExtractionError" in data["warnings"]
    assert data["results"][0]["verdict"] == "REVIEW"
