# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# ACCOUNT SERVICE
# ============================================================================

# services/account_service.py (REFACTORED)
"""
Simplified AccountService that delegates to ConfigurationService.
No more duplicate default accounts!
"""

import logging
from typing import Dict, Any, Optional
from .config_service import ConfigurationService
from config.defaults import DEFAULT_BANK_ACCOUNTS

class AccountService:
    """Simplified service that delegates to configuration service"""
    
    def __init__(self, config_service: ConfigurationService):
        self.logger = logging.getLogger(__name__)
        self.config_service = config_service
    
    def get_all_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Get all bank account configurations"""
        return self.config_service.get_bank_accounts()
    
    def get_account_config(self, account_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific account"""
        accounts = self.config_service.get_bank_accounts()
        return accounts.get(account_name)
    
    def get_statement_transformer(self, account_name: str) -> Optional[str]:
        """Get statement transformer for account"""
        account = self.get_account_config(account_name)
        return account.get('transformer') if account else None
    
    def update_accounts(self, accounts: Dict[str, Dict[str, Any]]) -> bool:
        """Update account configurations"""
        return self.config_service.save_bank_accounts(accounts)

    def reset_to_defaults(self) -> bool:
        """Reset account configurations to default values"""
        default_accounts = {
            name: {
                "account_number": acc.account_number,
                "sort_code": acc.sort_code,
                "transformer": acc.transformer,
                "erp_account_code": acc.erp_account_code,
                "erp_account_name": acc.erp_account_name,
                "statement_format": acc.statement_format,
                "currency": acc.currency,
            }
            for name, acc in DEFAULT_BANK_ACCOUNTS.items()
        }
        return self.config_service.save_bank_accounts(default_accounts)
    
    def reload_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Reload account configurations from storage"""
        return self.config_service.get_bank_accounts()