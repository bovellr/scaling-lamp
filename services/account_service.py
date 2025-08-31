# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# ACCOUNT SERVICE
# ============================================================================

import logging
from typing import Any, Dict, Optional

from .account_config_manager import AccountConfigManager


class AccountService:
    """Service layer for managing bank account configuration."""

    def __init__(self, event_bus: Optional[object] = None) -> None:
        self.logger = logging.getLogger(__name__)
        try:
            self.account_manager = AccountConfigManager(event_bus=event_bus)
            self.bank_accounts_config = self.account_manager.load_accounts()
            self.logger.info("Dynamic account configuration loaded")
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.warning("Using default account configuration: %s", exc)
            self.account_manager = None
            self.bank_accounts_config = self._get_default_accounts()

    def _get_default_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Return default account configurations."""
        return {
            "Main Current Account": {
                "account_number": "12345678",
                "sort_code": "12-34-56",
                "transformer": "standard_uk_bank",
                "erp_account_code": "1001",
                "erp_account_name": "Main Bank Account",
                "statement_format": "UK_STANDARD",
                "currency": "GBP",
            },
            "RBS-Natwest Account": {
                "account_number": "87654321",
                "sort_code": "65-43-21",
                "transformer": "Natwest_bank",
                "erp_account_code": "1002",
                "erp_account_name": "RBS-Natwest Bank Account",
                "statement_format": "UK_BUSINESS",
                "currency": "GBP",
            },
            "Charity Business Account": {
                "account_number": "11223344",
                "sort_code": "11-22-33",
                "transformer": "Charity_bank",
                "erp_account_code": "1003",
                "erp_account_name": "Charity Bank Account",
                "statement_format": "UK_STANDARD",
                "currency": "GBP",
            },
        }

    # ------------------------------------------------------------------
    # Helper accessors
    # ------------------------------------------------------------------
    def get_current_account_config(self, account_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """Return configuration for the specified account name."""
        if account_name is None:
            return None
        return self.bank_accounts_config.get(account_name)

    def get_statement_transformer(self, account_name: Optional[str]) -> Optional[str]:
        """Return statement transformer for the specified account."""
        config = self.get_current_account_config(account_name)
        if config is None:
            return None
        return config.get("transformer")

    def get_erp_account_code(self, account_name: Optional[str]) -> Optional[str]:
        """Return ERP account code for the specified account."""
        config = self.get_current_account_config(account_name)
        if config is None:
            return None
        return config.get("erp_account_code")