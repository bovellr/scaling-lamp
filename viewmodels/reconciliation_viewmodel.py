# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# viewmodels/reconciliation_viewmodel.py
"""High level reconciliation workflow.

This view model coordinates the matching process between imported bank
statements and ERP transactions.  It delegates the actual matching to
:class:`MatchingViewModel` and exposes signals that the UI can observe to show
progress or react to completion.
"""

from __future__ import annotations

from typing import List
from PySide6.QtCore import Signal

from .base_viewmodel import BaseViewModel
from .matching_viewmodel import MatchingViewModel
from models.data_models import TransactionData


class ReconciliationViewModel(BaseViewModel):
    """ViewModel orchestrating reconciliation between datasets."""

    reconciliation_started = Signal()
    reconciliation_completed = Signal(list)  # List of matches
    reconciliation_failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.matching_vm = MatchingViewModel()

    def reconcile(self, bank_transactions: List[TransactionData],
                  erp_transactions: List[TransactionData]) -> List:
        """Run the reconciliation process and return matches."""
        try:
            self.reconciliation_started.emit()
            self.matching_vm.load_transactions(bank_transactions, erp_transactions)
            matches = self.matching_vm.run_auto_match()
            self.reconciliation_completed.emit(matches)
            return matches
        except Exception as exc:  # pragma: no cover - defensive logging
            self.reconciliation_failed.emit(str(exc))
            self.set_error(str(exc))
            return []