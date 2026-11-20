"""Unit tests for criteria and void list resolution across documents."""

from app.resolver import resolve_criteria, resolve_void_list
from app.schemas import Criterion, RuleType, VoidListItem


def test_golden_resolver_supersedes() -> None:
    """Verify corrigendum overrides older criterion threshold and records supersedes."""
    older_criterion = Criterion(
        id="exp_orders",
        title="Experience in Orders",
        rule_type=RuleType.MIN_COUNT.value,
        threshold=3,
        unit="orders",
        source_doc="GEM-2026-B-7945477-main.pdf",
        source_page=12,
        source_quote="Bidder must have 3 orders",
        supersedes=[],
    )
    corrigendum_criterion = Criterion(
        id="exp_orders",
        title="Experience in Orders (Updated)",
        rule_type=RuleType.MIN_COUNT.value,
        threshold=2,
        unit="orders",
        source_doc="GEM-2026-B-7945477-C5-corrigendum.pdf",
        source_page=2,
        source_quote="Provide at least two orders for the same quoted item",
        supersedes=[],
    )
    older_unique = Criterion(
        id="turnover",
        title="Turnover",
        rule_type=RuleType.MIN_AVG_VALUE.value,
        threshold=5000000.0,
        unit="INR",
        source_doc="GEM-2026-B-7945477-main.pdf",
        source_page=14,
        source_quote="Turnover must be 50 Lakh",
        supersedes=[],
    )

    docs = [[older_criterion, older_unique], [corrigendum_criterion]]
    resolved = resolve_criteria(docs)

    res_map = {c.id: c for c in resolved}
    assert len(res_map) == 2
    assert "turnover" in res_map
    assert res_map["turnover"].threshold == 5000000.0

    exp = res_map["exp_orders"]
    assert exp.threshold == 2
    assert exp.source_doc == "GEM-2026-B-7945477-C5-corrigendum.pdf"
    assert "exp_orders" in exp.supersedes


def test_resolve_void_list() -> None:
    """Verify the void list from the last non-empty document is selected."""
    list1 = [VoidListItem(index=1, text="Item 1", source_page=2, source_quote="Item 1")]
    list2 = [
        VoidListItem(index=1, text="Updated Item 1", source_page=2, source_quote="Updated Item 1"),
        VoidListItem(index=2, text="Updated Item 2", source_page=2, source_quote="Updated Item 2"),
    ]
    empty_list: list[VoidListItem] = []

    # Last non-empty wins
    assert resolve_void_list([list1, list2, empty_list]) == list2
    assert resolve_void_list([list1]) == list1
    assert resolve_void_list([empty_list]) == []
