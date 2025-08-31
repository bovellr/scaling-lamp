# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""Reports widget"""

from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox


class ReportsWidget(QGroupBox):
    """Widget providing report generation options."""

    def __init__(self, parent=None):
        super().__init__("Reports & Analysis", parent)
        layout = QVBoxLayout(self)

        button_layout = QHBoxLayout()
        self.btn_reconciliation_report = QPushButton("Reconciliation Report")
        self.btn_exception_report = QPushButton("Exception Report")
        self.btn_audit_trail = QPushButton("Audit Trail")
        self.btn_performance_metrics = QPushButton("AI Performance")
        button_layout.addWidget(self.btn_reconciliation_report)
        button_layout.addWidget(self.btn_exception_report)
        button_layout.addWidget(self.btn_audit_trail)
        button_layout.addWidget(self.btn_performance_metrics)
        layout.addLayout(button_layout)

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Export Format:"))
        self.combo_export_format = QComboBox()
        self.combo_export_format.addItems(["Excel (.xlsx)", "PDF", "CSV", "JSON"])
        format_layout.addWidget(self.combo_export_format)
        format_layout.addStretch()
        layout.addLayout(format_layout)