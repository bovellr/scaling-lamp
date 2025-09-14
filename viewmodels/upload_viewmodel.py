# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
# viewmodels/upload_viewmodel.py
"""
ViewModel for file upload and bank statement transformation.
Integrates your bank transformation functionality.
"""

from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import logging
import pandas as pd
from datetime import datetime

from models.data_models import BankTemplate, BankStatement, ERPTransaction, TransactionData
from models.erp_file_processor import ERPFileProcessor
from models.file_processor import FileProcessor
from models.database import TemplateRepository
from .base_viewmodel import BaseViewModel
from PySide6.QtCore import Signal

logger = logging.getLogger(__name__)

class UploadViewModel(BaseViewModel):
    """ViewModel for file upload and transformation logic."""
    
    # Bank statement signals (enhanced from your existing)
    bank_file_uploaded = Signal(str)                    # file_path
    bank_data_transformed = Signal(object, dict)        # statement, transformation_result
    transformation_started = Signal(str)                # template_name
    transformation_completed = Signal(object, dict)     # statement, result_info
    transformation_failed = Signal(str)                 # error_message
    
    # ERP data signals (new functionality)
    erp_data_loaded = Signal(object, str, str)          # data, source_type, source_info
    erp_loading_started = Signal(str)                   # operation_description
    erp_loading_progress = Signal(int)                  # progress_percentage
    erp_loading_failed = Signal(str, str)              # source, error_message
    
    # Combined processing signals
    both_sources_ready = Signal(object, object, dict)   # bank_data, erp_data, metadata
    data_cleared = Signal(str)                          # source_name
    
    # Template management signals (from your existing)
    templates_loaded = Signal(list)                     # available_templates
    template_selected = Signal(object)                  # selected_template
    
    # Property change signals
    processing_enabled_changed = Signal(bool)
    erp_source_type_changed = Signal(str)              # 'file' or 'database'


    def __init__(self, config_service=None):
        super().__init__()
        self.template_repository = TemplateRepository()
        self.file_processor = FileProcessor(self)

        # Store config service if provided
        self.config_service = config_service
        # Enhanced state management
        self._init_bank_properties()
        self._init_erp_properties()
        self._init_processing_state()
        
        # Load your existing templates
        self._load_templates()
        
        # Initialize ERP database service (if available)
        self._erp_database_service = None
    
    def _init_bank_properties(self):
        """Initialize bank-related properties (your existing functionality)"""
        self._available_templates: List[BankTemplate] = []
        self._selected_template: Optional[BankTemplate] = None
        self._uploaded_file_path: Optional[str] = None
        self._transformed_statement: Optional[BankStatement] = None
        self._transformation_result: Optional[dict] = None
        self._bank_raw_data: Optional[pd.DataFrame] = None
    
    def _init_erp_properties(self):
        """Initialize ERP-related properties (new functionality)"""
        self._erp_data: Optional[pd.DataFrame] = None
        self._erp_source_type: str = 'file'  # 'file' or 'database'
        self._erp_source_info: str = ""
        self._erp_file_path: Optional[str] = None
        self._erp_ledger: Optional[ERPTransaction] = None
    
    def _init_processing_state(self):
        """Initialize processing state"""
        self._is_processing: bool = False
        self._processing_enabled: bool = False

    # ========================================================================
    # BANK STATEMENT PROPERTIES - Your existing functionality enhanced
    # ========================================================================
    
    @property
    def available_templates(self) -> List[BankTemplate]:
        return self._available_templates
    
    @property
    def selected_template(self) -> Optional[BankTemplate]:
        return self._selected_template
    
    @selected_template.setter
    def selected_template(self, template: Optional[BankTemplate]):
        if self._selected_template != template:
            self._selected_template = template
            self.template_selected.emit(template)
            self.notify_property_changed('selected_template', template)
    
    @property
    def uploaded_file_path(self) -> Optional[str]:
        return self._uploaded_file_path
    
    @property
    def transformed_statement(self) -> Optional[BankStatement]:
        return self._transformed_statement
    
    @property
    def transformation_result(self) -> Optional[dict]:
        return self._transformation_result
    
    @property
    def bank_raw_data(self) -> Optional[pd.DataFrame]:
        """Access to raw bank data for advanced processing"""
        return self._bank_raw_data
    
    # ========================================================================
    # ERP DATA PROPERTIES - New functionality
    # ========================================================================
    
    @property
    def erp_data(self) -> Optional[pd.DataFrame]:
        return self._erp_data
    
    @erp_data.setter
    def erp_data(self, value: Optional[pd.DataFrame]):
        if self._erp_data is not value:
            self._erp_data = value
            self.notify_property_changed('erp_data', value)
            self._update_processing_enabled()
    
    @property
    def erp_source_type(self) -> str:
        return self._erp_source_type
    
    @erp_source_type.setter
    def erp_source_type(self, value: str):
        if self._erp_source_type != value:
            self._erp_source_type = value
            self.erp_source_type_changed.emit(value)
            self.notify_property_changed('erp_source_type', value)
    
    @property
    def erp_source_info(self) -> str:
        return self._erp_source_info
    
    @property
    def erp_ledger(self) -> Optional[ERPTransaction]:
        return self._erp_ledger
    
    # ========================================================================
    # PROCESSING STATE PROPERTIES
    # ========================================================================
    
    @property
    def processing_enabled(self) -> bool:
        return self._processing_enabled
    
    @property
    def is_processing(self) -> bool:
        return self._is_processing
    
    @property
    def has_bank_data(self) -> bool:
        return self._transformed_statement is not None
    
    @property
    def has_erp_data(self) -> bool:
        return self._erp_data is not None and len(self._erp_data) > 0
    
    @property
    def data_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of loaded data"""
        bank_records = len(self._transformed_statement.transactions) if self.has_bank_data else 0
        erp_records = len(self._erp_data) if self.has_erp_data else 0
        
        return {
            'bank_records': bank_records,
            'erp_records': erp_records,
            'bank_source': Path(self._uploaded_file_path).name if self._uploaded_file_path else None,
            'bank_template': self._selected_template.name if self._selected_template else None,
            'erp_source_type': self._erp_source_type,
            'erp_source_info': self._erp_source_info,
            'both_loaded': self.has_bank_data and self.has_erp_data,
            'last_updated': datetime.now().isoformat(),
            'transformation_success_rate': self._get_transformation_success_rate()
        }
    
    def _get_transformation_success_rate(self) -> Optional[float]:
        """Get transformation success rate from last result"""
        if not self._transformation_result:
            return None
        
        rows_processed = self._transformation_result.get('rows_processed', 0)
        rows_transformed = self._transformation_result.get('rows_transformed', 0)
        
        if rows_processed > 0:
            return (rows_transformed / rows_processed) * 100
        return None

    # ========================================================================
    # BANK STATEMENT METHODS - Your existing functionality enhanced
    # ========================================================================
    
    def upload_file(self, file_path: str) -> bool:
        """Handle bank file upload (your existing method enhanced)"""
        try:
            self.clear_error()
            
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                self.error_message = "File does not exist"
                return False
            
            if file_path_obj.suffix.lower() not in ['.csv', '.xlsx', '.xls']:
                self.error_message = "Unsupported file format"
                return False
            
            self._uploaded_file_path = file_path
            self.bank_file_uploaded.emit(file_path)
            self.notify_property_changed('uploaded_file_path', file_path)
            
            # Try to auto-detect template
            self._auto_detect_template(file_path)
            
            return True
            
        except Exception as e:
            self.error_message = f"File upload failed: {str(e)}"
            return False
    
    def transform_statement(self) -> bool:
        """Transform uploaded statement using selected template (your existing method enhanced)"""
        if not self._uploaded_file_path or not self._selected_template:
            self.error_message = "Please select a file and template first"
            return False
        
        try:
            self.is_loading = True
            self.clear_error()
            
            # Emit transformation started
            self.transformation_started.emit(self._selected_template.name)
            
            # Read file and store raw data
            self._bank_raw_data = self.file_processor.read_file(self._uploaded_file_path)
            
            # Transform using your existing template system
            statement, result_info = self.file_processor.transform_statement(
                self._bank_raw_data, 
                self._selected_template
            )
            
            if result_info['success']:
                self._transformed_statement = statement
                self._transformation_result = result_info
                
                # Emit signals
                self.bank_data_transformed.emit(statement, result_info)
                self.transformation_completed.emit(statement, result_info)
                self.notify_property_changed('transformed_statement', statement)
                self.notify_property_changed('transformation_result', result_info)
                
                # Update processing state
                self._update_processing_enabled()
                
                logger.info(f"Bank statement transformed: {result_info.get('rows_transformed', 0)} transactions")
                return True
            else:
                self.error_message = result_info['message']
                self.transformation_failed.emit(result_info['message'])
                return False
                
        except Exception as e:
            error_msg = f"Transformation failed: {str(e)}"
            self.error_message = error_msg
            self.transformation_failed.emit(error_msg)
            logger.error(f"Bank transformation error: {e}")
            return False
        finally:
            self.is_loading = False
    
    def _auto_detect_template(self, file_path: str):
        """Auto-detect appropriate template based on file content"""
        try:
            # Read first few rows to detect format
            sample_data = self.file_processor.read_file(file_path, nrows=10)
            
            # Try to match headers with templates
            if sample_data is not None:
                columns = [str(col).lower().strip() for col in sample_data.columns]
                
                best_match = None
                best_score = 0
                
                for template in self._available_templates:
                    score = self._calculate_template_match_score(columns, template)
                    if score > best_score and score > 0.5:  # Minimum 50% match
                        best_match = template
                        best_score = score
                
                if best_match:
                    self.selected_template = best_match
                    logger.info(f"Auto-detected template: {best_match.name} (score: {best_score:.2f})")
                    
        except Exception as e:
            logger.warning(f"Template auto-detection failed: {e}")
    
    def _calculate_template_match_score(self, columns: List[str], template: BankTemplate) -> float:
        """Calculate how well a template matches the file columns"""
        header_keywords = [str(kw).lower().strip() for kw in template.header_keywords]
        matches = sum(1 for col in columns if any(keyword in col for keyword in header_keywords))
        return matches / len(header_keywords) if header_keywords else 0
    
    # ========================================================================
    # ERP DATA METHODS - New functionality
    # ========================================================================
    
    def load_erp_from_file(self, file_path: str, mapping: Optional[Dict[str, int]] = None) -> bool:
        """Enhanced ERP file loading with auto-mapping and data cleaning."""
        try:
            self._is_processing = True
            self.clear_error()
            
            self.erp_loading_started.emit(f"Loading ERP file: {Path(file_path).name}")
            
            # Validate file
            if not self._validate_file(file_path):
                return False
            
            # Use enhanced processor
            processor = ERPFileProcessor()
            
            # Process file with enhanced capabilities
            result = processor.analyze_and_process_file(file_path)
            
            if not result['success']:
                self.error_message = result.get('message', 'File processing failed')
                return False
            
            # Get cleaned and processed data
            data = result['data']
            
            if data.empty:
                self.error_message = "No valid transaction data found after processing and cleaning"
                return False
            
            # Store processed data
            self._erp_data = data
            self._erp_file_path = file_path
            self.erp_source_type = 'file'
            
            # Enhanced source info with processing details
            analysis = result.get('analysis', {})
            confidence = analysis.get('confidence', 0)
            original_rows = result.get('analysis', {}).get('metadata', {}).get('total_rows', len(data))
            
            source_info = (f"{Path(file_path).name} "
                        f"({len(data)} transactions, "
                        f"{confidence:.1%} confidence, "
                        f"{original_rows} → {len(data)} after cleaning)")
            self._erp_source_info = source_info
            
            # Emit success signals with enhanced metadata
            metadata = {
                'processing_stats': {
                    'original_rows': original_rows,
                    'cleaned_rows': len(data),
                    'confidence': confidence,
                    'mapping_details': analysis.get('mapping', {})
                }
            }
            
            self.erp_data_loaded.emit(data, 'file', source_info)
            
            logger.info(f"Enhanced ERP file loaded: {file_path} ({len(data)} transactions, {confidence:.1%} confidence)")
            return True
            
        except Exception as e:
            error_msg = f"Failed to load ERP file: {str(e)}"
            self.error_message = error_msg
            self.erp_loading_failed.emit('file', error_msg)
            logger.error(f"Enhanced ERP file loading error: {e}")
            return False
            
        finally:
            self._is_processing = False
    
    def load_erp_from_database(self, connection_params: Dict[str, Any], 
                              query_params: Optional[Dict[str, Any]] = None) -> bool:
        """Load ERP data from database"""
        try:
            self._is_processing = True
            self.clear_error()
            
            self.erp_loading_started.emit("Connecting to ERP database...")
            
            # Initialize database service if needed
            if not self._erp_database_service:
                from models.erp_database_service import ERPDatabaseService
                self._erp_database_service = ERPDatabaseService(connection_params)
            
            # Test connection
            if not self._erp_database_service.test_connection():
                raise ConnectionError("Database connection failed")
            
            # Load data
            data = self._erp_database_service.load_ledger_data(query_params)
            if data is None or len(data) == 0:
                raise ValueError("No data returned from database")
            
            # Validate data
            if not self._validate_erp_data(data):
                return False
            
            # Create ERP ledger model
            self._erp_ledger = ERPTransaction.from_dataframe(data, "database_query")
            
            # Update properties
            self.erp_source_type = 'database'
            self.erp_data = data
            
            # Create source info
            date_info = ""
            if query_params and 'start_date' in query_params:
                date_info = f" ({query_params['start_date']} to {query_params.get('end_date', 'now')})"
            
            source_info = f"Database: {connection_params.get('host', 'ERP')} ({len(data)} records){date_info}"
            self._erp_source_info = source_info
            
            # Emit success signals
            self.erp_data_loaded.emit(data, 'database', source_info)
            
            logger.info(f"ERP data loaded from database: {len(data)} records")
            return True
            
        except Exception as e:
            error_msg = f"Failed to load from database: {str(e)}"
            self.error_message = error_msg
            self.erp_loading_failed.emit('database', error_msg)
            logger.error(f"ERP database loading error: {e}")
            return False
            
        finally:
            self._is_processing = False
    
    # ========================================================================
    # COMBINED PROCESSING - New functionality
    # ========================================================================
    
    def process_both_sources(self) -> bool:
        """Process both bank and ERP data for matching"""
        try:
            if not (self.has_bank_data and self.has_erp_data):
                self.error_message = "Both bank and ERP data must be loaded before processing"
                return False
            
            self._is_processing = True
            self.clear_error()
            
            # Convert bank statement to transaction list
            bank_transactions = self._transformed_statement.transactions
            
            # Convert ERP data to transaction list
            erp_transactions = self._convert_erp_to_transactions()
            
            # Create comprehensive metadata
            metadata = self.data_summary
            metadata['processed_at'] = datetime.now().isoformat()
            
            # Emit ready signal
            self.both_sources_ready.emit(bank_transactions, erp_transactions, metadata)
            
            logger.info(f"Both sources processed: {len(bank_transactions)} bank, {len(erp_transactions)} ERP transactions")
            return True
            
        except Exception as e:
            error_msg = f"Failed to process both sources: {str(e)}"
            self.error_message = error_msg
            logger.error(f"Combined processing error: {e}")
            return False
            
        finally:
            self._is_processing = False
    
    def _convert_erp_to_transactions(self) -> List[TransactionData]:
        """Convert ERP DataFrame to TransactionData objects"""
        records = self._erp_data.to_dict('records')
        transactions = [
            TransactionData(
                id=f"erp_{idx}",
                date=str(row.get('Date', '')),
                description=str(row.get('Description', '')),
                amount=float(row.get('Amount', 0)),
                source='erp'
            )
            for idx, row in enumerate(records)
        ]
        
        return transactions
    
    # ========================================================================
    # DATA MANAGEMENT - Enhanced
    # ========================================================================
    
    def clear_bank_data(self):
        """Clear bank data"""
        self._uploaded_file_path = None
        self._transformed_statement = None
        self._transformation_result = None
        self._bank_raw_data = None
        self._selected_template = None
        
        self.notify_property_changed('uploaded_file_path', None)
        self.notify_property_changed('transformed_statement', None)
        self.notify_property_changed('selected_template', None)
        self.notify_property_changed('transformation_result', None)
        self.notify_property_changed('error_message', None)
        self.notify_property_changed('is_loading', False)

        if hasattr(self, '_selected_template'):
            self.notify_property_changed('selected_template', self._selected_template)
        
        self._update_processing_enabled()
        self.data_cleared.emit('bank')
        
        logger.info("Bank data cleared")
    
    def clear_erp_data(self):
        """Clear ERP data"""
        self._erp_data = None
        self._erp_source_info = ""
        self._erp_file_path = None
        self._erp_ledger = None
        
        self.erp_data = None
        self._update_processing_enabled()
        self.data_cleared.emit('erp')
        
        logger.info("ERP data cleared")
    
    def clear_all_data(self):
        """Clear all loaded data"""
        self.clear_bank_data()
        self.clear_erp_data()
        self.data_cleared.emit('all')
    
    # ========================================================================
    # TEMPLATE MANAGEMENT - Your existing functionality
    # ========================================================================
    
    def _load_templates(self):
        """Load available bank templates (your existing method)"""
        try:
            # Load default templates (your existing templates)
            default_templates = self._get_default_templates()
            
            # Load custom templates from repository
            try:
                custom_templates = self.template_repository.get_all_templates()
            except Exception as e:
                logger.warning(f"Failed to load custom templates: {e}")
                custom_templates = []
            
            # Combine templates
            all_templates = default_templates + custom_templates
            
            # Remove duplicates (prefer custom over default)
            template_dict = {}
            for template in all_templates:
                template_dict[template.bank_type] = template
            
            self._available_templates = list(template_dict.values())
            self.templates_loaded.emit(self._available_templates)
            self.notify_property_changed('available_templates', self._available_templates)
            
            logger.info(f"Loaded {len(self._available_templates)} templates")
            
        except Exception as e:
            self.error_message = f"Failed to load templates: {str(e)}"
            logger.error(f"Template loading error: {e}")

    def _get_default_templates(self) -> List[BankTemplate]:
        """Get your existing default templates"""
        return [
            BankTemplate(
                name="Lloyds Bank",
                bank_type="lloyds",
                debit_positive=False,
                skip_rows=6,
                header_keywords=["posting date", "date", "type", "details", "debits", "credits"],
                date_patterns=[
                    r"\d{1,2}[-/]\w{3}[-/]\d{4}",      # 11-Apr-2025
                    r"\d{1,2}[-/]\d{1,2}[-/]\d{4}",    # 11/04/2025
                ],
                skip_keywords=["totals", "balance", "end of report", "closing", "opening"],
                column_mapping={
                    "date": ["posting date"],
                    "type": ["type"],
                    "description": ["details"],
                    "debit": ["debits"],
                    "credit": ["credits"]
                },
                description="Standard Lloyds Bank statement format"
            ),
            
            BankTemplate(
                name="NatWest/RBS Bank",
                bank_type="rbs/natwest",
                debit_positive=False,
                skip_rows=0,
                header_keywords=["date", "narrative #1", "narrative #3","type", "value", "balance"],
                date_patterns=[
                    r"\d{1,2}\s+\w{3}\s+\d{4}",        # 11 Apr 2025
                    r"\d{1,2}/\d{1,2}/\d{4}"           # 11/04/2025
                ],
                skip_keywords=["balance brought forward", "balance carried forward", "total"],
                column_mapping={
                    "date": ["date"],
                    "type": ["type"],
                    "description": ["narrative #1", "narrative #3"],
                    "debit": ["debit"],
                    "credit": ["credit"]
                },
                description="NatWest and RBS statement format"
            ),
            
            # Add more of your existing templates here
            BankTemplate(
                name="Barclays Bank",
                bank_type="barclays",
                header_keywords=["date", "description", "amount", "balance"],
                date_patterns=[
                    r"\d{1,2}/\d{1,2}/\d{4}",          # 11/04/2025
                    r"\d{4}-\d{1,2}-\d{1,2}",          # 2025-04-11
                ],
                skip_keywords=["opening balance", "closing balance", "statement total"],
                column_mapping={
                    "date": ["date", "transaction date", "value date"],
                    "description": ["description", "details", "memo"],
                    "amount": ["amount", "value", "transaction amount"]
                },
                description="Barclays Bank statement format"
            )
        ]
    
    def get_template_by_type(self, bank_type: str) -> Optional[BankTemplate]:
        """Get template by bank type (your existing method)"""
        for template in self._available_templates:
            if template.bank_type == bank_type:
                return template
        return None
    
    def refresh_templates(self):
        """Refresh the list of available templates (your existing method)"""
        self._load_templates()
    
    # ========================================================================
    # VALIDATION AND HELPER METHODS
    # ========================================================================
    
    def _validate_file(self, file_path: str) -> bool:
        """Validate file exists and has correct extension"""
        path = Path(file_path)
        
        if not path.exists():
            self.error_message = f"File not found: {file_path}"
            return False
        
        if path.suffix.lower() not in ['.csv', '.xlsx', '.xls']:
            self.error_message = f"Unsupported file type: {path.suffix}"
            return False
        
        return True
    
    def _load_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Load file using your existing file processor"""
        try:
            return self.file_processor.read_file(file_path)
        except Exception as e:
            self.error_message = f"Failed to read file: {str(e)}"
            return None
    
    def _validate_erp_data(self, data: pd.DataFrame) -> bool:
        """Validate ERP data structure"""
        required_columns = ['Date', 'Description', 'Amount']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            self.error_message = f"ERP data missing required columns: {', '.join(missing_columns)}"
            return False
        
        if len(data) == 0:
            self.error_message = "ERP data contains no records"
            return False
        
        return True
    
    def _update_processing_enabled(self):
        """Update processing enabled state"""
        new_state = self.has_bank_data and self.has_erp_data and not self._is_processing
        
        if self._processing_enabled != new_state:
            self._processing_enabled = new_state
            self.processing_enabled_changed.emit(new_state)
            self.notify_property_changed('processing_enabled', new_state)
    
    # ========================================================================
    # DEPENDENCY INJECTION
    # ========================================================================
    
    def set_erp_database_service(self, service):
        """Inject ERP database service"""
        self._erp_database_service = service
    
    def set_template_repository(self, repository):
        """Inject template repository"""
        self.template_repository = repository
        self._load_templates()
    
    def set_file_processor(self, processor):
        """Inject file processor"""
        self.file_processor = processor