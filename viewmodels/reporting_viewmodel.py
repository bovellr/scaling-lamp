# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# viewmodels/reporting_viewmodel.py
"""Generate reports from reconciliation results."""

from __future__ import annotations

from typing import List, Optional
from PySide6.QtCore import Signal

from .base_viewmodel import BaseViewModel
from models.data_models import ReconciliationReport, TransactionData, BankStatement


class ReportingViewModel(BaseViewModel):
    """ViewModel responsible for producing reconciliation reports."""

    report_generated = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._current_report: Optional[ReconciliationReport] = None

    @property
    def current_report(self) -> Optional[ReconciliationReport]:
        return self._current_report

    def generate_report(self,
                        matches: List,
                        bank_statement: Optional[BankStatement] = None,
                        erp_data: Optional[List[TransactionData]] = None) -> ReconciliationReport:
        """Create a :class:`ReconciliationReport` from the provided data."""
        report = ReconciliationReport(
            bank_statement=bank_statement,
            erp_data=erp_data or [],
            matches=matches,
            unmatched_bank=[],
            unmatched_erp=[],
            summary_stats={}
        )
        self._current_report = report
        self.report_generated.emit(report)
        self.notify_property_changed("current_report", report)
        return report