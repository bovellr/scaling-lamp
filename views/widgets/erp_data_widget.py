# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
# views/widgets/erp_data_widget.py
"""
Widget for loading ERP data from database or file.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                            QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
                            QTabWidget, QFormLayout, QLineEdit, QDateEdit, QDateTimeEdit,  
                            QSpinBox, QDoubleSpinBox, QLabel, QTextEdit, QCheckBox, QHeaderView,
                            QProgressBar, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QDate, QDateTime, Signal
import pandas as pd
from datetime import datetime, date
import logging
from typing import Dict, Any
from pathlib import Path

from viewmodels.erp_database_viewmodel import ERPDatabaseViewModel
from models.data_models import TransactionData
from models.erp_file_processor import ERPFileProcessor
from views.dialogs.database_connection_dialog import DatabaseConnectionDialog
from views.dialogs.query_template_dialog import QueryTemplateDialog

logger = logging.getLogger(__name__)

class ERPDataWidget(QWidget):
    """Widget for loading ERP transaction data from database or files."""
    
    # Signals
    erp_data_loaded = Signal(object)  # Emits List[TransactionData]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewmodel = ERPDatabaseViewModel()
        self._setup_ui()
        self._bind_viewmodel()

        self._initialize_oracle_connection()
    
    def _initialize_oracle_connection(self):
        """NEW METHOD: Initialize Oracle connection from settings"""
        try:
            # Check if Oracle connection exists and select it
            oracle_connections = [
                conn for conn in self.viewmodel.available_connections 
                if 'oracle' in conn.name.lower()
            ]
            
            if oracle_connections:
                # Select the first Oracle connection
                oracle_conn = oracle_connections[0]
                
                # Find the connection in combo box and select it
                for i in range(self.connection_combo.count()):
                    if self.connection_combo.itemData(i) == oracle_conn:
                        self.connection_combo.setCurrentIndex(i)
                        break
                
                logger.info(f"Auto-selected Oracle connection: {oracle_conn.name}")
            
        except Exception as e:
            logger.warning(f"Could not auto-select Oracle connection: {e}")
    
    def get_loaded_transactions(self):
        """NEW METHOD: Get loaded transactions for integration with other widgets"""
        return self.viewmodel.erp_transactions
    
    def is_data_loaded(self):
        """NEW METHOD: Check if data is loaded"""
        return len(self.viewmodel.erp_transactions) > 0

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("ERP Transaction Data")
        title_label.setStyleSheet("QLabel { font-size: 14pt; font-weight: bold; }")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Data source tabs
        self.source_tabs = QTabWidget()
        
        # Database tab
        db_tab = self._create_database_tab()
        self.source_tabs.addTab(db_tab, "Database Query")
        
        # File upload tab
        file_tab = self._create_file_tab()
        self.source_tabs.addTab(file_tab, "File Upload")
        
        layout.addWidget(self.source_tabs)
        
        # Results section
        results_group = QGroupBox("ERP Transaction Data")
        results_layout = QVBoxLayout(results_group)
        
        # Results summary
        self.results_summary = QLabel("No data loaded")
        results_layout.addWidget(self.results_summary)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setObjectName("resultsTable")
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Date", "Description", "Amount", "Reference"])
        self.results_table.setMaximumHeight(200)
        results_layout.addWidget(self.results_table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.use_data_button = QPushButton("Use This Data for Reconciliation")
        self.export_button = QPushButton("Export Data")
        self.clear_button = QPushButton("Clear Data")
        
        self.use_data_button.clicked.connect(self._use_data_for_reconciliation)
        self.export_button.clicked.connect(self._export_data)
        self.clear_button.clicked.connect(self._clear_data)
        
        self.use_data_button.setEnabled(False)
        self.export_button.setEnabled(False)
        
        action_layout.addWidget(self.use_data_button)
        action_layout.addWidget(self.export_button)
        action_layout.addStretch()
        action_layout.addWidget(self.clear_button)
        
        results_layout.addLayout(action_layout)
        layout.addWidget(results_group)
    
    def _create_database_tab(self) -> QWidget:
        """Create database query tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Connection management
        conn_group = QGroupBox("Database Connection")
        conn_layout = QVBoxLayout(conn_group)
        
        conn_selection_layout = QHBoxLayout()
        conn_selection_layout.addWidget(QLabel("Connection:"))
        
        self.connection_combo = QComboBox()
        self.connection_combo.currentTextChanged.connect(self._on_connection_changed)
        conn_selection_layout.addWidget(self.connection_combo)
        
        self.new_connection_button = QPushButton("New")
        self.edit_connection_button = QPushButton("Edit")
        self.test_connection_button = QPushButton("Test")
        
        self.new_connection_button.clicked.connect(self._create_connection)
        self.edit_connection_button.clicked.connect(self._edit_connection)
        self.test_connection_button.clicked.connect(self._test_connection)
        
        conn_selection_layout.addWidget(self.new_connection_button)
        conn_selection_layout.addWidget(self.edit_connection_button)
        conn_selection_layout.addWidget(self.test_connection_button)
        
        conn_layout.addLayout(conn_selection_layout)
        
        # Connection status
        self.connection_status = QLabel("No connection selected")
        self.connection_status.setStyleSheet("QLabel { color: #666; padding: 5px; }")
        conn_layout.addWidget(self.connection_status)
        
        layout.addWidget(conn_group)
        
        # Query management
        query_group = QGroupBox("Query Template")
        query_layout = QVBoxLayout(query_group)
        
        query_selection_layout = QHBoxLayout()
        query_selection_layout.addWidget(QLabel("Template:"))
        
        self.query_combo = QComboBox()
        self.query_combo.currentTextChanged.connect(self._on_query_changed)
        query_selection_layout.addWidget(self.query_combo)
        
        self.new_query_button = QPushButton("New")
        self.edit_query_button = QPushButton("Edit")
        
        self.new_query_button.clicked.connect(self._create_query)
        self.edit_query_button.clicked.connect(self._edit_query)
        
        query_selection_layout.addWidget(self.new_query_button)
        query_selection_layout.addWidget(self.edit_query_button)
        
        query_layout.addLayout(query_selection_layout)
        layout.addWidget(query_group)
        
        # Query parameters
        self.params_group = QGroupBox("Query Parameters")
        self.params_layout = QFormLayout(self.params_group)
        self.params_group.setVisible(False)
        layout.addWidget(self.params_group)
        
        # Execute query
        execute_layout = QHBoxLayout()
        
        self.execute_button = QPushButton("Execute Query")
        self.execute_button.clicked.connect(self._execute_query)
        self.execute_button.setEnabled(False)
        
        self.query_progress = QProgressBar()
        self.query_progress.setVisible(False)
        
        execute_layout.addWidget(self.execute_button)
        execute_layout.addWidget(self.query_progress)
        execute_layout.addStretch()
        
        layout.addLayout(execute_layout)
        
        # Query status
        self.query_status = QLabel("")
        layout.addWidget(self.query_status)
        
        layout.addStretch()
        return tab
    
    def _create_file_tab(self) -> QWidget:
        """Create file upload tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File upload section
        upload_group = QGroupBox("Upload ERP File")
        upload_layout = QVBoxLayout(upload_group)
        
        file_layout = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        self.browse_file_button = QPushButton("Browse...")
        self.browse_file_button.clicked.connect(self._browse_erp_file)
        
        file_layout.addWidget(self.file_path_label)
        file_layout.addWidget(self.browse_file_button)
        upload_layout.addLayout(file_layout)
        
        # File processing options
        options_layout = QFormLayout()
        
        self.has_header_checkbox = QCheckBox()
        self.has_header_checkbox.setChecked(True)
        options_layout.addRow("File has headers:", self.has_header_checkbox)
        
        self.sheet_combo = QComboBox()
        self.sheet_combo.setVisible(False)
        options_layout.addRow("Excel sheet:", self.sheet_combo)
        
        upload_layout.addLayout(options_layout)
        
        # Column mapping
        mapping_group = QGroupBox("Column Mapping")
        mapping_layout = QFormLayout(mapping_group)
        
        self.date_column_combo = QComboBox()
        self.description_column_combo = QComboBox()
        self.amount_column_combo = QComboBox()
        self.reference_column_combo = QComboBox()
        
        mapping_layout.addRow("Date Column:", self.date_column_combo)
        mapping_layout.addRow("Description Column:", self.description_column_combo)
        mapping_layout.addRow("Amount Column:", self.amount_column_combo)
        mapping_layout.addRow("Reference Column:", self.reference_column_combo)
        
        upload_layout.addWidget(mapping_group)
        
        # Process file button
        self.process_file_button = QPushButton("Process File")
        self.process_file_button.clicked.connect(self._process_erp_file)
        self.process_file_button.setEnabled(False)
        upload_layout.addWidget(self.process_file_button)
        
        layout.addWidget(upload_group)
        layout.addStretch()
        return tab
    
    def _bind_viewmodel(self):
        """Bind ViewModel to UI elements."""
        self.viewmodel.bind_property_changed('available_connections', self._update_connections)
        self.viewmodel.bind_property_changed('available_queries', self._update_queries)
        self.viewmodel.bind_property_changed('selected_query', self._update_query_parameters)
        self.viewmodel.bind_property_changed('is_executing_query', self._update_execution_state)
        self.viewmodel.bind_property_changed('connection_test_result', self._update_connection_status)
        self.viewmodel.bind_property_changed('erp_transactions', self._update_results)
        self.viewmodel.bind_property_changed('error_message', self._update_error_message)
        
        # Initial update
        self._update_connections(self.viewmodel.available_connections)
        self._update_queries(self.viewmodel.available_queries)
    
    def _update_connections(self, connections):
        """Update connection combo box."""
        self.connection_combo.clear()
        self.connection_combo.addItem("Select connection...", None)
        
        for conn in connections:
            display_text = f"{conn.name} ({conn.connection_type})"
            self.connection_combo.addItem(display_text, conn)
    
    def _update_queries(self, queries):
        """Update query combo box."""
        self.query_combo.clear()
        self.query_combo.addItem("Select query template...", None)
        
        for query in queries:
            self.query_combo.addItem(f"{query.name} - {query.description[:50]}", query)
    
    def _update_query_parameters(self, query):
        """Update query parameters form."""
        # Clear existing parameters
        for i in reversed(range(self.params_layout.count())):
            self.params_layout.itemAt(i).widget().setParent(None)
        
        if not query or not query.parameters:
            self.params_group.setVisible(False)
            return
        
        self.params_group.setVisible(True)
        
        invalid_defaults = []

        # Add parameter controls
        for param in query.parameters:
            if param.data_type == 'date':
                control = QDateEdit()
                control.setDate(QDate.currentDate())
                control.setCalendarPopup(True)
                control.dateChanged.connect(
                    lambda date, name=param.name: self.viewmodel.update_parameter_command(
                        name, date.toString('yyyy-MM-dd')
                    )
                )
            elif param.data_type == 'datetime':
                control = QDateTimeEdit()
                control.setDateTime(QDateTime.currentDateTime())
                control.dateTimeChanged.connect(
                    lambda dt, name=param.name: self.viewmodel.update_parameter_command(
                        name, dt.toString('yyyy-MM-dd hh:mm:ss')
                    )
                )
            elif param.data_type == 'integer':
                control = QSpinBox()
                control.setRange(-999999999, 999999999)
                if param.default_value:
                    try:
                        control.setValue(int(param.default_value))
                    except ValueError:
                        logger.warning(
                            "Invalid default value '%s' for parameter '%s'", param.default_value, param.name
                        )
                        control.setToolTip(
                            f"Invalid default value '{param.default_value}' ignored"
                        )
                        invalid_defaults.append(param.name)
                control.valueChanged.connect(
                    lambda value, name=param.name: self.viewmodel.update_parameter_command(name, value)
                )
            elif param.data_type == 'decimal':
                control = QDoubleSpinBox()
                control.setRange(-999999999.99, 999999999.99)
                control.setDecimals(2)
                if param.default_value:
                    try:
                        control.setValue(float(param.default_value))
                    except ValueError:
                        logger.warning(
                            "Invalid default value '%s' for parameter '%s'", param.default_value, param.name
                        )
                        control.setToolTip(
                            f"Invalid default value '{param.default_value}' ignored"
                        )
                        invalid_defaults.append(param.name)
                control.valueChanged.connect(
                    lambda value, name=param.name: self.viewmodel.update_parameter_command(name, value)
                )
            else:  # string
                control = QLineEdit()
                if param.default_value:
                    control.setText(param.default_value)
                control.textChanged.connect(
                    lambda text, name=param.name: self.viewmodel.update_parameter_command(name, text)
                )
            
            # Create label with description
            label_text = f"{param.name}:"
            if param.description:
                label_text += f" ({param.description})"
            if param.is_required:
                label_text += " *"
            
            self.params_layout.addRow(label_text, control)
            
        if invalid_defaults:
            self.query_status.setText(
                "Invalid default value ignored for: " + ", ".join(invalid_defaults)
            )
            self.query_status.setStyleSheet("QLabel { color: orange; }")
        else:
            self.query_status.setText("")
            self.query_status.setStyleSheet("")

    def _update_execution_state(self, is_executing):
        """Update UI during query execution."""
        self.execute_button.setEnabled(not is_executing and self.viewmodel.can_execute_query)
        self.query_progress.setVisible(is_executing)
        
        if is_executing:
            self.query_progress.setRange(0, 0)  # Indeterminate
    
    def _update_connection_status(self, status):
        """Update connection status display."""
        self.connection_status.setText(status)
        
        if "success" in status.lower():
            self.connection_status.setStyleSheet("QLabel { color: green; padding: 5px; }")
        elif "fail" in status.lower():
            self.connection_status.setStyleSheet("QLabel { color: red; padding: 5px; }")
        else:
            self.connection_status.setStyleSheet("QLabel { color: #666; padding: 5px; }")
    
    def _update_results(self, transactions):
        """Update results display."""
        if not transactions:
            self.results_summary.setText("No data loaded")
            self.results_table.setRowCount(0)
            self.use_data_button.setEnabled(False)
            self.export_button.setEnabled(False)
            return
        
        # Update summary
        self.results_summary.setText(f"Loaded {len(transactions)} ERP transactions")
        
        # Update table (show first 100 rows)
        display_count = min(100, len(transactions))
        self.results_table.setRowCount(display_count)
        
        for row, transaction in enumerate(transactions[:display_count]):
            self.results_table.setItem(row, 0, QTableWidgetItem(transaction.date))
            self.results_table.setItem(row, 1, QTableWidgetItem(transaction.description))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"£{transaction.amount:.2f}"))
            self.results_table.setItem(row, 3, QTableWidgetItem(transaction.reference or ""))
        
        if len(transactions) > 100:
            self.results_summary.setText(
                f"Loaded {len(transactions)} ERP transactions (showing first 100)"
            )
        
        self.results_table.resizeColumnsToContents()
        
        # Enable action buttons
        self.use_data_button.setEnabled(True)
        self.export_button.setEnabled(True)
    
    def _update_error_message(self, error):
        """Update error message display."""
        if error:
            self.query_status.setText(error)
            self.query_status.setStyleSheet("QLabel { color: red; }")
        else:
            self.query_status.setStyleSheet("")
    
    # Event handlers
    def _on_connection_changed(self):
        """Handle connection selection change."""
        connection = self.connection_combo.currentData()
        self.viewmodel.selected_connection = connection
        self.execute_button.setEnabled(self.viewmodel.can_execute_query)
    
    def _on_query_changed(self):
        """Handle query selection change."""
        query = self.query_combo.currentData()
        self.viewmodel.selected_query = query
        self.execute_button.setEnabled(self.viewmodel.can_execute_query)
    
    def _create_connection(self):
        """Create new database connection."""
        dialog = DatabaseConnectionDialog(self)
        if dialog.exec():
            connection = dialog.connection
            if self.viewmodel.save_connection_command(connection):
                QMessageBox.information(self, "Success", f"Connection '{connection.name}' saved successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to save connection.")
    
    def _edit_connection(self):
        """Edit selected database connection."""
        connection = self.connection_combo.currentData()
        if not connection:
            QMessageBox.warning(self, "No Selection", "Please select a connection to edit.")
            return
        
        dialog = DatabaseConnectionDialog(self, connection)
        if dialog.exec():
            updated_connection = dialog.connection
            if self.viewmodel.save_connection_command(updated_connection):
                QMessageBox.information(self, "Success", "Connection updated successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to update connection.")
    
    def _test_connection(self):
        """Test selected database connection."""
        connection = self.connection_combo.currentData()
        if not connection:
            QMessageBox.warning(self, "No Selection", "Please select a connection to test.")
            return
        
        success = self.viewmodel.test_connection_command(connection)
        # Result will be shown via status update
    
    def _create_query(self):
        """Create new query template."""
        connections = self.viewmodel.available_connections
        dialog = QueryTemplateDialog(self, connections=connections)
        if dialog.exec():
            template = dialog.template
            if self.viewmodel.save_query_template_command(template):
                QMessageBox.information(self, "Success", f"Query template '{template.name}' saved successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to save query template.")
    
    def _edit_query(self):
        """Edit selected query template."""
        query = self.query_combo.currentData()
        if not query:
            QMessageBox.warning(self, "No Selection", "Please select a query template to edit.")
            return
        
        connections = self.viewmodel.available_connections
        dialog = QueryTemplateDialog(self, query, connections)
        if dialog.exec():
            updated_template = dialog.template
            if self.viewmodel.save_query_template_command(updated_template):
                QMessageBox.information(self, "Success", "Query template updated successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to update query template.")
    
    def _execute_query(self):
        """Execute selected query."""
        success = self.viewmodel.execute_query_command()
        # Results will be shown via data binding
    
    def _browse_erp_file(self):
        """Browse for ERP file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ERP Transaction File",
            "",
            "Supported Files (*.csv *.xlsx *.xls);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            self.file_path_label.setText(file_path)
            self._analyze_file_structure(file_path)
    
    def _analyze_file_structure(self, file_path):
        """Enhanced file structure analysis with auto-mapping."""
        try:
            # Use the enhanced processor
            processor = ERPFileProcessor()
            
            # Get comprehensive analysis
            analysis = processor._analyze_file_structure(file_path)
            
            if not analysis['success']:
                QMessageBox.warning(self, "File Error", f"Failed to analyze file: {analysis.get('error', 'Unknown error')}")
                return
            
            # For Excel files, populate sheet selector
            if analysis.get('metadata', {}).get('file_type') == 'excel':
                xl_file = pd.ExcelFile(file_path)
                self.sheet_combo.clear()
                self.sheet_combo.addItems(xl_file.sheet_names)
                self.sheet_combo.setVisible(True)
                
                # Select recommended sheet if available
                if analysis.get('sheet_name'):
                    self.sheet_combo.setCurrentText(analysis['sheet_name'])
            
            # Store analysis results for later use
            self.analysis_results = analysis
            
            # Update column combo boxes with detected columns
            columns = analysis.get('columns', [])
            
            for combo in [self.date_column_combo, self.description_column_combo,
                        self.amount_column_combo, self.reference_column_combo]:
                combo.clear()
                combo.addItem("Select column...", None)
                combo.addItems([str(col) for col in columns])
            
            # Apply enhanced auto-detected mappings
            mapping = analysis.get('mapping', {})
            self._apply_enhanced_mapping_to_ui(mapping)
            
            # Show confidence indicator
            confidence = analysis.get('confidence', 0)
            self._update_confidence_display(confidence)
            
            self.process_file_button.setEnabled(True)
            
            logger.info(f"File structure analyzed: {len(columns)} columns, {confidence:.1%} mapping confidence")
            
        except Exception as e:
            logger.error(f"File analysis error: {e}")
            QMessageBox.warning(self, "File Error", f"Failed to analyze file: {str(e)}")

    
    def _apply_enhanced_mapping_to_ui(self, mapping: Dict[str, Any]):
        """Apply enhanced auto-detected mapping to UI controls."""
        
        # Handle date mapping (simple single column)
        if mapping.get('date') is not None:
            self.date_column_combo.setCurrentIndex(mapping['date'] + 1)
        
        # Handle enhanced description mapping (single or combined)
        desc_config = mapping.get('description')
        if desc_config:
            self._update_description_mapping_ui(desc_config)
        
        # Handle enhanced amount mapping (single or combined)  
        amount_config = mapping.get('amount')
        if amount_config:
            self._update_amount_mapping_ui(amount_config)
        
        # Handle reference mapping (simple single column)
        if mapping.get('reference') is not None:
            self.reference_column_combo.setCurrentIndex(mapping['reference'] + 1)

    def _update_description_mapping_ui(self, desc_config: Dict[str, Any]):
        """Update the description mapping UI to show multi-column configuration."""
        
        if desc_config['type'] == 'combined':
            # Show primary and secondary columns
            primary_idx = desc_config['primary_column']
            secondary_cols = desc_config.get('secondary_columns', [])
            
            # Build display text
            columns = self.analysis_results.get('columns', []) if hasattr(self, 'analysis_results') else []
            
            primary_name = columns[primary_idx] if primary_idx < len(columns) else f"Column {primary_idx + 1}"
            
            secondary_names = []
            for sec_info in secondary_cols[:2]:  # Show max 2 in UI
                sec_idx = sec_info['index']
                sec_name = columns[sec_idx] if sec_idx < len(columns) else f"Column {sec_idx + 1}"
                secondary_names.append(sec_name)
            
            if secondary_names:
                combo_text = f"{primary_name} + {' + '.join(secondary_names)} (Combined)"
            else:
                combo_text = primary_name
            
            # Add special combined option to description combo
            self.description_column_combo.addItem(combo_text, desc_config)
            self.description_column_combo.setCurrentText(combo_text)
            
        elif desc_config['type'] == 'single':
            # Single column - normal handling
            column_idx = desc_config['column']
            self.description_column_combo.setCurrentIndex(column_idx + 1)

    def _update_amount_mapping_ui(self, amount_config: Dict[str, Any]):
        """Update the amount mapping UI to show multi-column configuration."""
        
        if amount_config['type'] == 'combined':
            # Show both credits and debits columns
            credits_idx = amount_config['credits_column']
            debits_idx = amount_config['debits_column']
            
            # Update the amount combo to show the combination
            columns = self.analysis_results.get('columns', []) if hasattr(self, 'analysis_results') else []
            credits_name = columns[credits_idx] if credits_idx < len(columns) else f"Column {credits_idx + 1}"
            debits_name = columns[debits_idx] if debits_idx < len(columns) else f"Column {debits_idx + 1}"
            
            combo_text = f"{credits_name} - {debits_name} (Combined)"
            
            # Add special combined option to amount combo
            self.amount_column_combo.addItem(combo_text, amount_config)
            self.amount_column_combo.setCurrentText(combo_text)
            
        elif amount_config['type'] == 'single':
            # Single column - normal handling
            column_idx = amount_config['column']
            self.amount_column_combo.setCurrentIndex(column_idx + 1)

    def _update_confidence_display(self, confidence: float):
        """Update confidence display in UI."""
        if not hasattr(self, 'confidence_label'):
            self.confidence_label = QLabel()
            # Add to your existing layout - insert after column mapping group
            try:
                if hasattr(self, 'mapping_group') and self.mapping_group.layout():
                    self.mapping_group.layout().addRow("Mapping Confidence:", self.confidence_label)
            except:
                pass  # If layout addition fails, label will exist but not be visible
        
        if confidence > 0.7:
            confidence_color = "green"
            confidence_text = "High"
        elif confidence > 0.4:
            confidence_color = "orange" 
            confidence_text = "Medium"
        else:
            confidence_color = "red"
            confidence_text = "Low"
        
        self.confidence_label.setText(f"{confidence_text} ({confidence:.1%})")
        self.confidence_label.setStyleSheet(f"color: {confidence_color}; font-weight: bold;")


    def _process_erp_file(self):
        """Process the uploaded ERP file with enhanced auto-mapping."""
        try:
            file_path = self.file_path_label.text()
            if not file_path or file_path == "No file selected":
                QMessageBox.warning(self, "No File", "Please select a file first.")
                return
            
            # Get sheet name for Excel files
            sheet_name = None
            if self.sheet_combo.isVisible() and self.sheet_combo.currentText():
                sheet_name = self.sheet_combo.currentText()
            
            # Use enhanced processor
            processor = ERPFileProcessor()
            
            # Process file with enhanced auto-mapping
            result = processor.analyze_and_process_file(file_path, sheet_name)
            
            if not result['success']:
                QMessageBox.critical(self, "Processing Error", 
                                f"Failed to process file: {result.get('message', 'Unknown error')}")
                return
            
            # Get processed and cleaned data
            processed_df = result['data']
            analysis = result['analysis']
            
            if processed_df.empty:
                QMessageBox.warning(self, "No Data", 
                                "No valid transaction data found in file after cleaning.")
                return
            
            # Convert to TransactionData objects
            transactions = []
            for _, row in processed_df.iterrows():
                try:
                    transaction = TransactionData(
                        date=row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else '',
                        description=str(row.get('Description', '')),  # Now potentially combined
                        amount=float(row.get('Amount', 0)),            # Now potentially combined
                        reference=str(row.get('Reference', '')) if row.get('Reference') else None
                    )
                    transactions.append(transaction)
                except Exception as e:
                    logger.warning(f"Skipping invalid transaction row: {e}")
                    continue
            
            # Update ViewModel
            self.viewmodel._erp_transactions = transactions
            self.viewmodel.notify_property_changed('erp_transactions', transactions)
            
            # Enhanced success message with mapping details
            self._show_enhanced_success_message(transactions, analysis, file_path)
            
            logger.info(f"Enhanced ERP file processed: {len(transactions)} transactions loaded")
            
        except Exception as e:
            logger.error(f"Enhanced ERP file processing error: {e}")
            QMessageBox.critical(self, "Processing Error", f"Failed to process file: {str(e)}")

    def _show_enhanced_success_message(self, transactions, analysis, file_path):
        """Show enhanced success message with detailed mapping information."""
        confidence = analysis.get('confidence', 0)
        mapping = analysis.get('mapping', {})
        
        # Build detailed mapping information
        mapping_details = []
        
        # Amount mapping details
        amount_config = mapping.get('amount')
        if isinstance(amount_config, dict):
            if amount_config['type'] == 'combined':
                credits_name = amount_config.get('credits_name', 'Credits')
                debits_name = amount_config.get('debits_name', 'Debits')
                mapping_details.append(f"• Amount: {credits_name} - {debits_name} (Combined)")
            elif amount_config['type'] == 'single':
                amount_name = amount_config.get('column_name', 'Amount')
                method = amount_config.get('method', 'direct')
                method_text = " (negated)" if method == 'negate' else ""
                mapping_details.append(f"• Amount: {amount_name}{method_text}")
        
        # Description mapping details
        desc_config = mapping.get('description')
        if isinstance(desc_config, dict):
            if desc_config['type'] == 'combined':
                primary_col = analysis['columns'][desc_config['primary_column']]
                secondary_cols = desc_config.get('secondary_columns', [])
                sec_names = [sec['column_name'] for sec in secondary_cols[:2]]
                if sec_names:
                    mapping_details.append(f"• Description: {primary_col} + {' + '.join(sec_names)}")
                else:
                    mapping_details.append(f"• Description: {primary_col}")
            elif desc_config['type'] == 'single':
                desc_col = analysis['columns'][desc_config['column']]
                mapping_details.append(f"• Description: {desc_col}")
        
        # Date mapping
        if mapping.get('date') is not None:
            date_col = analysis['columns'][mapping['date']]
            mapping_details.append(f"• Date: {date_col}")
        
        # Reference mapping
        if mapping.get('reference') is not None:
            ref_col = analysis['columns'][mapping['reference']]
            mapping_details.append(f"• Reference: {ref_col}")
        
        mapping_text = "\n".join(mapping_details) if mapping_details else "Basic column mapping applied"
        
        # Show comprehensive success message
        QMessageBox.information(
            self, "Enhanced Processing Success", 
            f"ERP file processed successfully!\n\n"
            f"File: {Path(file_path).name}\n"
            f"Transactions loaded: {len(transactions)}\n"
            f"Mapping confidence: {confidence:.1%}\n"
            f"Data cleaned and validated\n\n"
            f"Column Mapping Applied:\n{mapping_text}\n\n"
            f"Data is ready for reconciliation!"
        )

    
    def _use_data_for_reconciliation(self):
        """Use loaded data for reconciliation."""
        if self.viewmodel.erp_transactions:
            self.erp_data_loaded.emit(self.viewmodel.erp_transactions)
            QMessageBox.information(self, "Data Ready", "ERP data is ready for reconciliation!")
    
    def _export_data(self):
        """Export loaded data to file."""
        if not self.viewmodel.erp_transactions:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export ERP Data",
            "erp_transactions.csv",
            "CSV Files (*.csv);;Excel Files (*.xlsx)"
        )
        
        if file_path:
            try:
                # Convert to DataFrame
                data = []
                for txn in self.viewmodel.erp_transactions:
                    data.append({
                        'date': txn.date,
                        'description': txn.description,
                        'amount': txn.amount,
                        'reference': txn.reference or ''
                    })
                
                df = pd.DataFrame(data)
                
                if file_path.endswith('.csv'):
                    df.to_csv(file_path, index=False)
                else:
                    df.to_excel(file_path, index=False)
                
                QMessageBox.information(self, "Export Complete", f"Data exported to {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
    
    def _clear_data(self):
        """Clear loaded data."""
        self.viewmodel._erp_transactions = []
        self.viewmodel.notify_property_changed('erp_transactions', [])
        self.viewmodel._query_results = pd.DataFrame()
        self.viewmodel.notify_property_changed('query_results', pd.DataFrame())
