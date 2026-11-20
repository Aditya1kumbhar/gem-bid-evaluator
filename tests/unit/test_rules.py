"""Unit tests for the rules engine against synthetic bidder packs."""

import json
from pathlib import Path
from app.rules import evaluate
from app.schemas import BidderEvidence, Criterion, RuleType, Verdict

FIXTURES_DIR = Path("fixtures/extracted")

CRIT_EXP_ORDERS = Criterion(
    id="exp_orders",
    title="Past Experience Orders",
    rule_type=RuleType.MIN_COUNT.value,
    threshold=2,
    unit="orders",
    source_doc="GEM-2026-B-7945477-C5-corrigendum.pdf",
    source_page=2,
    source_quote="Provide at least two orders for the same quoted item",
)

CRIT_OEM_AUTH = Criterion(
    id="oem_authorisation",
    title="OEM Authorisation",
    rule_type=RuleType.OEM_OR_AUTHORISED.value,
    source_doc="GEM-2026-B-7945477-C5-corrigendum.pdf",
    source_page=1,
    source_quote="Authorisation Form /Certificate with OEM",
)

CRIT_UNDERTAKING = Criterion(
    id="liquidation_undertaking",
    title="No Liquidation Undertaking",
    rule_type=RuleType.UNDERTAKING_PRESENT.value,
    source_doc="GEM-2026-B-7945477-C5-corrigendum.pdf",
    source_page=1,
    source_quote="Bidder to upload undertaking to this effect with bid.",
)

CRIT_TURNOVER = Criterion(
    id="turnover",
    title="Annual Average Turnover",
    rule_type=RuleType.MIN_AVG_VALUE.value,
    threshold=5000000.0,
    unit="INR",
    source_doc="GEM-2026-B-7945477-main.pdf",
    source_page=10,
    source_quote="Average annual turnover of Rs 50 lakh over last 3 years",
)

CRIT_MANUAL = Criterion(
    id="custom_clause",
    title="Custom Discretionary Check",
    rule_type=RuleType.MANUAL.value,
    source_doc="GEM-2026-B-7945477-main.pdf",
    source_page=15,
    source_quote="Discretionary officer check",
)


def test_bidder_pass_pack() -> None:
    """Verify bidder_pass fixture yields PASS across all evaluated criteria."""
    data = json.loads((FIXTURES_DIR / "bidder_pass.json").read_text(encoding="utf-8"))
    evidence = BidderEvidence(**data)

    res_exp = evaluate(CRIT_EXP_ORDERS, evidence)
    assert res_exp.verdict == Verdict.PASS
    assert res_exp.speaking_order_line is None

    res_oem = evaluate(CRIT_OEM_AUTH, evidence)
    assert res_oem.verdict == Verdict.PASS

    res_und = evaluate(CRIT_UNDERTAKING, evidence)
    assert res_und.verdict == Verdict.PASS


def test_bidder_fail_pack() -> None:
    """Verify bidder_fail fixture yields FAIL with speaking order lines."""
    data = json.loads((FIXTURES_DIR / "bidder_fail.json").read_text(encoding="utf-8"))
    evidence = BidderEvidence(**data)

    res_exp = evaluate(CRIT_EXP_ORDERS, evidence)
    assert res_exp.verdict == Verdict.FAIL
    assert res_exp.speaking_order_line is not None
    assert "FailBidder Pvt Ltd" in res_exp.speaking_order_line
    assert "rejected under Past Experience Orders" in res_exp.speaking_order_line

    res_oem = evaluate(CRIT_OEM_AUTH, evidence)
    assert res_oem.verdict == Verdict.FAIL
    assert res_oem.speaking_order_line is not None
    assert "rejected under OEM Authorisation" in res_oem.speaking_order_line


def test_bidder_review_pack() -> None:
    """Verify bidder_review fixture yields REVIEW for unverified quotes and missing yearly values."""
    data = json.loads((FIXTURES_DIR / "bidder_review.json").read_text(encoding="utf-8"))
    evidence = BidderEvidence(**data)

    res_exp = evaluate(CRIT_EXP_ORDERS, evidence)
    assert res_exp.verdict == Verdict.REVIEW
    assert res_exp.reason == "No verified evidence found"
    assert res_exp.speaking_order_line is None

    res_turnover = evaluate(CRIT_TURNOVER, evidence)
    assert res_turnover.verdict == Verdict.REVIEW
    assert "fewer than 3 required" in res_turnover.reason
    assert res_turnover.speaking_order_line is None


def test_manual_rule_type() -> None:
    """Verify MANUAL rule_type always returns REVIEW with officer judgement reason."""
    evidence = BidderEvidence(bidder_name="AnyBidder")
    res = evaluate(CRIT_MANUAL, evidence)
    assert res.verdict == Verdict.REVIEW
    assert res.reason == "Needs officer judgement"
    assert res.speaking_order_line is None
