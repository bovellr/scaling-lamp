# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# models/erp_file_processor.py
# ================================

"""
Enhanced ERP file processor with auto-mapping and data cleaning capabilities.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

from .base_file_processor import BaseFileProcessor

logger = logging.getLogger(__name__)

class ERPFileProcessor(BaseFileProcessor):
    """Enhanced ERP file processor for complex bank statements and ERP files."""
    
    def __init__(self):
        super().__init__()
        # Enhanced column mapping patterns for your Lloyds file
        self.column_patterns = {
            'date': [
                'posting date', 'transaction date', 'date', 'posting_date', 
                'transaction_date', 'gl_date', 'trans_date'
            ],
            'description': [
                'description', 'details', 'narrative', 'particulars', 'memo', 
                'transaction description', 'gl_description','reference details'
            ],
            'amount': [
                'amount', 'value', 'transaction_amount', 'net amount',
                'credits', 'debits', 'ledger balance' , 'gl_amount' # For your Lloyds file
            ],
            'reference': [
                'reference', 'ref', 'transaction_ref', 'gl_transaction_type', 
                'type', 'cheque_ref', 'gl_cheque_ref','payment_type'
            ]
        }

        # Secondary descriptive patterns for multi-column descriptions
        self.secondary_desc_patterns = [
            'cheque_ref', 'cheque_number', 'payment_ref', 'transaction_ref',
            'bank_ref', 'customer_ref', 'doc_number', 'voucher_number',
            'additional_details', 'memo2', 'notes', 'comments'
        ]
    
    def analyze_and_process_file(
        self, file_path: str, sheet_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Simplified file analysis and processing."""

        
        try:
            logger.info("Starting analysis of ERP file: %s", file_path)

            df = self.read_file(file_path, header=0)
            file_type = 'csv' if Path(file_path).suffix.lower() == '.csv' else 'excel'

            analysis = {
                'success': True,
                'file_type': file_type,
                'sheet_name': sheet_name or 'Sheet1',
                'header_row': 0,
                'columns': df.columns.tolist(),
                'mapping': {},
                'confidence': 1.0,
                'metadata': {
                    'file_type': file_type,
                    'sheet_name': sheet_name or 'Sheet1',
                    'header_row': 0,
                    'total_rows': len(df),
                    'data_start_row': 1
                }
            }
          
            return {
                'success': True,
                'data': df,
                'analysis': analysis,
                'row_count': len(df),
                'message': f"Successfully processed {len(df)} transactions"
            }
            
        except Exception as e:
            logger.error(f"Error processing ERP file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to process file: {str(e)}"
            }
    
    def _analyze_file_structure(self, file_path: str, 
                               sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Analyze file structure to find headers and data."""
        try:
            if Path(file_path).suffix.lower() == '.csv':
                return self._analyze_csv_structure(file_path)
            else:
                return self._analyze_excel_structure(file_path, sheet_name)
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_csv_structure(self, file_path: str) -> Dict[str, Any]:
        """Analyze CSV file structure."""
        try:
            # Read first few rows to detect structure
            sample_df = self.read_file(file_path, nrows=10, header=0)
            
            # Assume first row is headers for CSV
            columns = sample_df.columns.tolist()
            
            # Generate mapping
            mapping = self._generate_enhanced_column_mapping(columns)
            
            return {
                'success': True,
                'file_type': 'csv',
                'header_row': 0,
                'columns': columns,
                'mapping': mapping,
                'confidence': self._calculate_mapping_confidence(mapping),
                'metadata': {
                    'file_type': 'csv',
                    'total_rows': len(sample_df),
                    'data_start_row': 1
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_excel_structure(self, file_path: str, 
                                sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Analyze Excel file structure - handles complex layouts like Lloyds."""
        try:
            # Read Excel file to find structure
            xl_file = pd.ExcelFile(file_path)
            
            if sheet_name is None:
                sheet_name = xl_file.sheet_names[0]  # Use first sheet
            
            # Read first 20 rows to find header structure
            sample_df = self.read_file(
                file_path, sheet_name=sheet_name, header=None, nrows=20
            )
            
            # Find the header row (row with most text values)
            header_row_idx = self._find_header_row(sample_df)
            
            if header_row_idx is None:
                return {
                    'success': False,
                    'error': 'Could not identify header row in Excel file'
                }
            
            # Read file with correct header
            full_df = self.read_file(
                file_path, sheet_name=sheet_name, header=header_row_idx
            )
            
            # Generate enhanced column mapping
            mapping = self._generate_enhanced_column_mapping(full_df.columns.tolist())
            
            return {
                'success': True,
                'file_type': 'excel',
                'sheet_name': sheet_name,
                'header_row': header_row_idx,
                'columns': full_df.columns.tolist(),
                'mapping': mapping,
                'confidence': self._calculate_mapping_confidence(mapping),
                'metadata': {
                    'file_type': 'excel',
                    'sheet_name': sheet_name,
                    'header_row': header_row_idx,
                    'total_rows': len(full_df),
                    'data_start_row': header_row_idx + 1
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
       
    def _generate_enhanced_column_mapping(self, columns: List[str]) -> Dict[str, Any]:
        """Generate enhanced automatic column mapping with multi-column support."""
        mapping = {
            'date': None,
            'description': None, 
            'amount': None,
            'reference': None
        }
        
        # Convert to lowercase for matching
        lower_columns = [str(col).lower().strip() for col in columns]
        
        # Enhanced description mapping - can combine multiple descriptive columns
        description_mapping = self._detect_description_columns(lower_columns, columns)
        if description_mapping:
            mapping['description'] = description_mapping
        
        # Enhanced amount mapping - can handle multiple columns (Credits/Debits)
        amount_mapping = self._detect_amount_columns(lower_columns, columns)
        if amount_mapping:
            mapping['amount'] = amount_mapping
        
        # Single column mappings for date and reference
        for field_type in ['date', 'reference']:
            patterns = self.column_patterns[field_type]
            best_match_idx = None
            best_match_score = 0
            
            for i, col_name in enumerate(lower_columns):
                for pattern in patterns:
                    if pattern in col_name:
                        score = 2 if pattern == col_name else 1
                        if score > best_match_score:
                            best_match_score = score
                            best_match_idx = i
            
            mapping[field_type] = best_match_idx
        
        return mapping
    
    def _detect_description_columns(self, lower_columns: List[str], 
                                   original_columns: List[str]) -> Optional[Dict[str, Any]]:
        """Detect description columns - can combine multiple descriptive fields."""
        
        # Primary description patterns
        primary_desc_patterns = [
            'description', 'details', 'narrative', 'particulars', 'memo',
            'gl_description', 'transaction_description', 'trans_desc'
        ]
        
        # Find primary description column
        primary_idx = None
        for pattern in primary_desc_patterns:
            for i, col_name in enumerate(lower_columns):
                if pattern in col_name:
                    primary_idx = i
                    break
            if primary_idx is not None:
                break
        
        # Find secondary description columns
        secondary_indices = []
        for pattern in self.secondary_desc_patterns:
            for i, col_name in enumerate(lower_columns):
                if pattern in col_name and i != primary_idx:  # Don't duplicate primary
                    secondary_indices.append({
                        'index': i,
                        'column_name': original_columns[i],
                        'pattern': pattern,
                        'priority': self._get_secondary_priority(pattern)
                    })
        
        # Sort secondary columns by priority
        secondary_indices.sort(key=lambda x: x['priority'])
        
        if primary_idx is not None:
            if secondary_indices:
                # Combined description mapping
                return {
                    'type': 'combined',
                    'primary_column': primary_idx,
                    'secondary_columns': secondary_indices[:3],  # Max 3 additional columns
                    'combination_method': 'concatenate_with_separator',
                    'separator': ' | '  # Separator between fields
                }
            else:
                # Single primary description
                return {
                    'type': 'single',
                    'column': primary_idx,
                    'method': 'direct'
                }
        
        # No primary found, use best secondary as primary
        if secondary_indices:
            best_secondary = secondary_indices[0]
            remaining_secondary = secondary_indices[1:3]  # Max 2 additional
            
            if remaining_secondary:
                return {
                    'type': 'combined',
                    'primary_column': best_secondary['index'],
                    'secondary_columns': remaining_secondary,
                    'combination_method': 'concatenate_with_separator',
                    'separator': ' | '
                }
            else:
                return {
                    'type': 'single',
                    'column': best_secondary['index'],
                    'method': 'direct'
                }
        
        return None
    
    def _detect_amount_columns(self, lower_columns: List[str], 
                              original_columns: List[str]) -> Optional[Dict[str, Any]]:
        """Detect amount columns - can be single column or Credits/Debits combination."""
        # First, look for single amount columns
        single_amount_patterns = ['amount', 'value', 'transaction_amount', 'net_amount', 'total']
        
        for pattern in single_amount_patterns:
            for i, col_name in enumerate(lower_columns):
                if pattern in col_name:
                    return {
                        'type': 'single',
                        'column': i,
                        'column_name': original_columns[i],
                        'method': 'direct'
                    }
        
        # Look for Credits/Debits combination (like your Lloyds statement)
        credits_idx = None
        debits_idx = None
        
        credits_patterns = ['credits', 'credit', 'receipts', 'deposits', 'inflow']
        debits_patterns = ['debits', 'debit', 'payments', 'withdrawals', 'outflow']
        
        for i, col_name in enumerate(lower_columns):
            if any(pattern in col_name for pattern in credits_patterns):
                credits_idx = i
            elif any(pattern in col_name for pattern in debits_patterns):
                debits_idx = i
        
        # If we found both credits and debits columns
        if credits_idx is not None and debits_idx is not None:
            return {
                'type': 'combined',
                'credits_column': credits_idx,
                'debits_column': debits_idx,
                'credits_name': original_columns[credits_idx],
                'debits_name': original_columns[debits_idx],
                'method': 'credits_minus_debits'  # Credits positive, Debits negative
            }
        
        # If we found only credits column
        if credits_idx is not None:
            return {
                'type': 'single',
                'column': credits_idx,
                'column_name': original_columns[credits_idx],
                'method': 'direct'
            }
        
        # If we found only debits column  
        if debits_idx is not None:
            return {
                'type': 'single',
                'column': debits_idx,
                'column_name': original_columns[debits_idx],
                'method': 'negate'  # Make debits negative
            }
        
        # Look for balance/ledger columns as fallback
        balance_patterns = ['balance', 'ledger_balance', 'running_balance']
        for pattern in balance_patterns:
            for i, col_name in enumerate(lower_columns):
                if pattern in col_name:
                    return {
                        'type': 'single',
                        'column': i,
                        'column_name': original_columns[i],
                        'method': 'direct'
                    }
        
        return None
    
    def _get_secondary_priority(self, pattern: str) -> int:
        """Get priority for secondary description patterns (lower number = higher priority)."""
        priority_map = {
            'cheque_ref': 1,           # High priority - often contains dates
            'cheque_number': 1,
            'payment_ref': 2,
            'transaction_ref': 2,
            'reference': 3,
            'doc_number': 3,
            'voucher_number': 4,
            'bank_ref': 5,
            'customer_ref': 5,
            'additional_details': 6,
            'memo2': 7,
            'notes': 8,
            'comments': 9
        }
        return priority_map.get(pattern, 10)  # Default low priority
    
    def _process_data_with_mapping(self, file_path: str, mapping: Dict[str, Any], 
                                  metadata: Dict[str, Any]) -> pd.DataFrame:
        """Process file data using the enhanced column mapping."""
        try:
            # Read file with correct settings
            read_kwargs: Dict[str, Any] = {
                'header': metadata.get('header_row', 0)
            }

            if metadata['file_type'] == 'excel':
                read_kwargs['sheet_name'] = metadata.get('sheet_name')
            df = self.read_file(file_path, **read_kwargs)
            
            # Create result DataFrame with mapped columns
            result_df = pd.DataFrame()
            
            # Map date column
            if mapping.get('date') is not None:
                date_col = df.iloc[:, mapping['date']]
                result_df['Date'] = pd.to_datetime(date_col, errors='coerce')
            
            # Enhanced description mapping - handles multiple columns
            if mapping.get('description') is not None:
                result_df['Description'] = self._process_description_mapping(df, mapping['description'])
            
            # Enhanced amount mapping - handles multiple columns
            if mapping.get('amount') is not None:
                result_df['Amount'] = self._process_amount_mapping(df, mapping['amount'])
            
            # Map reference column
            if mapping.get('reference') is not None:
                ref_col = df.iloc[:, mapping['reference']]
                result_df['Reference'] = ref_col.astype(str)
            else:
                result_df['Reference'] = ''
            
            # Clean the data - CRITICAL for your requirements
            cleaned_df = self._clean_erp_data(result_df)
            
            return cleaned_df
            
        except Exception as e:
            logger.error(f"Error processing data with mapping: {e}")
            raise
    
    def _process_description_mapping(self, df: pd.DataFrame, desc_config: Dict[str, Any]) -> pd.Series:
        """Process description mapping - can combine multiple descriptive columns."""
        try:
            if desc_config['type'] == 'single':
                # Single column mapping
                desc_col = df.iloc[:, desc_config['column']]
                return desc_col.astype(str).str.strip()
                
            elif desc_config['type'] == 'combined':
                # Multiple column combination
                primary_col = df.iloc[:, desc_config['primary_column']]
                primary_desc = primary_col.astype(str).str.strip()
                
                # Process secondary columns
                secondary_parts = []
                for sec_info in desc_config['secondary_columns']:
                    sec_col = df.iloc[:, sec_info['index']]
                    sec_values = sec_col.astype(str).str.strip()
                    
                    # Clean secondary values (remove 'nan', empty strings, etc.)
                    sec_values = sec_values.replace(['nan', 'None', 'NaN', ''], pd.NA)
                    secondary_parts.append(sec_values)
                
                # Combine all parts
                combined_descriptions = []
                separator = desc_config.get('separator', ' | ')
                
                for i in range(len(df)):
                    parts = [primary_desc.iloc[i]]
                    
                    # Add non-null secondary parts
                    for sec_series in secondary_parts:
                        if pd.notna(sec_series.iloc[i]) and sec_series.iloc[i].strip():
                            parts.append(sec_series.iloc[i].strip())
                    
                    # Join all non-empty parts
                    combined = separator.join(part for part in parts if part and part.strip())
                    combined_descriptions.append(combined)
                
                return pd.Series(combined_descriptions)
            
            else:
                raise ValueError(f"Unknown description mapping type: {desc_config['type']}")
                
        except Exception as e:
            logger.error(f"Error processing description mapping: {e}")
            # Return primary column as fallback
            if desc_config.get('primary_column') is not None:
                return df.iloc[:, desc_config['primary_column']].astype(str).str.strip()
            elif desc_config.get('column') is not None:
                return df.iloc[:, desc_config['column']].astype(str).str.strip()
            else:
                return pd.Series([''] * len(df))
    
    def _process_amount_mapping(self, df: pd.DataFrame, amount_config: Dict[str, Any]) -> pd.Series:
        """Process amount mapping based on configuration (single or multiple columns)."""
        try:
            if amount_config['type'] == 'single':
                # Single column mapping
                amount_col = df.iloc[:, amount_config['column']]
                amounts = pd.to_numeric(amount_col, errors='coerce')
                
                if amount_config['method'] == 'negate':
                    # Make values negative (for debit columns)
                    amounts = -amounts.abs()
                elif amount_config['method'] == 'direct':
                    # Use values as-is
                    pass
                
                return amounts
                
            elif amount_config['type'] == 'combined':
                # Multiple column mapping (Credits/Debits)
                credits_col = df.iloc[:, amount_config['credits_column']]
                debits_col = df.iloc[:, amount_config['debits_column']]
                
                credits = pd.to_numeric(credits_col, errors='coerce').fillna(0)
                debits = pd.to_numeric(debits_col, errors='coerce').fillna(0)
                
                if amount_config['method'] == 'credits_minus_debits':
                    # Credits positive, Debits negative
                    amounts = credits - debits
                elif amount_config['method'] == 'sum':
                    # Both positive (rare case)
                    amounts = credits + debits
                else:
                    # Default: Credits positive, Debits negative
                    amounts = credits - debits
                
                return amounts
            
            else:
                raise ValueError(f"Unknown amount mapping type: {amount_config['type']}")
                
        except Exception as e:
            logger.error(f"Error processing amount mapping: {e}")
            # Return zero series as fallback
            return pd.Series([0] * len(df))
    
    def _clean_erp_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean ERP data by removing blank rows, totals, and invalid dates."""
        logger.info(f"Cleaning ERP data: {len(df)} initial rows")
        
        # Step 1: Remove rows where ALL required fields are empty/null
        required_cols = ['Date', 'Description', 'Amount']
        available_required = [col for col in required_cols if col in df.columns]
        
        if available_required:
            # Remove rows where all required columns are null/empty
            df = df.dropna(subset=available_required, how='all')
        
        # Step 2: Remove rows with invalid/missing dates
        if 'Date' in df.columns:
            df = df.dropna(subset=['Date'])
            # Remove rows where date couldn't be parsed (NaT values)
            df = df[df['Date'].notna()]
        
        # Step 3: Remove rows with missing amounts
        if 'Amount' in df.columns:
            df = df.dropna(subset=['Amount'])
            # Remove rows where amount is 0 or couldn't be parsed
            df = df[df['Amount'] != 0]
            df = df[df['Amount'].notna()]
        
        # Step 4: Remove rows that look like totals or summaries
        if 'Description' in df.columns:
            # Remove rows with descriptions containing total/summary keywords
            total_keywords = ['total', 'summary', 'balance brought forward', 
                            'carried forward', 'opening balance', 'closing balance',
                            'grand total', 'subtotal']
            
            for keyword in total_keywords:
                mask = ~df['Description'].str.contains(keyword, case=False, na=False)
                df = df[mask]
        
        # Step 5: Remove completely blank rows (all fields empty/null)
        df = df.dropna(how='all')
        
        # Step 6: Clean string fields
        string_cols = ['Description', 'Reference']
        for col in string_cols:
            if col in df.columns:
                # Remove leading/trailing whitespace
                df[col] = df[col].astype(str).str.strip()
                # Replace 'nan' strings with empty strings
                df[col] = df[col].replace(['nan', 'None', 'NaN'], '')
        
        # Reset index after cleaning
        df = df.reset_index(drop=True)
        
        logger.info(f"Cleaned ERP data: {len(df)} final rows")
        return df
    
    def _calculate_mapping_confidence(self, mapping: Dict[str, Any]) -> float:
        """Calculate confidence score for the mapping (supports multi-column)."""
        required_fields = ['date', 'description', 'amount']
        confidence_score = 0.0
        
        # Check each required field
        for field in required_fields:
            field_value = mapping.get(field)
            
            if field == 'amount' and isinstance(field_value, dict):
                # Enhanced scoring for amount fields
                if field_value['type'] == 'combined':
                    confidence_score += 0.4  # Higher confidence for combined Credits/Debits
                elif field_value['type'] == 'single':
                    confidence_score += 0.3  # Good confidence for single amount
            elif field == 'description' and isinstance(field_value, dict):
                # Enhanced scoring for description fields
                if field_value['type'] == 'combined':
                    base_score = 0.3
                    # Bonus for high-quality secondary columns (like cheque_ref)
                    secondary_cols = field_value.get('secondary_columns', [])
                    quality_bonus = sum(0.05 for col in secondary_cols 
                                      if col.get('priority', 10) <= 3)  # High priority patterns
                    confidence_score += min(base_score + quality_bonus, 0.4)
                elif field_value['type'] == 'single':
                    confidence_score += 0.3
            elif field_value is not None:
                confidence_score += 0.3  # Standard confidence for other fields
        
        # Bonus for optional reference field
        if mapping.get('reference') is not None:
            confidence_score += 0.1
        
        return min(confidence_score, 1.0)



