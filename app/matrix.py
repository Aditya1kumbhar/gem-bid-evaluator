"""Matrix generation and CSV/HTML export for bid evaluation results."""

import html
from typing import List
from app.schemas import Criterion, CriterionResult, Verdict


def build_matrix(criteria: List[Criterion], results: List[CriterionResult]) -> List[List[str]]:
    """Build a criteria-by-bidder verdict matrix."""
    bidder_names: List[str] = []
    for r in results:
        if r.bidder_name and r.bidder_name not in bidder_names:
            bidder_names.append(r.bidder_name)

    # Index results by (criterion_id, bidder_name)
    result_map = {(r.criterion_id, r.bidder_name): r.verdict.value for r in results}

    matrix: List[List[str]] = []
    for crit in criteria:
        row = [crit.title]
        for b_name in bidder_names:
            verdict = result_map.get((crit.id, b_name), Verdict.REVIEW.value)
            row.append(verdict)
        matrix.append(row)
    return matrix


def to_csv(matrix: List[List[str]], bidder_names: List[str]) -> str:
    """Export the verdict matrix to CSV string format."""
    header = ["Criterion"] + bidder_names
    lines = [",".join(f'"{col}"' if "," in col else col for col in header)]
    for row in matrix:
        lines.append(",".join(f'"{col}"' if "," in col else col for col in row))
    return "\n".join(lines) + "\n"


def to_html(matrix: List[List[str]], bidder_names: List[str]) -> str:
    """Export the verdict matrix to standalone HTML table with light status colors."""
    colors = {
        "PASS": "background-color: #d4edda; color: #155724; font-weight: 600;",
        "FAIL": "background-color: #f8d7da; color: #721c24; font-weight: 600;",
        "REVIEW": "background-color: #fff3cd; color: #856404; font-weight: 600;",
    }

    out = ['<table style="border-collapse: collapse; width: 100%; font-family: sans-serif; font-size: 14px;">']
    out.append("<thead><tr style=\"background-color: #f8f9fa;\">")
    out.append('<th style="border: 1px solid #dee2e6; padding: 10px; text-align: left;">Criterion</th>')
    for name in bidder_names:
        out.append(f'<th style="border: 1px solid #dee2e6; padding: 10px; text-align: center;">{html.escape(name)}</th>')
    out.append("</tr></thead><tbody>")

    for row in matrix:
        out.append("<tr>")
        out.append(f'<td style="border: 1px solid #dee2e6; padding: 8px;">{html.escape(row[0])}</td>')
        for verdict in row[1:]:
            style = colors.get(verdict, "border: 1px solid #dee2e6; padding: 8px; text-align: center;")
            out.append(f'<td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; {style}">{html.escape(verdict)}</td>')
        out.append("</tr>")

    out.append("</tbody></table>")
    return "".join(out)
