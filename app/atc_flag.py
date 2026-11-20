"""ATC clause legality classification against GeM null-and-void Disclaimer rules."""

from typing import List, Optional
from app.evidence_guard import quote_exists
import app.gemini_client as gemini_client
from app.schemas import AtcClause, AtcFlag, AtcVerdict, VoidListItem


def _generate_candidate_hints(clause_text: str, void_list: List[VoidListItem]) -> List[str]:
    """Generate deterministic candidate hints based on known disclaimer triggers."""
    hints: List[str] = []
    text_lower = clause_text.lower()
    if "tender fee" in text_lower or "bid participation fee" in text_lower:
        for v in void_list:
            if "fee" in v.text.lower():
                hints.append(f"Clause mentions fee -> matches item {v.index}: '{v.text}'")
    if "only" in text_lower and any(kw in text_lower for kw in ("make", "brand", "model", "hp", "dell")):
        for v in void_list:
            if "brand" in v.text.lower() or "make" in v.text.lower():
                hints.append(f"Clause restricts brand/make -> matches item {v.index}: '{v.text}'")
    return hints


def _is_clause_ambiguous(clause_text: str) -> bool:
    """Check if clause ambiguously names specific institutions while permitting generic government bodies."""
    lower = clause_text.lower()
    has_specific = "iit" in lower or "nit" in lower or "specific" in lower
    has_generic = "any other government" in lower or "any government" in lower or "other government" in lower
    return has_specific and has_generic


def flag_clause(clause: AtcClause, void_list: List[VoidListItem]) -> AtcFlag:
    """Classify an ATC clause, verify quotes in code, and return a validated AtcFlag."""
    hints = _generate_candidate_hints(clause.text, void_list)
    draft = gemini_client.classify_atc_clause(clause, void_list, hints=hints)

    # 1. No void item matched -> CLEAR
    if draft.matched_void_index is None:
        draft.verdict = AtcVerdict.CLEAR.value
        return draft

    # Locate the matched void disclaimer item
    matched_item: Optional[VoidListItem] = next(
        (v for v in void_list if v.index == draft.matched_void_index), None
    )
    if not matched_item:
        draft.verdict = AtcVerdict.REVIEW.value
        draft.reason = f"Matched void index {draft.matched_void_index} not found in void list."
        return draft

    # 2. Dual quote verification in code
    clause_quote_ok = bool(draft.clause_quote and quote_exists(draft.clause_quote, clause.text))
    void_quote_ok = bool(draft.void_quote and quote_exists(draft.void_quote, matched_item.text))

    if not clause_quote_ok or not void_quote_ok:
        draft.verdict = AtcVerdict.REVIEW.value
        draft.reason = (
            f"Quote verification failed (clause_quote_verified={clause_quote_ok}, "
            f"void_quote_verified={void_quote_ok}). Needs officer review."
        )
        return draft

    # 3. Ambiguity check (e.g. naming specific orgs but also allowing any govt organisation)
    if _is_clause_ambiguous(clause.text) or "disputed" in draft.reason.lower():
        draft.verdict = AtcVerdict.REVIEW.value
        draft.reason = (
            f"Clause is ambiguous: specifies particular organizations (IITs/NITs) but also "
            f"permits any government organisation. Disclaimer item {draft.matched_void_index}. {draft.reason}"
        )
        return draft

    # 4. Validated violation -> FLAG
    draft.verdict = AtcVerdict.FLAG.value
    return draft
