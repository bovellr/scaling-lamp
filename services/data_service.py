# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# DATA SERVICE
# ============================================================================

"""
Centralized data management service to eliminate duplication and provide single source of truth
"""
from PySide6.QtCore import QObject, Signal
from typing import Optional, List, Dict, Any
import pandas as pd
import logging
from pathlib import Path

from models.data_models import TransactionData, BankStatement, TransactionMatch

logger = logging.getLogger(__name__)

class DataService(QObject):
    """Centralized service for managing all application data"""
    
    # Signals for data state changes
    bank_data_loaded = Signal(object)  # BankStatement
    erp_data_loaded = Signal(list)     # List[TransactionData]
    reconciliation_completed = Signal(list)  # List[TransactionMatch]
    data_cleared = Signal(str)         # data_type: 'bank' | 'erp' | 'all'
    
    def __init__(self):
        super().__init__()
        self._bank_statement: Optional[BankStatement] = None
        self._erp_transactions: List[TransactionData] = []
        self._reconciliation_results: List[TransactionMatch] = []
        self._training_data: List[TransactionMatch] = []
        
    # Properties for external access
    @property
    def bank_statement(self) -> Optional[BankStatement]:
        return self._bank_statement
        
    @property
    def erp_transactions(self) -> List[TransactionData]:
        return self._erp_transactions
        
    @property
    def reconciliation_results(self) -> List[TransactionMatch]:
        return self._reconciliation_results
        
    @property
    def is_ready_for_reconciliation(self) -> bool:
        """Check if both datasets are available for reconciliation"""
        return (self._bank_statement is not None and 
                len(self._bank_statement.transactions) > 0 and
                len(self._erp_transactions) > 0)
    
    # Data loading methods
    def set_bank_data(self, statement: BankStatement) -> None:
        """Set bank statement data and notify all subscribers"""
        self._bank_statement = statement
        self.bank_data_loaded.emit(statement)
        logger.info(f"Bank data loaded: {len(statement.transactions)} transactions")
    
    def set_erp_data(self, transactions: List[TransactionData]) -> None:
        """Set ERP transaction data and notify all subscribers"""
        self._erp_transactions = transactions
        self.erp_data_loaded.emit(transactions)
        logger.info(f"ERP data loaded: {len(transactions)} transactions")
    
    def set_reconciliation_results(self, matches: List[TransactionMatch]) -> None:
        """Set reconciliation results and notify subscribers"""
        self._reconciliation_results = matches
        self.reconciliation_completed.emit(matches)
        logger.info(f"Reconciliation completed: {len(matches)} matches")
    
    # Data analysis methods
    def get_data_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of all loaded data"""
        summary = {
            'bank_loaded': self._bank_statement is not None,
            'bank_count': len(self._bank_statement.transactions) if self._bank_statement else 0,
            'erp_loaded': len(self._erp_transactions) > 0,
            'erp_count': len(self._erp_transactions),
            'reconciliation_count': len(self._reconciliation_results),
            'ready_for_reconciliation': self.is_ready_for_reconciliation
        }
        
        if self._bank_statement:
            bank_df = self._bank_statement.to_dataframe()
            summary.update({
                'bank_date_range': (bank_df['date'].min(), bank_df['date'].max()),
                'bank_total_amount': bank_df['amount'].sum(),
                'bank_currency': getattr(self._bank_statement, 'currency', 'Unknown')
            })
            
        if self._erp_transactions:
            erp_df = pd.DataFrame([{
                'date': t.date,
                'amount': t.amount,
                'description': t.description
            } for t in self._erp_transactions])
            
            summary.update({
                'erp_date_range': (erp_df['date'].min(), erp_df['date'].max()),
                'erp_total_amount': erp_df['amount'].sum()
            })
            
        return summary
    
    def clear_data(self, data_type: str = 'all') -> None:
        """Clear specified data type"""
        if data_type in ['bank', 'all']:
            self._bank_statement = None
        if data_type in ['erp', 'all']:
            self._erp_transactions = []
        if data_type in ['reconciliation', 'all']:
            self._reconciliation_results = []
            
        self.data_cleared.emit(data_type)
        logger.info(f"Data cleared: {data_type}")


