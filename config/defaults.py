# config/defaults.py
"""
Single source of truth for all default configurations.
This eliminates duplication across multiple classes.
"""

from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class DefaultBankAccount:
    account_number: str
    sort_code: str
    transformer: str
    erp_account_code: str
    erp_account_name: str
    statement_format: str = "UK_STANDARD"
    currency: str = "GBP"

@dataclass
class DefaultBankTemplate:
    name: str
    bank_type: str
    header_keywords: List[str]
    date_patterns: List[str]
    skip_keywords: List[str]
    column_mapping: Dict[str, List[str]]
    description: str

# SINGLE SOURCE OF TRUTH FOR DEFAULT ACCOUNTS
DEFAULT_BANK_ACCOUNTS: Dict[str, DefaultBankAccount] = {
    "Main Current Account": DefaultBankAccount(
        account_number="01584534",
        sort_code="30-96-96",
        transformer="lloyds",  # Use consistent template names
        erp_account_code="152000",
        erp_account_name="Lloyds Main Account"
    ),
    "RBS-Natwest Account": DefaultBankAccount(
        account_number="87654321", 
        sort_code="65-43-21",
        transformer="rbs/natwest",  # Use consistent template names
        erp_account_code="150600",
        erp_account_name="RBS-Natwest Bank Account",
        statement_format="UK_BUSINESS"
    ),
    "Charity Business Account": DefaultBankAccount(
        account_number="01586871",
        sort_code="30-96-96", 
        transformer="lloyds",  # Use consistent template names
        erp_account_code="153100",
        erp_account_name="Charity Bank Account"
    )
}

# SINGLE SOURCE OF TRUTH FOR DEFAULT TEMPLATES
DEFAULT_BANK_TEMPLATES: Dict[str, DefaultBankTemplate] = {
    "lloyds": DefaultBankTemplate(
        name="Lloyds Bank",
        bank_type="lloyds",
        header_keywords=["posting date", "date", "type", "details", "debits", "credits"],
        date_patterns=[
            r"\d{1,2}[-/]\w{3}[-/]\d{4}",      # 11-Apr-2025
            r"\d{1,2}[-/]\d{1,2}[-/]\d{4}",    # 11/04/2025
        ],
        skip_keywords=["totals", "balance", "end of report", "closing", "opening"],
        column_mapping={
            "date": ["posting date", "date", "transaction date"],
            "type": ["type", "transaction type"],
            "description": ["details", "description", "reference"],
            "debit": ["debit", "debits", "payment", "out"],
            "credit": ["credit", "credits", "receipt", "deposit"]
        },
        description="Standard Lloyds Bank statement format"
    ),
    
    "rbs/natwest": DefaultBankTemplate(
        name="NatWest/RBS Bank", 
        bank_type="rbs/natwest",
        header_keywords=["date", "narrative #1", "narrative #2", "type", "debit", "credit"],
        date_patterns=[
            r"\d{1,2}/\d{1,2}/\d{2,4}",        # 2/28/25, 02/28/2025
            r"\d{1,2}-\d{1,2}-\d{2,4}",        # 2-28-25, 02-28-2025  
            r"\d{4}-\d{1,2}-\d{1,2}"           # 2025-02-28
        ],
        skip_keywords=["Sort Code", "Account Number", "BIC", "Bank Name"],
        column_mapping={
            "date": ["date", "transaction date"],
            "type": ["type", "transaction type"],
            "description": ["narrative #1", "narrative #2", "Narrative #3", "Narrative #4", "Narrative #5"],
            "debit": ["debit", "debits"],
            "credit": ["credit", "credits"]
        },
        description="NatWest and RBS statement format"
    )
}

# LEGACY TRANSFORMER MAPPINGS (for backward compatibility)
LEGACY_TRANSFORMER_MAPPINGS = {
    'standard_uk_bank': 'lloyds',
    'Natwest_bank': 'rbs/natwest', 
    'Charity_bank': 'lloyds',
    'natwest': 'rbs/natwest',
    'rbs': 'rbs/natwest'
}