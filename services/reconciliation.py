from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import List
import re


@dataclass
class TransactionRecord:
    """Minimal transaction representation used for reconciliation."""
    date: str
    description: str
    amount: float


@dataclass
class ReconciledMatch:
    """Simple container for a reconciled transaction pair."""
    bank_transaction: TransactionRecord
    gl_transaction: TransactionRecord
    confidence: float


_DATE_PATTERNS = [
    "%d/%m/%Y",
    "%d/%m/%y",
    "%d-%m-%Y",
    "%d-%m-%y",
]


def _normalize_description(text: str) -> str:
    """Normalize description for comparison.

    Numbers are stripped to avoid mismatches when a GL description embeds a
    date that should not affect similarity checks.
    """
    return re.sub(r"[^a-z]+", " ", text.lower()).strip()


def _extract_description_date(text: str) -> date | None:
    """Extract a date embedded in the description if present."""
    match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text)
    if not match:
        return None
    token = match.group(1)
    for fmt in _DATE_PATTERNS:
        try:
            return datetime.strptime(token, fmt).date()
        except ValueError:
            continue
    return None


def reconcile_transactions(
    bank_transactions: List[TransactionRecord],
    gl_transactions: List[TransactionRecord],
    score_threshold: float = 0.8,
) -> List[ReconciledMatch]:
    """Reconcile bank and GL transactions using heuristic matching.

    When the GL posting date differs from the bank date, a date embedded in the
    GL description (``description_date``) is compared with the bank date. If the
    ``description_date`` matches the bank transaction date within ±1 day, the
    match score receives a boost to reflect the likely connection between the
    records. Amounts and normalized descriptions are still compared to finalise
    the match decision.
    """

    matches: List[ReconciledMatch] = []
    for bank_tx in bank_transactions:
        best_gl: TransactionRecord | None = None
        best_score = 0.0
        bank_date = datetime.fromisoformat(str(bank_tx.date)).date()
        for gl_tx in gl_transactions:
            gl_date = datetime.fromisoformat(str(gl_tx.date)).date()

            # Base similarity metrics
            amount_score = 1.0 if abs(bank_tx.amount - gl_tx.amount) < 0.01 else 0.0
            desc_score = (
                1.0
                if _normalize_description(bank_tx.description)
                == _normalize_description(gl_tx.description)
                else 0.0
            )
            date_score = 1.0 if bank_date == gl_date else 0.0

            score = amount_score * 0.4 + desc_score * 0.3 + date_score * 0.3

            # If posting dates differ, check for a description date
            if date_score == 0.0:
                desc_date = _extract_description_date(gl_tx.description)
                if desc_date and abs((desc_date - bank_date).days) <= 1:
                    score += 0.2  # boost for description date proximity

            score = min(score, 1.0)
            if score > best_score:
                best_score = score
                best_gl = gl_tx

        if best_gl and best_score >= score_threshold:
            matches.append(ReconciledMatch(bank_tx, best_gl, best_score))

    return matches