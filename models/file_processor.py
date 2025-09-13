# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# FILE PROCESSOR
# ============================================================================

# models/file_processor.py
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import logging
import re
from datetime import datetime

from .base_file_processor import BaseFileProcessor
from .data_models import BankTemplate, BankStatement, TransactionData


logger = logging.getLogger(__name__)

DATE_REGEX = re.compile(r"\b(\d{1,2}[.\/]\d{1,2}(?:[.\/]\d{2,4})?)\b")


class FileProcessor(BaseFileProcessor):
    """Handles file I/O and bank statement parsing.
    Parameters
    ----------
    templates_manager:
        Object providing access to bank templates.
    debit_positive:
        When ``True`` (default), debit amounts remain positive and credit
        amounts become negative. When ``False`` the opposite convention is
        applied. This allows adapting to differing statement formats from
        various data sources.
    """
    
    def __init__(self, templates_manager, debit_positive: bool = False):
        super().__init__()
        self.templates_manager = templates_manager
        self.default_debit_positive = debit_positive
     
    def transform_statement(self, df: pd.DataFrame, template: BankTemplate) -> Tuple[BankStatement, Dict[str, Any]]:
        """Transform raw bank statement data using template rules."""
        result_info = {
            'success': False,
            'message': '',
            'rows_processed': len(df),
            'rows_transformed': 0,
            'warnings': []
        }
        
        if df.empty:
            result_info['message'] = "Empty DataFrame provided"
            return BankStatement("", None, "", []), result_info
        
        try:
            # IMPORTANT: Use the template's debit_positive setting, fallback to default if not set
            self.debit_positive = getattr(template, 'debit_positive', self.default_debit_positive)

            # Use skip_rows from template
            skip_rows = getattr(template, 'skip_rows', 0)

            # Find header row
            header_row_idx = self.find_header_row(df, template.header_keywords, skip_rows)
            if header_row_idx is None:
                result_info['message'] = f"Could not find header row for {template.name}"
                return BankStatement("", None, "", []), result_info
            
            # Extract headers and find transactions
            headers = self._extract_headers(df, header_row_idx)
            transaction_indices = self._find_transaction_rows(df, template, header_row_idx)
            
            if not transaction_indices:
                result_info['message'] = "No transaction rows found"
                return BankStatement("", None, "", []), result_info
            
            # Transform transactions
            transactions = self._transform_transactions(df, transaction_indices, headers, template)
            
            # Create bank statement object
            bank_statement = BankStatement(
                bank_name=template.name,
                account_number=None,  # Could be extracted from metadata
                statement_date=datetime.now().isoformat(),
                transactions=transactions,
                metadata={
                    'template_used': template.bank_type,
                    'processing_date': datetime.now().isoformat(),
                    'source_file_rows': len(df)
                }
            )
            
            result_info.update({
                'success': True,
                'message': f"Successfully transformed {len(transactions)} transactions",
                'rows_transformed': len(transactions)
            })
            
            return bank_statement, result_info
            
        except Exception as e:
            result_info['message'] = f"Transformation failed: {str(e)}"
            logger.error(f"Transformation error: {e}")
            return BankStatement("", None, "", []), result_info
   
    def _extract_headers(self, df: pd.DataFrame, header_row_idx: int) -> List[str]:
        """Extract and clean header row while preserving column positions."""
        headers = df.iloc[header_row_idx].fillna("").astype(str).str.strip().str.lower().tolist()
        return headers
    
    def _find_transaction_rows(self, df: pd.DataFrame, template: BankTemplate, header_row_idx: int) -> List[int]:
        """Find rows containing transaction data."""
        transaction_indices = []
        headers = self._extract_headers(df, header_row_idx)
        column_map = template.map_columns(headers)
        date_col_idx = column_map.get('date', 0)
        
        # Debug info
               
        for idx in range(header_row_idx + 1, len(df)):
            row = df.iloc[idx]
            
            if row.isna().all():
                continue
            
            date_cell = str(row.iloc[date_col_idx]).strip() if date_col_idx < len(row) else ""
            if not date_cell:
                continue
            
            # Skip summary rows
            row_text = " ".join([str(val) for val in row if pd.notna(val)]).lower()
            if any(keyword in row_text for keyword in template.skip_keywords):
                continue
            
            if template.matches_date_pattern(date_cell):
                transaction_indices.append(idx)
        
        return transaction_indices
    
    def _transform_transactions(self, df: pd.DataFrame, transaction_indices: List[int], 
                              headers: List[str], template: BankTemplate) -> List[TransactionData]:
        """Transform transaction rows to TransactionData objects."""
        column_map = template.map_columns(headers)
        transactions = []
        
        for row_idx in transaction_indices:
            row = df.iloc[row_idx]
            
            try:
                # Extract data
                date = str(row.iloc[column_map.get('date', 0)]).strip()
                description = self._extract_description(row, column_map, headers)
                amount = self._extract_amount(row, column_map)
                description_date, normalized_description = self._extract_description_date(description, date)

                transaction = TransactionData(
                    date=date,
                    description=description,
                    amount=amount,
                    reference=None,  # Could be extracted if available
                    description_date=description_date,
                    normalized_description=normalized_description
                )
                
                transactions.append(transaction)
                
            except Exception as e:
                logger.warning(f"Error processing row {row_idx}: {e}")
                continue
        
        return transactions
    
    def _extract_description(self, row: pd.Series, column_map: Dict[str, int], headers: List[str]) -> str:
        """Extract description from transaction row."""
        description_parts = []
        
        for col_type in ['type', 'description', 'details']:
            if col_type in column_map:
                idx = column_map[col_type]
                if idx < len(row) and pd.notna(row.iloc[idx]):
                    part = str(row.iloc[idx]).strip()
                    if part:
                        description_parts.append(part)
        
        if not description_parts:
            for i in range(1, max(1, len(row) - 2)):
                if pd.notna(row.iloc[i]):
                    part = str(row.iloc[i]).strip()
                    if part and part.lower() not in ['', 'none', 'null']:
                        description_parts.append(part)
        
        return " | ".join(description_parts) if description_parts else "Transaction"
    
    def _extract_amount(self, row: pd.Series, column_map: Dict[str, int]) -> float:
        """Extract amount from transaction row."""
        debit_amount = 0.0
        credit_amount = 0.0
        
        if 'amount' in column_map:
            amount_val = row.iloc[column_map['amount']]
            if pd.notna(amount_val):
                return self._parse_amount(str(amount_val))
        
        if 'debit' in column_map:
            debit_val = row.iloc[column_map['debit']]
            if pd.notna(debit_val) and str(debit_val).strip():
                debit_amount = self._parse_amount(str(debit_val))
        
        if 'credit' in column_map:
            credit_val = row.iloc[column_map['credit']]
            if pd.notna(credit_val) and str(credit_val).strip():
                credit_amount = self._parse_amount(str(credit_val))
        
        # ACCOUNTING CONVENTION:
        #   debit_positive=True  -> Debits positive, Credits negative
        #   debit_positive=False -> Credits positive, Debits negative
        if self.debit_positive:
            return credit_amount - debit_amount
        return debit_amount + credit_amount
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string with currency/parentheses support."""
        if not amount_str:
            return 0.0
        cleaned = amount_str.replace("£", "").replace(",", "").strip()
        is_negative = cleaned.startswith("-") or \
                    (cleaned.startswith("(") and cleaned.endswith(")"))
        cleaned = cleaned.strip("-()")
        try:
            amount = float(cleaned)
            return -amount if is_negative else amount
        except ValueError:
            return 0.0

    def _extract_description_date(self, description: str, posting_date: str) -> Tuple[Optional[str], str]:
        """Extract date from description and return normalized date and cleaned description."""
        match = DATE_REGEX.search(description)
        if not match:
            return None, description

        date_str = match.group(1)
        normalized_date = self._normalize_description_date(date_str, posting_date)

        normalized_description = (description[:match.start()] + description[match.end():]).strip()
        normalized_description = re.sub(r"\s+", " ", normalized_description)

        return normalized_date, normalized_description

    def _normalize_description_date(self, date_str: str, posting_date: str) -> str:
        """Normalize extracted date to ISO format, inferring missing year."""
        parts = re.split(r"[./]", date_str)
        day = int(parts[0])
        month = int(parts[1])

        year = None
        if len(parts) == 3:
            year_part = parts[2]
            if len(year_part) == 2:
                year = int(year_part)
                year += 2000 if year < 70 else 1900
            else:
                year = int(year_part)
        else:
            posting_dt = pd.to_datetime(posting_date, dayfirst=True, errors="coerce")
            if not pd.isna(posting_dt):
                year = posting_dt.year
            else:
                year = datetime.now().year

        return datetime(year, month, day).date().isoformat()