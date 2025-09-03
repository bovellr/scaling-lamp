# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# models/__init__.py
"""Models package for Bank Reconciliation AI"""

from .data_models import (
    Transaction, BankTransaction, ERPTransaction, 
    TransactionMatch, ReconciliationReport
)

try:  # Optional MLEngine import
    from .ml_engine import MLEngine  # type: ignore
except Exception:  # pragma: no cover - optional
    MLEngine = None  # type: ignore

__all__ = [
    'Transaction', 'BankTransaction', 'ERPTransaction',
    'TransactionMatch', 'ReconciliationReport', 'MLEngine'
]
