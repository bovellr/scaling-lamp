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

from viewmodels.erp_database_viewmodel import ERPDatabaseViewModel
from models.data_models import TransactionData
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
        layout.addWidget(header_layout)
        
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
        """Analyze file structure and populate column mappings."""
        try:
            # Read file to get column names
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, nrows=0)  # Just headers
            else:
                df = pd.read_excel(file_path, nrows=0)
                
                # For Excel files, also get sheet names
                xl_file = pd.ExcelFile(file_path)
                self.sheet_combo.clear()
                self.sheet_combo.addItems(xl_file.sheet_names)
                self.sheet_combo.setVisible(True)
            
            # Update column combo boxes
            columns = df.columns.tolist()
            
            for combo in [self.date_column_combo, self.description_column_combo,
                         self.amount_column_combo, self.reference_column_combo]:
                combo.clear()
                combo.addItem("Select column...", None)
                combo.addItems(columns)
            
            # Try to auto-detect column mappings
            self._auto_detect_columns(columns)
            
            self.process_file_button.setEnabled(True)
            
        except Exception as e:
            QMessageBox.warning(self, "File Error", f"Failed to analyze file: {str(e)}")
    
    def _auto_detect_columns(self, columns):
        """Auto-detect column mappings based on column names."""
        column_patterns = {
            'date': ['date', 'transaction_date', 'posting_date', 'trans_date'],
            'description': ['description', 'narrative', 'details', 'memo'],
            'amount': ['amount', 'value', 'transaction_amount'],
            'reference': ['reference', 'ref', 'transaction_ref', 'doc_number', 'cheque_ref']
        }
        
        combos = {
            'date': self.date_column_combo,
            'description': self.description_column_combo,
            'amount': self.amount_column_combo,
            'reference': self.reference_column_combo
        }
        
        for field, patterns in column_patterns.items():
            combo = combos[field]
            for pattern in patterns:
                for col in columns:
                    if pattern.lower() in col.lower():
                        combo.setCurrentText(col)
                        break
                if combo.currentText() != "Select column...":
                    break
    
    def _process_erp_file(self):
        """Process the uploaded ERP file."""
        try:
            file_path = self.file_path_label.text()
            if not file_path or file_path == "No file selected":
                QMessageBox.warning(self, "No File", "Please select a file first.")
                return
            
            # Get column mappings
            date_col = self.date_column_combo.currentText()
            desc_col = self.description_column_combo.currentText()
            amount_col = self.amount_column_combo.currentText()
            ref_col = self.reference_column_combo.currentText()
            
            if date_col == "Select column..." or desc_col == "Select column..." or amount_col == "Select column...":
                QMessageBox.warning(self, "Missing Mapping", "Please map the required columns (Date, Description, Amount).")
                return
            
            # Read file
            read_kwargs = {}
            if self.has_header_checkbox.isChecked():
                read_kwargs['header'] = 0
            else:
                read_kwargs['header'] = None
            
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, **read_kwargs)
            else:
                sheet_name = self.sheet_combo.currentText() if self.sheet_combo.isVisible() else 0
                df = pd.read_excel(file_path, sheet_name=sheet_name, **read_kwargs)
            
            # Convert to TransactionData objects
            transactions = []
            for _, row in df.iterrows():
                try:
                    transaction = TransactionData(
                        date=str(row[date_col]),
                        description=str(row[desc_col]),
                        amount=float(row[amount_col]),
                        reference=str(row[ref_col]) if ref_col != "Select column..." and pd.notna(row[ref_col]) else None
                    )
                    transactions.append(transaction)
                except Exception as e:
                    continue  # Skip invalid rows
            
            # Update ViewModel
            self.viewmodel._erp_transactions = transactions
            self.viewmodel.notify_property_changed('erp_transactions', transactions)
            
            QMessageBox.information(self, "Success", f"Successfully loaded {len(transactions)} transactions from file.")
            
        except Exception as e:
            QMessageBox.critical(self, "Processing Error", f"Failed to process file: {str(e)}")
    
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
