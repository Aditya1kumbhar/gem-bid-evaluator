"""Criteria and void list resolution across base tender and corrigenda."""

from typing import List
from app.schemas import Criterion, VoidListItem


def resolve_criteria(docs_in_order: List[List[Criterion]]) -> List[Criterion]:
    """Merge criteria in document order; later documents override earlier ones on same id."""
    resolved: dict[str, Criterion] = {}
    for doc_criteria in docs_in_order:
        for crit in doc_criteria:
            if crit.id in resolved:
                older = resolved[crit.id]
                crit_copy = crit.model_copy(deep=True)
                accumulated = list(older.supersedes)
                if older.id not in accumulated:
                    accumulated.append(older.id)
                crit_copy.supersedes = accumulated
                resolved[crit.id] = crit_copy
            else:
                resolved[crit.id] = crit.model_copy(deep=True)
    return list(resolved.values())


def resolve_void_list(lists_in_order: List[List[VoidListItem]]) -> List[VoidListItem]:
    """Return the void list from the last document that produced a non-empty list."""
    for void_list in reversed(lists_in_order):
        if void_list:
            return void_list
    return []
