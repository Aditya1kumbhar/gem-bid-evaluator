"""Draft speaking-order lines for rejection of failing bids."""

from app.schemas import Criterion, CriterionResult


def line_for(bidder_name: str, criterion: Criterion, result: CriterionResult) -> str:
    """Format an exact template-based speaking order rejection line for a FAIL verdict."""
    return (
        f"The bid of {bidder_name} is rejected under {criterion.title} "
        f"({criterion.source_doc}, page {criterion.source_page}): {result.reason} "
        f"Criterion as per tender: {criterion.source_quote}"
    )
