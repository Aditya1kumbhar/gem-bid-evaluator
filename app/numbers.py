"""Indian currency and count parsing utilities."""

import re
from typing import Optional


def parse_money_to_inr(text: str) -> Optional[float]:
    """Parse monetary expressions in INR including lakh, crore, and Indian grouping."""
    if not text:
        return None
    cleaned = text.lower().replace("₹", "").replace("inr", "").replace("rs.", "").replace("rs", "")
    cleaned = cleaned.replace("/-", "").strip()

    # Case 1: Crore expressions (e.g., "1.2 crore", "5 crores")
    cr_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:crore|crores|cr\.?)\b", cleaned)
    if cr_match:
        return float(cr_match.group(1)) * 10_000_000.0

    # Case 2: Lakh expressions (e.g., "50 lakh", "2.5 lakhs", "10 lac")
    lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs)\b", cleaned)
    if lakh_match:
        return float(lakh_match.group(1)) * 100_000.0

    # Case 3: Standard numbers with Indian comma grouping (e.g., "5,00,000", "75,000")
    num_match = re.search(r"(\d[\d,]*(?:\.\d+)?)", cleaned)
    if num_match:
        digits_only = num_match.group(1).replace(",", "")
        try:
            return float(digits_only)
        except ValueError:
            return None

    return None


def parse_count(text: str) -> Optional[int]:
    """Parse and return the first integer count found in the text."""
    if not text:
        return None
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None
