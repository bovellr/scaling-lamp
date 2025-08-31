# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# viewmodels/matching_viewmodel.py
"""Logic for matching bank and ERP transactions.

The real project now hooks into :class:`models.ml_engine.MLEngine` to propose
matches using heuristic or trained models.  It remains lightweight while
providing an interface for future user feedback and model training.  The view
model exposes Qt signals so the UI can react to long running operations or
display results.
"""

from __future__ import annotations

from typing import List
from datetime import datetime

import pandas as pd
from PySide6.QtCore import Signal

from .base_viewmodel import BaseViewModel
from models.data_models import (
    TransactionData,
    Transaction,
    TransactionMatch,
    MatchStatus,
)
from models.ml_engine import MLEngine


class MatchingViewModel(BaseViewModel):
    """ViewModel responsible for proposing matches between transactions."""

    matching_started = Signal()
    matching_completed = Signal(list)  # List[TransactionMatch]
    matching_failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._bank_transactions: List[TransactionData] = []
        self._erp_transactions: List[TransactionData] = []
        self._matches: List[TransactionMatch] = []
        self._confirmed_matches: List[TransactionMatch] = []
        self._ml_engine = MLEngine()

    # ------------------------------------------------------------------
    # Data management
    # ------------------------------------------------------------------
    def load_transactions(self,
                          bank_transactions: List[TransactionData],
                          erp_transactions: List[TransactionData]) -> None:
        """Load the transactions to be matched."""
        self._bank_transactions = bank_transactions
        self._erp_transactions = erp_transactions
        self._matches = []
        self._confirmed_matches = []
        self.notify_property_changed("matches", self._matches)

    @property
    def matches(self) -> List[TransactionMatch]:
        """Return the list of matches produced by the last run."""
        return self._matches

    # ------------------------------------------------------------------
    # Matching logic
    # ------------------------------------------------------------------
    def run_auto_match(self, confidence_threshold: float = 0.5) -> List[TransactionMatch]:
        """Run the ML-based matcher and return potential matches."""
        try:
            self.matching_started.emit()
            self.is_loading = True

            bank_tx = [self._to_ml_transaction(i, tx) for i, tx in enumerate(self._bank_transactions)]
            erp_tx = [self._to_ml_transaction(i, tx) for i, tx in enumerate(self._erp_transactions)]

            matches = self._ml_engine.generate_matches(
                bank_tx, erp_tx, confidence_threshold=confidence_threshold
            )

            self._matches = matches
            self.notify_property_changed("matches", matches)
            self.matching_completed.emit(matches)
            return matches
        except Exception as exc:  # pragma: no cover - defensive logging
            self.matching_failed.emit(str(exc))
            self.set_error(str(exc))
            return []
        finally:
            self.is_loading = False

    # ------------------------------------------------------------------
    # User feedback & training
    # ------------------------------------------------------------------
    def confirm_match(self, match: TransactionMatch) -> None:
        """Mark a match as confirmed and store for training."""
        match.status = MatchStatus.MATCHED
        if match not in self._confirmed_matches:
            self._confirmed_matches.append(match)

    def reject_match(self, match: TransactionMatch) -> None:
        """Mark a match as rejected and store for training."""
        match.status = MatchStatus.REJECTED
        if match not in self._confirmed_matches:
            self._confirmed_matches.append(match)

    def train_model(self) -> None:
        """Train the ML model with accumulated confirmations."""
        self._ml_engine.train_model(self._confirmed_matches)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _to_ml_transaction(self, idx: int, data: TransactionData) -> Transaction:
        """Convert :class:`TransactionData` to ML :class:`Transaction`."""
        if isinstance(data.date, datetime):
            date_val = data.date
        else:
            # pandas handles various date formats gracefully
            date_val = pd.to_datetime(data.date).to_pydatetime()
        return Transaction(
            id=str(idx),
            date=date_val,
            description=data.description,
            amount=data.amount,
            reference=data.reference,
        )