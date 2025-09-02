# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""Account export widget"""

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QComboBox, QPushButton
from services.app_container import get_account_service

class AccountExportWidget(QGroupBox):
    """Widget for account selection and report export."""

    def __init__(self, parent=None):
        super().__init__("Account Selection & Export", parent)
        
        # Get account service from container
        self.account_service = get_account_service()
        
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Bank Account:"))
        
        self.combo_account = QComboBox()
        self.combo_account.setPlaceholderText("Select a bank account")
        
        # Populate from configuration service (no hardcoded accounts!)
        self._populate_accounts()
        
        layout.addWidget(self.combo_account)
        layout.addStretch()

        self.btn_export = QPushButton("Export Report")
        layout.addWidget(self.btn_export)
    
    def _populate_accounts(self):
        """Populate accounts from configuration service"""
        accounts = self.account_service.get_all_accounts()
        for account_name in accounts.keys():
            self.combo_account.addItem(account_name)
    
    def refresh_accounts(self):
        """Refresh account list"""
        self.combo_account.clear()
        self._populate_accounts()