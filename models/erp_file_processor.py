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

logger = logging.getLogger(__name__)

class ERPFileProcessor:
    """Enhanced ERP file processor for complex bank statements and ERP files."""
    
    def __init__(self):
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
    
    def analyze_and_process_file(self, file_path: str, 
                                sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Analyze file structure and process ERP data with auto-mapping."""
        try:
            # Step 1: Analyze file structure
            analysis = self._analyze_file_structure(file_path, sheet_name)
            
            if not analysis['success']:
                return analysis
            
            # Step 2: Find and process data
            processed_data = self._process_data_with_mapping(
                file_path, analysis['mapping'], analysis['metadata']
            )
            
            return {
                'success': True,
                'data': processed_data,
                'analysis': analysis,
                'row_count': len(processed_data),
                'message': f"Successfully processed {len(processed_data)} transactions"
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
    
    def _analyze_excel_structure(self, file_path: str, 
                                sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Analyze Excel file structure - handles complex layouts like Lloyds."""
        try:
            # Read Excel file to find structure
            xl_file = pd.ExcelFile(file_path)
            
            if sheet_name is None:
                sheet_name = xl_file.sheet_names[0]  # Use first sheet
            
            # Read first 20 rows to find header structure
            sample_df = pd.read_excel(file_path, sheet_name=sheet_name, 
                                    header=None, nrows=20)
            
            # Find the header row (row with most text values)
            header_row_idx = self._find_header_row(sample_df)
            
            if header_row_idx is None:
                return {
                    'success': False,
                    'error': 'Could not identify header row in Excel file'
                }
            
            # Read file with correct header
            full_df = pd.read_excel(file_path, sheet_name=sheet_name, 
                                   header=header_row_idx)
            
            # Generate column mapping
            mapping = self._generate_column_mapping(full_df.columns.tolist())
            
            return {
                'success': True,
                'sheet_name': sheet_name,
                'header_row': header_row_idx,
                'columns': full_df.columns.tolist(),
                'mapping': mapping,
                'confidence': self._calculate_mapping_confidence(mapping),
                'metadata': {
                    'file_type': 'excel',
                    'total_rows': len(full_df),
                    'data_start_row': header_row_idx + 1
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """Find row that contains column headers."""
        best_row = None
        max_text_count = 0
        
        for idx, row in df.iterrows():
            text_count = 0
            non_null_count = 0
            
            for val in row:
                if pd.notna(val):
                    non_null_count += 1
                    if isinstance(val, str) and len(val.strip()) > 2:
                        text_count += 1
            
            # Good header row has many text values and reasonable coverage
            if text_count >= 3 and text_count >= non_null_count * 0.6:
                if text_count > max_text_count:
                    max_text_count = text_count
                    best_row = idx
        
        return best_row
    
    def _generate_column_mapping(self, columns: List[str]) -> Dict[str, Any]:
        """Generate automatic column mapping with support for multiple column indexes."""
        mapping = {
            'date': None,
            'description': None, 
            'amount': None,
            'reference': None
        }
        
        # Convert to lowercase for matching
        lower_columns = [str(col).lower().strip() for col in columns]
        
        # Enhanced amount mapping - can handle multiple columns (Credits/Debits)
        amount_mapping = self._detect_amount_columns(lower_columns)
        if amount_mapping:
            mapping['amount'] = amount_mapping
        
        # Single column mappings for other fields
        for field_type in ['date', 'description', 'reference']:
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
    
    def _generate_column_mapping(self, columns: List[str]) -> Dict[str, Any]:
        """Generate automatic column mapping with support for multiple column indexes."""
        mapping = {
            'date': None,
            'description': None, 
            'amount': None,
            'reference': None
        }
        
        # Convert to lowercase for matching
        lower_columns = [str(col).lower().strip() for col in columns]
        
        # Enhanced description mapping - can combine multiple descriptive columns
        description_mapping = self._detect_description_columns(lower_columns)
        if description_mapping:
            mapping['description'] = description_mapping
        
        # Enhanced amount mapping - can handle multiple columns (Credits/Debits)
        amount_mapping = self._detect_amount_columns(lower_columns)
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
    
    def _detect_description_columns(self, lower_columns: List[str]) -> Optional[Dict[str, Any]]:
        """Detect description columns - can combine multiple descriptive fields."""
        
        # Primary description patterns
        primary_desc_patterns = [
            'description', 'details', 'narrative', 'particulars', 'memo',
            'gl_description', 'transaction_description', 'trans_desc'
        ]
        
        # Secondary descriptive patterns (cheque refs, additional details)
        secondary_desc_patterns = [
            'cheque_ref', 'cheque_number', 'reference', 'doc_number', 'voucher_number',
            'additional_details', 'memo2', 'notes', 'comments', 'ref_details',
            'payment_ref', 'transaction_ref', 'bank_ref', 'customer_ref'
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
        for pattern in secondary_desc_patterns:
            for i, col_name in enumerate(lower_columns):
                if pattern in col_name and i != primary_idx:  # Don't duplicate primary
                    secondary_indices.append({
                        'index': i,
                        'column_name': col_name,
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
    
    def _calculate_mapping_confidence(self, mapping: Dict[str, Any]) -> float:
        """Calculate confidence score for the mapping (updated for multi-column support)."""
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
            elif field_value is not None:
                confidence_score += 0.3  # Standard confidence for other fields
        
        # Bonus for optional reference field
        if mapping.get('reference') is not None:
            confidence_score += 0.1
        
    def _calculate_mapping_confidence(self, mapping: Dict[str, Any]) -> float:
        """Calculate confidence score for the mapping (updated for multi-column support)."""
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


