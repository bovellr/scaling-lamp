# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
# ============================================================================
# MODELS - Business Logic & Data (M in MVVM)
# ============================================================================

# models/data_models.py
"""
Data models and entities for bank reconciliation system.
Incorporates your existing bank transformation functionality.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import re
import logging
from pathlib import Path
import uuid

try:  # Optional dependency
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover - optional
    pd = None

# Configure logging
logger = logging.getLogger(__name__)

class TransactionType(Enum):
    """Transaction type enumeration"""
    DEBIT = "debit"
    CREDIT = "credit"

class BankType(Enum):
    """Supported bank statement formats."""
    LLOYDS = "lloyds"
    NATWEST = "rbs/natwest"
    HSBC = "hsbc"
    BARCLAYS = "barclays"
    CUSTOM = "custom"

@dataclass
class TransactionData:
    """Individual transaction data."""
    date: str
    description: str
    amount: float
    reference: Optional[str] = None
    original_row_index: int = 0
    
    def __post_init__(self):
        """Validate transaction data after initialization"""
        self._validate()
    
    def _validate(self):
        """Validate that the transaction data is valid"""
        # Check date
        if not self.date or str(self.date).lower() in ['nan', 'none', '']:
            raise ValueError("Invalid date: date cannot be empty or NaN")
        
        # Check description
        if not self.description or str(self.description).lower() in ['nan', 'none', '']:
            raise ValueError("Invalid description: description cannot be empty or NaN")
        
        # Check amount
        if self.amount is None or str(self.amount).lower() in ['nan', 'none', '']:
            raise ValueError("Invalid amount: amount cannot be NaN or None")
        
        try:
            float(self.amount)
        except (ValueError, TypeError):
            raise ValueError("Invalid amount: amount must be a valid number")
        
        if float(self.amount) == 0:
            raise ValueError("Invalid amount: amount cannot be zero")
    
    category: Optional[str] = None
    description_date: Optional[str] = None
    normalized_description: Optional[str] = None
    transaction_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class BankStatement:
    """Bank statement containing multiple transactions."""
    bank_name: str
    account_number: Optional[str]
    statement_date: str
    transactions: List[TransactionData]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dataframe(self):
        """Convert to pandas DataFrame for processing."""
        if pd is None:
            raise ImportError("pandas is required for to_dataframe")
        return pd.DataFrame([t.to_dict() for t in self.transactions])

    @property
    def transform(self) -> bool:
        """Whether statement has been transformed (has transactions)."""
        return len(self.transactions) > 0

@dataclass
class BankTemplate:
    """Template defining bank-specific parsing rules."""
    name: str
    bank_type: str
    header_keywords: List[str]
    date_patterns: List[str]
    skip_keywords: List[str]
    column_mapping: Dict[str, List[str]]
    skip_rows: int = 0
    description: str = ""
    created_by: str = "system"
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True
    debit_positive: bool = True
    
    def matches_date_pattern(self, text: str) -> bool:
        """Check if text matches any of the bank's date patterns."""
        if not text or len(text) < 6:
            return False
        
        for pattern_str in self.date_patterns:
            try:
                pattern = re.compile(pattern_str)
                if pattern.match(text.strip()):
                    return True
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern_str}")
                continue
        return False
    
    def _normalize(self, s: str) -> str:
        """Lowercase and strip all non-alphanumeric characters."""
        return re.sub(r'[^a-z0-9]', '', s.lower())

    def map_columns(self, headers: List[str]) -> Dict[str, List[int]]:
        """Map semantic column names to actual header positions."""
        column_map: Dict[str, List[int]] = {}
        header_to_indices: Dict[str, List[int]] = {}

        # Normalize headers and build a lookup from normalized header -> indices
        headers_normalized = [ self._normalize(h) for h in headers]
        
        for i, h_norm in enumerate(headers_normalized):
            header_to_indices.setdefault(h_norm, []).append(i)


        for semantic_name, possible_names in self.column_mapping.items():
            indices_for_semantic: List[int] = []
            for name in possible_names:
                n_name = self._normalize(name)
                if n_name in header_to_indices:
                    # extend with all indices that exactly match this normalized name
                    indices_for_semantic.extend(header_to_indices[n_name])

            # Deduplicate while preserving order
            if indices_for_semantic:
                seen = set()
                deduped = [idx for idx in indices_for_semantic if not (idx in seen or seen.add(idx))]
                column_map[semantic_name] = deduped
        
        return column_map

class MatchStatus(Enum):
    """Status of transaction matching process."""
    MATCHED = "matched"
    REJECTED = "rejected"
    MANUAL = "manual"
    PENDING = "pending"

@dataclass(kw_only=True)
class Transaction:
    """Base transaction with shared fields."""
    date: datetime
    amount: float
    description: str
    reference: Optional[str] = None
        
    def __post_init__(self):
        """Validate transaction data after initialization"""
        if self.amount == 0:
            raise ValueError("Transaction amount cannot be zero")
        
        if not self.description or not self.description.strip():
            raise ValueError("Transaction description cannot be empty")

@dataclass(kw_only=True)
class BankTransaction(Transaction):
    """Bank transaction with additional banking-specific fields"""
    id: str
    balance: Optional[float] = None
    check_number: Optional[str] = None
    category: Optional[str] = None
    description_date: Optional[str] = None
    normalized_description: Optional[str] = None

@dataclass(kw_only=True)
class ERPTransaction(Transaction):
    """ERP transaction with additional ERP-specific fields"""
    id: str
    invoice_number: Optional[str] = None
    vendor_id: Optional[str] = None
    cheque_number: Optional[str] = None
    description_date: Optional[str] = None
    normalized_description: Optional[str] = None


@dataclass
class TransactionMatch:
    """Potential match between bank and ERP transactions."""
    bank_transaction: BankTransaction
    erp_transaction: ERPTransaction
    confidence_score: float
    amount_score: float
    date_score: float
    description_score: float
    match_note: Optional[str] = None
    match_reasons: List[str] = field(default_factory=list)
    is_confirmed: bool = False
    reviewed_by: Optional[str] = None
    review_date: Optional[datetime] = None
    status: MatchStatus = MatchStatus.PENDING    

    def __post_init__(self):
        """Validate match data"""
        if not (0 <= self.confidence_score <= 1):
            raise ValueError("Confidence score must be between 0 and 1")

@dataclass
class MatchResult:
    """Result of transaction matching process."""
    bank_transaction: TransactionData
    erp_transaction: Optional[TransactionData]
    confidence_score: float
    match_type: str  # 'exact', 'fuzzy', 'manual', 'none'
    amount_difference: float = 0.0
    date_difference: int = 0
    description_similarity: float = 0.0
    
@dataclass
class ReconciliationResults:
    """Complete reconciliation report."""
    bank_statement: BankStatement
    erp_data: List[TransactionData]
    matches: List[MatchResult]
    unmatched_bank: List[TransactionData]
    unmatched_erp: List[TransactionData]
    summary_stats: Dict[str, Any]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ReconciliationReport:
    """Reconciliation results summary"""
    total_bank_transactions: int
    total_erp_transactions: int
    matched_count: int
    unmatched_bank_count: int
    unmatched_erp_count: int
    confidence_threshold: float
    processing_time: float
    matches: List[TransactionMatch] = field(default_factory=list)
    unmatched_bank: List[BankTransaction] = field(default_factory=list)
    unmatched_erp: List[ERPTransaction] = field(default_factory=list)
    
    @property
    def match_rate(self) -> float:
        """Calculate the matching rate"""
        total = self.total_bank_transactions + self.total_erp_transactions
        return (self.matched_count * 2) / total if total > 0 else 0.0