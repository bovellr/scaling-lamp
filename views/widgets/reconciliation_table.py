# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
"""Reconciliation table widget"""

from PySide6.QtWidgets import QTableWidget


class ReconciliationTable(QTableWidget):
    """
    A reusable QTableWidget configured for bank reconciliation transactions.
    Supports 5 standard columns: Date, Description, Amount, Status, Confidence.
    """

    def __init__(self, table_name: str = "table"):
        super().__init__()
        self.setObjectName(table_name)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Date", "Description", "Amount", "Status", "Confidence"])
        self._configure_style()

    def _configure_style(self):
        """
        Optional: Customize the appearance and behavior of the table.
        """
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #ccc;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                border: 1px solid #ddd;
            }
        """)
        self.setMinimumHeight(250)
        self.setSortingEnabled(True)

