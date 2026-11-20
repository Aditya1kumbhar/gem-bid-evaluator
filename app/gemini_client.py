"""Gemini API client for structured extraction and clause classification."""

import logging
import time
from typing import List, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import get_api_key, get_fallback_model, get_model
from app.schemas import (
    AtcClause,
    AtcFlag,
    BidderEvidence,
    Criterion,
    DocumentPresent,
    ExtractedField,
    PageText,
    VoidListItem,
)

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when an extraction call fails after retry and fallback."""
    pass


def get_client() -> genai.Client:
    """Build and return a Google Gen AI client or raise ExtractionError if unconfigured."""
    key = get_api_key()
    if not key:
        raise ExtractionError("AI not configured")
    return genai.Client(
        api_key=key,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1),
            timeout=60000,
        ),
    )


class _VoidListContainer(BaseModel):
    items: List[VoidListItem]


class _CriteriaContainer(BaseModel):
    criteria: List[Criterion]


class _AtcClausesContainer(BaseModel):
    clauses: List[AtcClause]


class _EvidenceContainer(BaseModel):
    documents_present: List[DocumentPresent]
    fields: List[ExtractedField]


class _AtcClassifyOutput(BaseModel):
    matched_void_index: Optional[int] = None
    clause_quote: str = ""
    void_quote: str = ""
    reason: str = ""


def _generate_structured(client: genai.Client, prompt: str, response_schema: type[BaseModel]) -> BaseModel:
    """Generate structured output with 1 retry on primary and 1 fallback attempt."""
    primary = get_model()
    fallback = get_fallback_model()
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema,
        temperature=0.0,
    )
    for model in (primary, primary, fallback):
        try:
            resp = client.models.generate_content(model=model, contents=prompt, config=config)
            return response_schema.model_validate_json(resp.text)
        except Exception as exc:
            logger.warning(f"Generation attempt with {model} failed: {exc}")
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                time.sleep(12)
    raise ExtractionError("Extraction failed after primary retry and fallback.")


def _format_pages(pages: List[PageText]) -> str:
    """Format PDF page texts with explicit page markers."""
    return "\n\n".join(f"[PAGE {p.page}]\n{p.text}" for p in pages)


def extract_void_list(pages: List[PageText], doc_name: str) -> List[VoidListItem]:
    """Extract null-and-void disclaimer categories from document text using double extraction."""
    client = get_client()
    doc_text = _format_pages(pages)
    prompt = (
        f"Analyze tender document '{doc_name}'. Find the Disclaimer section listing clause "
        "types that make the bid null and void. Return every numbered item 1 to 14 exactly as written.\n"
        "For each item, cite 1-based source_page and character-for-character source_quote.\n"
        f"Document text:\n{doc_text}"
    )
    r1 = _generate_structured(client, prompt, _VoidListContainer)
    r2 = _generate_structured(client, prompt, _VoidListContainer)
    assert isinstance(r1, _VoidListContainer) and isinstance(r2, _VoidListContainer)
    return r1.items if len(r1.items) >= len(r2.items) else r2.items


def extract_criteria(pages: List[PageText], doc_name: str) -> List[Criterion]:
    """Extract explicit eligibility/qualification criteria from tender with double extraction."""
    client = get_client()
    doc_text = _format_pages(pages)
    prompt = (
        f"Analyze tender document '{doc_name}'. Extract explicit qualification criteria.\n"
        "Map each to rule_type (MIN_COUNT, MIN_AVG_VALUE, DOC_PRESENT, UNDERTAKING_PRESENT, OEM_OR_AUTHORISED, MANUAL).\n"
        "Use stable id slugs: 'exp_orders' for past orders count (threshold=2, unit='orders'), "
        "'oem_authorisation', 'liquidation_undertaking'. Fill accepted_doc_types if specified.\n"
        "Cite 1-based source_page and exact character-for-character source_quote.\n"
        f"Document text:\n{doc_text}"
    )
    r1 = _generate_structured(client, prompt, _CriteriaContainer)
    r2 = _generate_structured(client, prompt, _CriteriaContainer)
    assert isinstance(r1, _CriteriaContainer) and isinstance(r2, _CriteriaContainer)
    # Check agreement on threshold and rule_type across runs
    map2 = {c.id: c for c in r2.criteria}
    merged: List[Criterion] = []
    for c in r1.criteria:
        crit = c.model_copy()
        crit.source_doc = doc_name
        if c.id in map2 and (map2[c.id].threshold != c.threshold or map2[c.id].rule_type != c.rule_type):
            crit.rule_type = "MANUAL"  # Disputed criteria revert to officer judgement
        merged.append(crit)
    return merged


def extract_atc_clauses(pages: List[PageText], doc_name: str) -> List[AtcClause]:
    """Extract buyer-added bid-specific ATC clauses from tender document."""
    client = get_client()
    doc_text = _format_pages(pages)
    prompt = (
        f"Extract all buyer-added bid-specific ATC clauses from '{doc_name}'.\n"
        "Include both numbered ATC conditions and text-based ATC blocks.\n"
        "For each clause, provide text, 1-based source_page, and set source_doc.\n"
        f"Document text:\n{doc_text}"
    )
    res = _generate_structured(client, prompt, _AtcClausesContainer)
    assert isinstance(res, _AtcClausesContainer)
    for cl in res.clauses:
        cl.source_doc = doc_name
    return res.clauses


def extract_bidder_evidence(
    pages: List[PageText], bidder_name: str, criteria: List[Criterion]
) -> BidderEvidence:
    """Extract evidence fields and present documents from a bidder submission pack."""
    client = get_client()
    doc_text = _format_pages(pages)
    crit_desc = "\n".join(f"- {c.id} ({c.title}): rule={c.rule_type}, threshold={c.threshold}" for c in criteria)
    prompt = (
        f"Extract evidence for bidder '{bidder_name}' against these criteria:\n{crit_desc}\n\n"
        "Find supporting value, 1-based page, and character-for-character quote for each criterion.\n"
        "Also list all documents_present with recognized doc_type vocabulary.\n"
        f"Document text:\n{doc_text}"
    )
    r1 = _generate_structured(client, prompt, _EvidenceContainer)
    r2 = _generate_structured(client, prompt, _EvidenceContainer)
    assert isinstance(r1, _EvidenceContainer) and isinstance(r2, _EvidenceContainer)

    # Cross-check field values for disputes
    r2_field_map = {(f.criterion_id, f.page): f.value for f in r2.fields}
    for field in r1.fields:
        other_val = r2_field_map.get((field.criterion_id, field.page))
        if other_val is not None and other_val != field.value:
            field.disputed = True
    return BidderEvidence(bidder_name=bidder_name, documents_present=r1.documents_present, fields=r1.fields)


def classify_atc_clause(
    clause: AtcClause,
    void_list: List[VoidListItem],
    hints: Optional[List[str]] = None,
) -> AtcFlag:
    """Classify an ATC clause against the null-and-void list and return a draft AtcFlag."""
    client = get_client()
    void_summary = "\n".join(f"{v.index}. {v.text}" for v in void_list)
    hint_block = f"\nCandidate hints (for reference only, verify independently):\n" + "\n".join(hints) if hints else ""
    prompt = (
        f"Classify this buyer ATC clause against the GeM null-and-void Disclaimer categories:\n"
        f"ATC Clause: {clause.text}\n\n"
        f"Disclaimer categories:\n{void_summary}\n"
        f"{hint_block}\n"
        "Return matched_void_index (1-14 integer if a Disclaimer item matches, else null).\n"
        "clause_quote: exact character-for-character substring from the ATC Clause.\n"
        "void_quote: exact character-for-character substring from the matched Disclaimer item text.\n"
        "reason: concise explanation."
    )
    r1 = _generate_structured(client, prompt, _AtcClassifyOutput)
    r2 = _generate_structured(client, prompt, _AtcClassifyOutput)
    assert isinstance(r1, _AtcClassifyOutput) and isinstance(r2, _AtcClassifyOutput)
    
    # If the two runs disagree on matched_void_index, mark as disputed
    matched_idx = r1.matched_void_index
    reason = r1.reason
    if r1.matched_void_index != r2.matched_void_index:
        reason = f"Disputed classification: run 1 matched {r1.matched_void_index}, run 2 matched {r2.matched_void_index}. {reason}"

    return AtcFlag(
        clause_text=clause.text,
        clause_quote=r1.clause_quote or "",
        matched_void_index=matched_idx,
        reason=reason,
        verdict="REVIEW" if matched_idx else "CLEAR",
        void_quote=r1.void_quote or "",
    )
