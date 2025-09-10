# SPDX-License-Identifier: LicenseRef-Proprietary
# Utility functions for ML feature computation

from __future__ import annotations

from typing import Dict
from datetime import datetime
try:  # Optional dependency
    from rapidfuzz.fuzz import token_sort_ratio  # type: ignore
except Exception:  # pragma: no cover - optional
    from difflib import SequenceMatcher

    def token_sort_ratio(a: str, b: str) -> int:
        """Fallback similarity using difflib if rapidfuzz not available."""
        a_sorted = " ".join(sorted(a.split()))
        b_sorted = " ".join(sorted(b.split()))
        return int(SequenceMatcher(None, a_sorted, b_sorted).ratio() * 100)


def compute_transaction_features(
    bank_amount: float,
    bank_date,
    bank_description: str,
    erp_amount: float,
    erp_date,
    erp_description: str,
) -> Dict[str, float]:
    """Compute basic comparison features between two transactions.

    Returns a dictionary containing:
        - amount_diff: absolute difference between amounts
        - date_diff: absolute difference in days between dates
        - description_similarity: fuzzy similarity score (0-100)
        - signed_amount_match: 1 if both amounts have same sign else 0
        - same_day: 1 if dates are the same calendar day else 0
    """
    def _to_datetime(value):
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    bank_date = _to_datetime(bank_date)
    erp_date = _to_datetime(erp_date)

    amount_diff = abs(abs(float(bank_amount)) - abs(float(erp_amount)))
    date_diff = abs((bank_date - erp_date).days)
    desc_sim = token_sort_ratio(str(bank_description), str(erp_description))
    
    # add tolerance for minor sign differences due to rounding
    amount_threshold = 0.01
    if abs(float(bank_amount)) < amount_threshold or abs(float(erp_amount)) < amount_threshold:
        # Near-zero amounts get sign match benefit
        signed_match = 1
    else:
        # Normal sign comparison (should now be consistent)
        signed_match = int((float(bank_amount) > 0) == (float(erp_amount) > 0))
    
    same_day = int(bank_date.date() == erp_date.date())

    return {
        "amount_diff": amount_diff,
        "date_diff": date_diff,
        "description_similarity": desc_sim,
        "signed_amount_match": signed_match,
        "same_day": same_day,
    }