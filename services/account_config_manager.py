# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# ACCOUNT CONFIGURATION MANAGER
# ============================================================================

# services/account_config_manager.py
"""Utilities for persisting and managing bank account configuration.

This module extends the initial scaffold with CRUD operations, atomic file
writes and optional event notifications so that the UI can react to account
changes.  The configuration is stored as JSON on disk but exposed as a simple
``dict`` structure to callers for compatibility with existing code.
"""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional


@dataclass
class AccountConfig:
    """Dataclass representing a single bank account configuration."""
    account_number: str
    sort_code: str
    transformer: str
    erp_account_code: str
    erp_account_name: str
    statement_format: str = "UK_STANDARD"
    currency: str = "GBP"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
class AccountConfigManager:
    """Manages bank account configurations with persistent storage"""

    def __init__(
        self, 
        config_file_path: str = "config/bank_accounts.json",
        event_bus: Optional[object] = None,
    ) -> None:
        self.config_file_path = Path(config_file_path)
        self.logger = logging.getLogger(__name__)

        self.event_bus = event_bus
        self._lock = RLock()

        # Ensure config directory exists
        self.config_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache of accounts
        self._accounts: Dict[str, Dict[str, Any]] = {}

        # Default configuration used when no file exists or parsing fails
        self.default_accounts: Dict[str, Dict[str, Any]] = {
            "Lloyds Main Account": {
                "account_number": "12345678",
                "sort_code": "12-34-56",
                "transformer": "standard_uk_bank",
                "erp_account_code": "152000",
                "erp_account_name": "LLOYDS Main Account",
                "statement_format": "UK_STANDARD",
                "currency": "GBP"
            }
        }

        # Pre-load accounts into memory
        self.load_accounts()


    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def load_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Load account configurations from disk.

        Returns a copy of the current account dictionary to prevent callers
        from mutating internal state directly.
        """

        with self._lock:
            if self.config_file_path.exists():
                try:
                    with open(self.config_file_path, 'r', encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict) and data:
                        self._accounts = data
                        self.logger.info(
                            "Loaded %d account configurations", len(self._accounts)
                        )
                    else:
                        raise ValueError("Invalid structure in account config file")
                except Exception as exc:  # pylint: disable=broad-except
                    self.logger.error("Failed to load accounts: %s", exc)
                    self._accounts = dict(self.default_accounts)
                    self.save_accounts()
            else:
                self.logger.info(
                    "No account configuration file found, creating default one"
                )
                self._accounts = dict(self.default_accounts)
                self.save_accounts()

            if self.event_bus:
                # Notify listeners that accounts were loaded/refreshed
                self.event_bus.publish("accounts.loaded", self.get_accounts())

            return self.get_accounts()
    
    def save_accounts(self, accounts: Optional[Dict[str, Dict[str, Any]]] = None) -> bool:
        """Persist account configurations to disk atomically.

        If ``accounts`` is provided, the internal cache is replaced before
        saving.  The write is performed via a temporary file which is then
        renamed to the actual path, and the previous file is backed up with a
        ``.bak`` suffix.
        """

        with self._lock:
            if accounts is not None:
                self._accounts = dict(accounts)

            # Validate before writing
            for name, cfg in self._accounts.items():
                if not self.validate_account_config(cfg):
                    self.logger.error("Invalid configuration for account '%s'", name)
                    return False

            tmp_path = self.config_file_path.with_suffix(".tmp")
            backup_path = self.config_file_path.with_suffix(".bak")

            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(self._accounts, f, indent=2)

                if self.config_file_path.exists():
                    self.config_file_path.replace(backup_path)

                tmp_path.replace(self.config_file_path)

                self.logger.info(
                    "Saved %d account configurations", len(self._accounts)
                )

                if self.event_bus:
                    self.event_bus.publish("accounts.updated", self.get_accounts())

                return True
            except Exception as exc:  # pylint: disable=broad-except
                self.logger.error("Failed to save account configurations: %s", exc)
                if tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)
                return False

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def add_account(self, name: str, config: Dict[str, Any]) -> bool:
        """Add a new account configuration."""

        with self._lock:
            if name in self._accounts:
                self.logger.warning("Account '%s' already exists", name)
                return False
            if not self.validate_account_config(config):
                self.logger.error("Invalid configuration for account '%s'", name)
                return False
            self._accounts[name] = dict(config)
            return self.save_accounts()

    def update_account(self, name: str, config: Dict[str, Any]) -> bool:
        """Update an existing account configuration."""

        with self._lock:
            if name not in self._accounts:
                self.logger.warning("Account '%s' does not exist", name)
                return False
            if not self.validate_account_config(config):
                self.logger.error("Invalid configuration for account '%s'", name)
                return False
            self._accounts[name] = dict(config)
            return self.save_accounts()

    def remove_account(self, name: str) -> bool:
        """Remove an account configuration by name."""

        with self._lock:
            if name in self._accounts:
                self._accounts.pop(name)
                return self.save_accounts()
            self.logger.warning("Account '%s' not found", name)
            return False
    
    # ------------------------------------------------------------------
    # Accessors & helpers
    # ------------------------------------------------------------------
    def get_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Return a deep copy of all account configurations."""

        with self._lock:
            # Return a copy to prevent external mutation
            return json.loads(json.dumps(self._accounts))

    def get_account(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single account configuration by name."""

        with self._lock:
            account = self._accounts.get(name)
            return json.loads(json.dumps(account)) if account else None

    def get_transformer_for_account(self, account_name: str) -> str:
        """Get transformer for a specific account."""

        with self._lock:
            return self._accounts.get(account_name, {}).get(
                "transformer", "standard_uk_bank"
            )

    def get_erp_code_for_account(self, account_name: str) -> str:
        """Get ERP account code for a specific account."""

        with self._lock:
            return self._accounts.get(account_name, {}).get("erp_account_code", "")

    def validate_account_config(self, config: Dict[str, Any]) -> bool:
        """Validate account configuration structure"""
        required_fields = {
            "account_number",
            "transformer",
            "erp_account_code",
            "erp_account_name",
            "currency",
        }

        return required_fields.issubset(config)