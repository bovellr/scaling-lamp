# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# DATA TRANSFORMATION SERVICE
# ============================================================================

"""
Centralized data transformation service to eliminate duplication and ensure consistency.
This service handles all data conversions between different transaction formats.
"""

from typing import List, Dict, Any, Optional, Union
import pandas as pd
from datetime import datetime
import logging
from dataclasses import dataclass

from models.data_models import (
    TransactionData, BankTransaction, ERPTransaction, 
    BankStatement, TransactionMatch
)

logger = logging.getLogger(__name__)

@dataclass
class TransformationResult:
    """Result of data transformation operation"""
    success: bool
    data: Any
    errors: List[str]
    metadata: Dict[str, Any]

class DataTransformationService:
    """Centralized service for all data transformations"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}
        self._cache_timeout = 300  # 5 minutes
    
    def clear_cache(self):
        """Clear all cached transformations"""
        self._cache.clear()
        self._cache_ttl.clear()
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if still valid"""
        import time
        if key in self._cache and key in self._cache_ttl:
            if time.time() - self._cache_ttl[key] < self._cache_timeout:
                return self._cache[key]
            else:
                # Remove expired cache
                del self._cache[key]
                del self._cache_ttl[key]
        return None
    
    def _set_cached(self, key: str, value: Any):
        """Cache data with timestamp"""
        import time
        self._cache[key] = value
        self._cache_ttl[key] = time.time()
    
    def bank_statement_to_transaction_data(
        self, 
        statement: BankStatement
    ) -> TransformationResult:
        """Convert BankStatement to List[TransactionData]"""
        cache_key = f"bank_to_tx_data_{id(statement)}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            transactions = []
            errors = []
            
            for idx, tx in enumerate(statement.transactions):
                try:
                    # Handle potential None or invalid values
                    date_val = str(tx.date) if tx.date else ""
                    description_val = str(tx.description) if tx.description else "Transaction"
                    amount_val = float(tx.amount) if tx.amount is not None else 0.0
                    
                    # Skip transactions with invalid data
                    if not date_val or date_val.lower() in ['nan', 'none', '']:
                        errors.append(f"Transaction {idx}: Invalid date")
                        continue
                    
                    if not description_val or description_val.lower() in ['nan', 'none', '']:
                        errors.append(f"Transaction {idx}: Invalid description")
                        continue
                    
                    tx_data = TransactionData(
                        date=date_val,
                        description=description_val,
                        amount=amount_val,
                        reference=getattr(tx, 'reference', None),
                        original_row_index=idx,
                        transaction_id=getattr(tx, 'id', f"bank_{idx}"),
                        category=getattr(tx, 'category', None),
                        description_date=getattr(tx, 'description_date', None),
                        normalized_description=getattr(tx, 'normalized_description', None)
                    )
                    transactions.append(tx_data)
                except Exception as e:
                    errors.append(f"Transaction {idx}: {str(e)}")
                    logger.warning(f"Failed to convert bank transaction {idx}: {e}")
            
            result = TransformationResult(
                success=len(errors) == 0,
                data=transactions,
                errors=errors,
                metadata={
                    'total_transactions': len(statement.transactions),
                    'converted_transactions': len(transactions),
                    'failed_transactions': len(errors)
                }
            )
            
            self._set_cached(cache_key, result)
            return result
            
        except Exception as e:
            error_msg = f"Failed to convert bank statement: {str(e)}"
            logger.error(error_msg)
            return TransformationResult(
                success=False,
                data=[],
                errors=[error_msg],
                metadata={'error': str(e)}
            )
    
    def transaction_data_to_bank_transactions(
        self, 
        transactions: List[TransactionData]
    ) -> TransformationResult:
        """Convert List[TransactionData] to List[BankTransaction]"""
        cache_key = f"tx_data_to_bank_{hash(tuple(t.id for t in transactions))}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            bank_transactions = []
            errors = []
            
            for tx in transactions:
                try:
                    # Convert date
                    if isinstance(tx.date, str):
                        date_val = pd.to_datetime(tx.date).to_pydatetime()
                    else:
                        date_val = tx.date
                    
                    bank_tx = BankTransaction(
                        id=tx.transaction_id or f"bank_{len(bank_transactions)}",
                        date=date_val,
                        amount=float(tx.amount),
                        description=tx.description,
                        reference=tx.reference,
                        balance=getattr(tx, 'balance', None),
                        check_number=getattr(tx, 'check_number', None),
                        category=tx.category,
                        description_date=tx.description_date,
                        normalized_description=tx.normalized_description
                    )
                    bank_transactions.append(bank_tx)
                except Exception as e:
                    errors.append(f"Transaction {tx.transaction_id}: {str(e)}")
                    logger.warning(f"Failed to convert transaction {tx.transaction_id}: {e}")
            
            result = TransformationResult(
                success=len(errors) == 0,
                data=bank_transactions,
                errors=errors,
                metadata={
                    'total_transactions': len(transactions),
                    'converted_transactions': len(bank_transactions),
                    'failed_transactions': len(errors)
                }
            )
            
            self._set_cached(cache_key, result)
            return result
            
        except Exception as e:
            error_msg = f"Failed to convert to bank transactions: {str(e)}"
            logger.error(error_msg)
            return TransformationResult(
                success=False,
                data=[],
                errors=[error_msg],
                metadata={'error': str(e)}
            )
    
    def transaction_data_to_erp_transactions(
        self, 
        transactions: List[TransactionData]
    ) -> TransformationResult:
        """Convert List[TransactionData] to List[ERPTransaction]"""
        cache_key = f"tx_data_to_erp_{hash(tuple(t.id for t in transactions))}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            erp_transactions = []
            errors = []
            
            for tx in transactions:
                try:
                    # Convert date
                    if isinstance(tx.date, str):
                        date_val = pd.to_datetime(tx.date).to_pydatetime()
                    else:
                        date_val = tx.date
                    
                    erp_tx = ERPTransaction(
                        id=tx.transaction_id or f"erp_{len(erp_transactions)}",
                        date=date_val,
                        amount=float(tx.amount),
                        description=tx.description,
                        reference=tx.reference,
                        invoice_number=getattr(tx, 'invoice_number', None),
                        vendor_id=getattr(tx, 'vendor_id', None),
                        cheque_number=getattr(tx, 'cheque_number', None),
                        description_date=tx.description_date,
                        normalized_description=tx.normalized_description
                    )
                    erp_transactions.append(erp_tx)
                except Exception as e:
                    errors.append(f"Transaction {tx.transaction_id}: {str(e)}")
                    logger.warning(f"Failed to convert transaction {tx.transaction_id}: {e}")
            
            result = TransformationResult(
                success=len(errors) == 0,
                data=erp_transactions,
                errors=errors,
                metadata={
                    'total_transactions': len(transactions),
                    'converted_transactions': len(erp_transactions),
                    'failed_transactions': len(errors)
                }
            )
            
            self._set_cached(cache_key, result)
            return result
            
        except Exception as e:
            error_msg = f"Failed to convert to ERP transactions: {str(e)}"
            logger.error(error_msg)
            return TransformationResult(
                success=False,
                data=[],
                errors=[error_msg],
                metadata={'error': str(e)}
            )
    
    def dataframe_to_transaction_data(
        self, 
        df: pd.DataFrame, 
        column_mapping: Dict[str, str],
        source_type: str = "unknown"
    ) -> TransformationResult:
        """Convert pandas DataFrame to List[TransactionData]"""
        cache_key = f"df_to_tx_data_{hash(df.to_string())}_{source_type}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            transactions = []
            errors = []
            
            # Validate required columns
            required_columns = ['date', 'description', 'amount']
            missing_columns = [col for col in required_columns if col not in column_mapping]
            if missing_columns:
                return TransformationResult(
                    success=False,
                    data=[],
                    errors=[f"Missing required column mappings: {missing_columns}"],
                    metadata={'error': 'Missing column mappings'}
                )
            
            for idx, row in df.iterrows():
                try:
                    # Extract data using column mapping
                    date_val = row[column_mapping['date']]
                    description = str(row[column_mapping['description']]).strip()
                    amount = float(row[column_mapping['amount']])
                    
                    # Convert date
                    if isinstance(date_val, str):
                        date_val = pd.to_datetime(date_val).to_pydatetime()
                    elif not isinstance(date_val, datetime):
                        date_val = pd.to_datetime(date_val).to_pydatetime()
                    
                    tx_data = TransactionData(
                        date=str(date_val),
                        description=description,
                        amount=amount,
                        reference=str(row.get(column_mapping.get('reference', ''), '')),
                        original_row_index=idx,
                        transaction_id=f"{source_type}_{idx}",
                        category=str(row.get(column_mapping.get('category', ''), '')),
                        description_date=str(row.get(column_mapping.get('description_date', ''), '')),
                        normalized_description=getattr(row, 'normalized_description', None)
                    )
                    transactions.append(tx_data)
                except Exception as e:
                    errors.append(f"Row {idx}: {str(e)}")
                    logger.warning(f"Failed to convert row {idx}: {e}")
            
            result = TransformationResult(
                success=len(errors) == 0,
                data=transactions,
                errors=errors,
                metadata={
                    'total_rows': len(df),
                    'converted_transactions': len(transactions),
                    'failed_transactions': len(errors),
                    'source_type': source_type
                }
            )
            
            self._set_cached(cache_key, result)
            return result
            
        except Exception as e:
            error_msg = f"Failed to convert DataFrame to transactions: {str(e)}"
            logger.error(error_msg)
            return TransformationResult(
                success=False,
                data=[],
                errors=[error_msg],
                metadata={'error': str(e)}
            )
    
    def optimize_transaction_list(
        self, 
        transactions: List[TransactionData]
    ) -> TransformationResult:
        """Optimize transaction list by removing duplicates and invalid entries"""
        try:
            # Remove duplicates based on transaction_id
            seen_ids = set()
            unique_transactions = []
            duplicates_removed = 0
            
            for tx in transactions:
                if tx.transaction_id and tx.transaction_id in seen_ids:
                    duplicates_removed += 1
                    continue
                if tx.transaction_id:
                    seen_ids.add(tx.transaction_id)
                unique_transactions.append(tx)
            
            # Remove invalid transactions
            valid_transactions = []
            invalid_removed = 0
            
            for tx in unique_transactions:
                if (tx.amount == 0 or 
                    not tx.description or 
                    not tx.description.strip() or
                    not tx.date):
                    invalid_removed += 1
                    continue
                valid_transactions.append(tx)
            
            logger.info(f"Transaction optimization: {len(transactions)} -> {len(valid_transactions)} "
                       f"(removed {duplicates_removed} duplicates, {invalid_removed} invalid)")
            
            return TransformationResult(
                success=True,
                data=valid_transactions,
                errors=[],
                metadata={
                    'original_count': len(transactions),
                    'final_count': len(valid_transactions),
                    'duplicates_removed': duplicates_removed,
                    'invalid_removed': invalid_removed
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to optimize transaction list: {str(e)}"
            logger.error(error_msg)
            return TransformationResult(
                success=False,
                data=transactions,  # Return original on error
                errors=[error_msg],
                metadata={'error': str(e)}
            )
