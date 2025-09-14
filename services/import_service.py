# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# IMPORT SERVICE
# ============================================================================

# services/import_service.py
"""
Centralized import service to eliminate duplicate file handling logic
"""
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool
from typing import Optional, List, Dict, Any, Callable
import pandas as pd
from pathlib import Path
import logging

# Import your existing ViewModels instead of non-existent transformers
from viewmodels.upload_viewmodel import UploadViewModel
from viewmodels.erp_database_viewmodel import ERPDatabaseViewModel
from models.data_models import TransactionData, BankStatement
from services.data_service import DataService

logger = logging.getLogger(__name__)

class ImportWorker(QRunnable):
    """Worker thread for file import operations using existing ViewModels"""
    
    def __init__(
        self,
        file_path: str,
        import_type: str,
        callback_success: Callable[[Any], None],
        callback_error: Callable[[str], None],
        template_type: str = None,
        upload_vm: Optional[UploadViewModel] = None,
        erp_vm: Optional[ERPDatabaseViewModel] = None,
    ):
        super().__init__()
        self.file_path = file_path
        self.import_type = import_type
        self.callback_success = callback_success
        self.callback_error = callback_error
        self.template_type = template_type
        self.upload_vm = upload_vm or UploadViewModel()
        self.erp_vm = erp_vm or ERPDatabaseViewModel()
            
    def run(self):
        try:
            if self.import_type == 'bank':
                result = self._import_bank_file()
            elif self.import_type == 'erp':
                result = self._import_erp_file()
            else:
                raise ValueError(f"Unknown import type: {self.import_type}")
                
            self.callback_success(result)
        except Exception as e:
            self.callback_error(str(e))
    
    def _import_bank_file(self) -> BankStatement:
        """Import bank file using existing UploadViewModel"""
        upload_vm = self.upload_vm
        
        # Get available templates
        templates = upload_vm.available_templates
        if not templates:
            raise ValueError("No bank templates available")
        
        # Use first available template if none specified, or find matching template
        if self.template_type:
            template = upload_vm.get_template_by_type(self.template_type)
            if not template:
                # Try common mappings for your existing templates
                template_mappings = {
                    'standard_uk_bank': 'lloyds',
                    'natwest_bank': 'rbs/natwest', 
                    'charity_bank': 'lloyds',
                    'lloyds': 'lloyds',
                    'rbs': 'rbs/natwest',
                    'natwest': 'rbs/natwest'
                }
                mapped_type = template_mappings.get(self.template_type.lower(), self.template_type.lower())
                template = upload_vm.get_template_by_type(mapped_type)
        else:
            # Use first available template as fallback
            template = templates[0] if templates else None
        
        if not template:
            raise ValueError(f"No suitable template found for type: {self.template_type}")
        
        # Set template and upload file
        upload_vm.selected_template = template
        
        if not upload_vm.upload_file(self.file_path):
            raise ValueError(upload_vm.error_message or "Failed to upload file")
        
        # Transform the statement
        if not upload_vm.transform_statement():
            raise ValueError(upload_vm.error_message or "Failed to transform statement")
        
        return upload_vm.transformed_statement
    
    def _import_erp_file(self) -> List[TransactionData]:
        """Import ERP file - this would integrate with your ERP data processing"""
       
        file_path = Path(self.file_path)
        
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(self.file_path)
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(self.file_path)
        else:
            raise ValueError(f"Unsupported ERP file format: {file_path.suffix}")
        
        # Convert DataFrame to TransactionData objects
        # This assumes your ERP data has certain columns - adjust as needed
        transactions = [
            TransactionData(
                date=pd.to_datetime(row.get('Date', row.get('date', ''))),
                description=str(row.get('Description', row.get('description', ''))),
                amount=float(row.get('Amount', row.get('amount', 0))),
                reference=str(row.get('Reference', row.get('Ref', row.get('reference', ''))))
            )
            for row in df.to_dict('records')
        ]
        
        return transactions

class ImportService(QObject):
    """Centralized service for all file import operations using existing architecture"""
    
    # Signals
    import_started = Signal(str)       # import_type
    import_completed = Signal(object)  # result data
    import_failed = Signal(str)        # error message
    
    def __init__(self, data_service: DataService):
        super().__init__()
        self.data_service = data_service
        self.thread_pool = QThreadPool()
        
        # Keep reference to ViewModels for template access
        self.upload_vm = UploadViewModel()
        self.erp_vm = ERPDatabaseViewModel()

        # Connect to existing ViewModel signals
        self._connect_viewmodel_signals()
    
    def _connect_viewmodel_signals(self):
        """Connect to existing ViewModel signals"""
        # Connect bank transformation signals
        if hasattr(self.upload_vm, 'transformation_completed'):
            self.upload_vm.transformation_completed.connect(self._on_bank_transformation_completed)
        if hasattr(self.upload_vm, 'transformation_failed'):
            self.upload_vm.transformation_failed.connect(self._on_transformation_failed)
            
        # Connect ERP signals
        if hasattr(self.erp_vm, 'data_loaded'):
            self.erp_vm.data_loaded.connect(self._on_erp_data_loaded)
    
    def import_bank_statement(self, parent: QWidget, template_type: str = None) -> bool:
        """Import bank statement file using a file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "Import Bank Statement",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if not file_path:
            return False

        return self.import_bank_statement_file(file_path, template_type)

    def import_bank_statement_file(self, file_path: str, template_type: str = None) -> bool:
        """Import a specific bank statement file"""    
        self.import_started.emit('bank')
        
        worker = ImportWorker(
            file_path, 
            'bank',
            self._on_bank_import_success,
            self._on_import_error,
            template_type,
            upload_vm=self.upload_vm
        )
        self.thread_pool.start(worker)
        return True
    
    def import_erp_data(self, parent: QWidget) -> bool:
        """Import ERP data file"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "Import ERP Data", 
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if not file_path:
            return False

        return self.import_erp_data_file(file_path)

    def import_erp_data_file(self, file_path: str) -> bool:
        """Import a specific ERP data file"""    
        self.import_started.emit('erp')
        
        worker = ImportWorker(
            file_path, 
            'erp',
            self._on_erp_import_success,
            self._on_import_error,
            erp_vm=self.erp_vm
        )
        self.thread_pool.start(worker)
        return True
    
    def import_training_data(self, parent: QWidget) -> bool:
        """Import training data for ML model"""
        file_path, file_filter = QFileDialog.getOpenFileName(
            parent,
            "Import Training Data",
            "",
            "JSON Files (*.json);;CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return False
            
        try:
            # Basic training data import - enhance based on your training data format
            if file_path.endswith('.json'):
                import json
                with open(file_path, 'r') as f:
                    training_data = json.load(f)
            elif file_path.endswith('.csv'):
                import pandas as pd
                df = pd.read_csv(file_path)
                training_data = df.to_dict('records')
            else:
                raise ValueError("Unsupported training data format")
            
            logger.info(f"Training data imported from: {file_path}")
            QMessageBox.information(parent, "Training Data", 
                                  f"Training data imported successfully!\n"
                                  f"Records: {len(training_data)}")
            return True
            
        except Exception as e:
            error_msg = f"Training data import failed: {str(e)}"
            self.import_failed.emit(error_msg)
            QMessageBox.critical(parent, "Training Data Error", error_msg)
            return False
    
    def get_available_bank_templates(self) -> List:
        """Get available bank templates from UploadViewModel"""
        return self.upload_vm.available_templates
    
    def get_template_by_type(self, template_type: str):
        """Get specific template by type"""
        return self.upload_vm.get_template_by_type(template_type)
    
    def _on_bank_import_success(self, statement: BankStatement):
        """Handle successful bank import"""
        self.data_service.set_bank_data(statement)
        self.import_completed.emit(statement)
        logger.info(f"Bank statement imported successfully: {len(statement.transactions)} transactions")
    
    def _on_erp_import_success(self, transactions: List[TransactionData]):
        """Handle successful ERP import"""
        self.data_service.set_erp_data(transactions)
        self.import_completed.emit(transactions)
        logger.info(f"ERP data imported successfully: {len(transactions)} transactions")
    
    def _on_import_error(self, error_message: str):
        """Handle import error"""
        self.import_failed.emit(error_message)
        logger.error(f"Import failed: {error_message}")

    # Additional signal handlers when using ViewModels directly
    def _on_bank_transformation_completed(self, statement, result_info):
        """Handle bank transformation completion from ViewModel"""
        self._on_bank_import_success(statement)
    
    def _on_transformation_failed(self, error_message: str):
        """Handle transformation failure from ViewModel"""
        self.import_failed.emit(error_message)
    
    def _on_erp_data_loaded(self, transactions):
        """Handle ERP data loading from ViewModel"""
        self._on_erp_import_success(transactions)



# ============================================================================
# Alternative: Enhanced ImportService that integrates more directly with your existing system
# ============================================================================

class EnhancedImportService(QObject):
    """Enhanced import service that uses your existing ViewModels directly"""
    
    import_started = Signal(str)
    import_completed = Signal(object)
    import_failed = Signal(str)
    
    def __init__(self, data_service: DataService, upload_viewmodel: UploadViewModel = None, 
                 erp_viewmodel: ERPDatabaseViewModel = None):
        super().__init__()
        self.data_service = data_service
        
        # Use provided ViewModels or create new ones
        self.upload_vm = upload_viewmodel or UploadViewModel()
        self.erp_vm = erp_viewmodel or ERPDatabaseViewModel()
        
        # Connect to existing ViewModel signals
        self._connect_viewmodel_signals()
    
    def _connect_viewmodel_signals(self):
        """Connect to existing ViewModel signals"""
        # Connect bank transformation signals
        if hasattr(self.upload_vm, 'transformation_completed'):
            self.upload_vm.transformation_completed.connect(self._on_bank_transformation_completed)
        if hasattr(self.upload_vm, 'transformation_failed'):
            self.upload_vm.transformation_failed.connect(self._on_transformation_failed)
            
        # Connect ERP signals
        if hasattr(self.erp_vm, 'data_loaded'):
            self.erp_vm.data_loaded.connect(self._on_erp_data_loaded)
    
    def import_bank_statement_with_dialog(self, parent: QWidget, account_type: str = None) -> bool:
        """Import bank statement using file dialog and existing UploadViewModel"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "Import Bank Statement",
            "",
            "Excel files (*.xlsx *.xls);;CSV files (*.csv);;All files (*.*)"
        )
        
        if not file_path:
            return False
        
        return self.import_bank_statement_file(file_path, account_type)
    
    def import_bank_statement_file(self, file_path: str, template_type: str = None) -> bool:
        """Import specific bank statement file"""
        try:
            self.import_started.emit('bank')
            
            # Auto-detect or use specified template
            if template_type:
                template = self.upload_vm.get_template_by_type(template_type)
                if not template:
                    # Try common mappings
                    mappings = {
                        'standard_uk_bank': 'lloyds',
                        'Natwest_bank': 'rbs/natwest',
                        'Charity_bank': 'lloyds'
                    }
                    mapped_type = mappings.get(template_type, template_type)
                    template = self.upload_vm.get_template_by_type(mapped_type)
                
                if template:
                    self.upload_vm.selected_template = template
            
            # Upload and transform using existing logic
            if not self.upload_vm.upload_file(file_path):
                raise ValueError(self.upload_vm.error_message or "Failed to upload file")
            
            if not self.upload_vm.transform_statement():
                raise ValueError(self.upload_vm.error_message or "Failed to transform statement")
            
            # Get the transformed statement
            statement = self.upload_vm.transformed_statement
            if statement:
                self.data_service.set_bank_data(statement)
                self.import_completed.emit(statement)
                return True
            else:
                raise ValueError("No statement data generated")
                
        except Exception as e:
            error_msg = f"Bank import failed: {str(e)}"
            self.import_failed.emit(error_msg)
            logger.error(error_msg)
            return False
    
    def import_erp_data_with_dialog(self, parent: QWidget) -> bool:
        """Import ERP data using file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "Import ERP Data",
            "",
            "CSV files (*.csv);;Excel files (*.xlsx *.xls);;All files (*.*)"
        )
        
        if not file_path:
            return False
        
        return self.import_erp_data_file(file_path)
    
    def import_erp_data_file(self, file_path: str) -> bool:
        """Import specific ERP data file"""
        try:
            self.import_started.emit('erp')
            
            # Use pandas for basic file reading (you can enhance this)
            file_path_obj = Path(file_path)
            
            if file_path_obj.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path_obj.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path_obj.suffix}")
            
            # Convert to TransactionData objects based on your ERP data structure
            transactions = self._convert_erp_dataframe_to_transactions(df)
            
            self.data_service.set_erp_data(transactions)
            self.import_completed.emit(transactions)
            return True
            
        except Exception as e:
            error_msg = f"ERP import failed: {str(e)}"
            self.import_failed.emit(error_msg)
            logger.error(error_msg)
            return False
    
    def _convert_erp_dataframe_to_transactions(self, df: pd.DataFrame) -> List[TransactionData]:
        """Convert ERP DataFrame to TransactionData objects"""
        transactions = []
        
        # Map common ERP column names - adjust based on your actual data structure
        column_mappings = {
            'date': ['Date', 'date', 'transaction_date', 'posting_date'],
            'description': ['Description', 'description', 'desc', 'details', 'narrative'],
            'amount': ['Amount', 'amount', 'value', 'total'],
            'reference': ['Reference', 'reference', 'ref', 'transaction_ref', 'id']
        }
        
        # Find actual column names in the DataFrame
        actual_columns = {}
        for field, possible_names in column_mappings.items():
            for name in possible_names:
                if name in df.columns:
                    actual_columns[field] = name
                    break
        
        if 'date' not in actual_columns or 'amount' not in actual_columns:
            # Try to infer from your sample data structure
            if 'Date' in df.columns and 'Amount' in df.columns:
                actual_columns['date'] = 'Date'
                actual_columns['amount'] = 'Amount'
                actual_columns['description'] = df.columns[1] if len(df.columns) > 1 else 'Description'
                actual_columns['reference'] = 'Reference' if 'Reference' in df.columns else None
            else:
                raise ValueError("Could not identify required columns (date, amount) in ERP data")
        
        def _build_transaction(row: Dict[str, Any]) -> Optional[TransactionData]:
            try:
                return TransactionData(
                    date=pd.to_datetime(row[actual_columns['date']]),
                    description=str(row.get(actual_columns.get('description', ''), '')),
                    amount=float(row[actual_columns['amount']]),
                    reference=str(row.get(actual_columns.get('reference', ''), ''))
                )
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid transaction row: {e}")
                return None
        
        transactions = list(filter(None, (_build_transaction(row) for row in df.to_dict('records'))))
        
        return transactions
    
    # Signal handlers for ViewModel integration
    def _on_bank_transformation_completed(self, statement, result_info):
        """Handle bank transformation completion from ViewModel"""
        self.data_service.set_bank_data(statement)
        self.import_completed.emit(statement)
    
    def _on_transformation_failed(self, error_message):
        """Handle transformation failure from ViewModel"""
        self.import_failed.emit(error_message)
    
    def _on_erp_data_loaded(self, transactions):
        """Handle ERP data loading from ViewModel"""
        self.data_service.set_erp_data(transactions)
        self.import_completed.emit(transactions)