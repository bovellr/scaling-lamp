# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""Transaction tables widget"""

from PySide6.QtWidgets import QGroupBox, QHBoxLayout

from .reconciliation_table import ReconciliationTable


class TransactionTablesWidget(QGroupBox):
    """Widget containing book and bank transaction tables."""

    def __init__(self, parent=None):
        super().__init__("Transaction Data", parent)
        layout = QHBoxLayout(self)

        self.table_book = ReconciliationTable("Book Transactions")
        self.table_bank = ReconciliationTable("Bank Transactions")

        layout.addWidget(self.table_book)
        layout.addWidget(self.table_bank)