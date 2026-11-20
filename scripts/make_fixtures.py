"""Generate synthetic bidder evidence PDFs using reportlab for offline testing."""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

FIXTURES_DIR = Path("fixtures")


def generate_pass_pdf(dest: Path) -> None:
    """Generate bidder_pass.pdf with 2 completed orders, OEM auth, and undertaking."""
    c = canvas.Canvas(str(dest), pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Technical Bid Submission - PassBidder Pvt Ltd")
    c.setFont("Helvetica", 11)
    c.drawString(50, 710, "1. Experience Proof:")
    c.drawString(70, 690, "Successfully completed 2 government orders for IT equipment.")
    c.drawString(70, 670, "Contract copy with invoices self-certified by bidder attached herewith.")
    c.drawString(70, 650, "Execution certificate by client with contract value verified.")
    c.drawString(50, 610, "2. Manufacturer Authorization:")
    c.drawString(70, 590, "Authorisation Form / Certificate with OEM details furnished.")
    c.drawString(50, 550, "3. Financial Standing Undertaking:")
    c.drawString(70, 530, "Undertaking to the effect of financial standing and no liquidation.")
    c.drawString(50, 490, "4. Annual Financial Turnover:")
    c.drawString(70, 470, "FY 2023-24: Rs 65,00,000 | FY 2022-23: Rs 70,00,000 | FY 2021-22: Rs 60,00,000")
    c.showPage()
    c.save()


def generate_fail_pdf(dest: Path) -> None:
    """Generate bidder_fail.pdf with only 1 order and missing OEM authorization."""
    c = canvas.Canvas(str(dest), pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Technical Bid Submission - FailBidder Pvt Ltd")
    c.setFont("Helvetica", 11)
    c.drawString(50, 710, "1. Experience Proof:")
    c.drawString(70, 690, "Successfully completed 1 order only for IT equipment.")
    c.drawString(70, 670, "Contract copy with single invoice attached.")
    c.drawString(50, 630, "2. Manufacturer Authorization:")
    c.drawString(70, 610, "Not applicable / Reseller without OEM authorization.")
    c.drawString(50, 570, "3. Financial Standing Undertaking:")
    c.drawString(70, 550, "Undertaking to the effect of financial standing and no liquidation.")
    c.showPage()
    c.save()


def generate_review_pdf(dest: Path) -> None:
    """Generate bidder_review.pdf with mismatched experience quote and only 2 years turnover."""
    c = canvas.Canvas(str(dest), pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Technical Bid Submission - ReviewBidder Pvt Ltd")
    c.setFont("Helvetica", 11)
    c.drawString(50, 710, "1. Experience Proof:")
    c.drawString(70, 690, "Successfully completed two commercial contracts in hardware supply.")
    c.drawString(70, 670, "Contract copy attached.")
    c.drawString(50, 630, "2. Annual Financial Turnover:")
    c.drawString(70, 610, "Annual Turnover FY 2023-24: Rs 60,00,000")
    c.drawString(70, 590, "Annual Turnover FY 2022-23: Rs 55,00,000")
    c.showPage()
    c.save()


def make_all_fixtures() -> None:
    """Create all three synthetic bidder PDFs inside fixtures/."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    generate_pass_pdf(FIXTURES_DIR / "bidder_pass.pdf")
    generate_fail_pdf(FIXTURES_DIR / "bidder_fail.pdf")
    generate_review_pdf(FIXTURES_DIR / "bidder_review.pdf")


if __name__ == "__main__":
    make_all_fixtures()
    print("Generated bidder_pass.pdf, bidder_fail.pdf, and bidder_review.pdf under fixtures/")
