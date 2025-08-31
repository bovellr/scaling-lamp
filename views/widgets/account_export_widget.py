# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""Account export widget"""

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QComboBox, QPushButton


class AccountExportWidget(QGroupBox):
    """Widget for account selection and report export."""

    def __init__(self, parent=None):
        super().__init__("Account Selection & Export", parent)
        layout = QHBoxLayout(self)

        layout.addWidget(QLabel("Bank Account:"))
        self.combo_account = QComboBox()
        self.combo_account.setPlaceholderText("Select a bank account")
        self.combo_account.addItems([
            "Main Current Account", "Savings Account", "Business Account"
        ])
        layout.addWidget(self.combo_account)

        layout.addStretch()

        self.btn_export = QPushButton("Export Report")
        layout.addWidget(self.btn_export)