# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
# views/dialogs/query_template_dialog.py
"""
Dialog for creating/editing ERP query templates.
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
                            QLineEdit, QTextEdit, QComboBox, QPushButton,
                            QTableWidget, QTableWidgetItem, QGroupBox,
                            QTabWidget, QWidget, QMessageBox, QCheckBox,
                            QHeaderView, QAbstractItemView)
from PySide6.QtCore import Qt
from typing import List, Optional
import logging

from models.database_models import ERPQueryTemplate, QueryParameter

logger = logging.getLogger(__name__)

class QueryTemplateDialog(QDialog):
    """Dialog for creating/editing query templates."""
    
    def __init__(self, parent=None, template: ERPQueryTemplate = None, connections=None):
        super().__init__(parent)
        self.template = template
        self.connections = connections or []
        self.is_editing = template is not None
        
        self.setWindowTitle("Edit Query Template" if self.is_editing else "New Query Template")
        self.setModal(True)
        self.resize(700, 600)
        
        self._setup_ui()
        if self.is_editing:
            self._populate_fields()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Tabs
        tabs = QTabWidget()
        
        # Basic Info Tab
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)
        
        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        
        self.connection_combo = QComboBox()
        for conn in self.connections:
            self.connection_combo.addItem(f"{conn.name} ({conn.connection_type})", conn.name)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(['transactions', 'accounts', 'vendors', 'customers', 'other'])
        
        self.is_active_checkbox = QCheckBox()
        self.is_active_checkbox.setChecked(True)
        
        basic_layout.addRow("Template Name:", self.name_edit)
        basic_layout.addRow("Description:", self.description_edit)
        basic_layout.addRow("Database Connection:", self.connection_combo)
        basic_layout.addRow("Category:", self.category_combo)
        basic_layout.addRow("Active:", self.is_active_checkbox)
        
        tabs.addTab(basic_tab, "Basic Info")
        
        # SQL Query Tab
        sql_tab = QWidget()
        sql_layout = QVBoxLayout(sql_tab)
        
        sql_layout.addWidget(QLabel("SQL Query:"))
        self.sql_edit = QTextEdit()
        self.sql_edit.setPlaceholderText(
            "SELECT \n"
            "    transaction_date as date,\n"
            "    description,\n"
            "    amount,\n"
            "    reference_number as reference\n"
            "FROM transactions \n"
            "WHERE account_id = :account_id\n"
            "    AND transaction_date BETWEEN :start_date AND :end_date\n"
            "ORDER BY transaction_date"
        )
        
        # Use monospace font for SQL
        font = self.sql_edit.font()
        font.setFamily("Consolas, Monaco, 'Courier New', monospace")
        font.setPointSize(10)
        self.sql_edit.setFont(font)
        
        sql_layout.addWidget(self.sql_edit)
        
        # Expected columns
        sql_layout.addWidget(QLabel("Expected Result Columns (comma-separated):"))
        self.expected_columns_edit = QLineEdit()
        self.expected_columns_edit.setPlaceholderText("date, description, amount, reference")
        sql_layout.addWidget(self.expected_columns_edit)
        
        # SQL validation button
        validate_button = QPushButton("✓ Validate SQL")
        validate_button.clicked.connect(self._validate_sql)
        sql_layout.addWidget(validate_button)
        
        tabs.addTab(sql_tab, "SQL Query")
        
        # Parameters Tab
        params_tab = QWidget()
        params_layout = QVBoxLayout(params_tab)
        
        # Parameter management buttons
        param_buttons = QHBoxLayout()
        self.add_param_button = QPushButton("Add Parameter")
        self.remove_param_button = QPushButton("Remove Parameter")
        self.add_param_button.clicked.connect(self._add_parameter)
        self.remove_param_button.clicked.connect(self._remove_parameter)
        
        param_buttons.addWidget(self.add_param_button)
        param_buttons.addWidget(self.remove_param_button)
        param_buttons.addStretch()
        
        params_layout.addLayout(param_buttons)
        
        # Parameters table
        self.params_table = QTableWidget()
        self.params_table.setColumnCount(5)
        self.params_table.setHorizontalHeaderLabels([
            "Name", "Type", "Description", "Default Value", "Required"
        ])
        
        # Configure table
        self.params_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header = self.params_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Description column
        
        params_layout.addWidget(self.params_table)
        
        # Parameter help
        param_help = QLabel(
            "Use parameters in SQL with colon prefix (e.g., :account_id, :start_date)\n"
            "Common types: string, integer, decimal, date, datetime"
        )
        param_help.setStyleSheet("QLabel { color: #666; font-size: 9pt; padding: 10px; }")
        params_layout.addWidget(param_help)
        
        tabs.addTab(params_tab, "Parameters")
        
        layout.addWidget(tabs)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Test Template")
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        self.test_button.clicked.connect(self._test_template)
        self.save_button.clicked.connect(self._save_template)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.test_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def _populate_fields(self):
        """Populate fields with existing template data."""
        if not self.template:
            return
        
        self.name_edit.setText(self.template.name)
        self.description_edit.setPlainText(self.template.description)
        self.sql_edit.setPlainText(self.template.sql_query)
        self.expected_columns_edit.setText(", ".join(self.template.expected_columns))
        self.category_combo.setCurrentText(self.template.category)
        self.is_active_checkbox.setChecked(self.template.is_active)
        
        # Set connection
        for i in range(self.connection_combo.count()):
            if self.connection_combo.itemData(i) == self.template.connection_name:
                self.connection_combo.setCurrentIndex(i)
                break
        
        # Populate parameters table
        self._populate_parameters_table()
    
    def _populate_parameters_table(self):
        """Populate parameters table with existing parameters."""
        if not self.template:
            return
        
        self.params_table.setRowCount(len(self.template.parameters))
        
        for row, param in enumerate(self.template.parameters):
            self.params_table.setItem(row, 0, QTableWidgetItem(param.name))
            
            # Type combo
            type_combo = QComboBox()
            type_combo.addItems(['string', 'integer', 'decimal', 'date', 'datetime'])
            type_combo.setCurrentText(param.data_type)
            self.params_table.setCellWidget(row, 1, type_combo)
            
            self.params_table.setItem(row, 2, QTableWidgetItem(param.description))
            self.params_table.setItem(row, 3, QTableWidgetItem(param.default_value or ""))
            
            # Required checkbox
            required_checkbox = QCheckBox()
            required_checkbox.setChecked(param.is_required)
            self.params_table.setCellWidget(row, 4, required_checkbox)
    
    def _add_parameter(self):
        """Add new parameter row."""
        row = self.params_table.rowCount()
        self.params_table.insertRow(row)
        
        # Set default values
        self.params_table.setItem(row, 0, QTableWidgetItem("param_name"))
        
        type_combo = QComboBox()
        type_combo.addItems(['string', 'integer', 'decimal', 'date', 'datetime'])
        self.params_table.setCellWidget(row, 1, type_combo)
        
        self.params_table.setItem(row, 2, QTableWidgetItem("Parameter description"))
        self.params_table.setItem(row, 3, QTableWidgetItem(""))
        
        required_checkbox = QCheckBox()
        required_checkbox.setChecked(True)
        self.params_table.setCellWidget(row, 4, required_checkbox)
    
    def _remove_parameter(self):
        """Remove selected parameter row."""
        current_row = self.params_table.currentRow()
        if current_row >= 0:
            self.params_table.removeRow(current_row)
    
    def _validate_sql(self):
        """Validate SQL query syntax."""
        try:
            sql = self.sql_edit.toPlainText().strip()
            if not sql:
                QMessageBox.warning(self, "Validation", "Please enter a SQL query.")
                return
            
            # Create temporary template for validation
            parameters = self._extract_parameters_from_table()
            temp_template = ERPQueryTemplate(
                name="temp",
                description="temp",
                sql_query=sql,
                parameters=parameters
            )
            
            is_valid, errors = temp_template.validate_query()
            
            if is_valid:
                QMessageBox.information(self, "Validation", "SQL query validation passed!")
            else:
                error_msg = "SQL query validation failed:\n\n" + "\n".join(errors)
                QMessageBox.warning(self, "Validation", error_msg)
                
        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Validation failed: {str(e)}")
    
    def _extract_parameters_from_table(self) -> List[QueryParameter]:
        """Extract parameters from table."""
        parameters = []
        
        for row in range(self.params_table.rowCount()):
            try:
                name_item = self.params_table.item(row, 0)
                desc_item = self.params_table.item(row, 2)
                default_item = self.params_table.item(row, 3)
                
                if not name_item or not name_item.text().strip():
                    continue
                
                type_combo = self.params_table.cellWidget(row, 1)
                required_checkbox = self.params_table.cellWidget(row, 4)
                
                parameter = QueryParameter(
                    name=name_item.text().strip(),
                    data_type=type_combo.currentText() if type_combo else 'string',
                    description=desc_item.text().strip() if desc_item else "",
                    default_value=default_item.text().strip() if default_item and default_item.text().strip() else None,
                    is_required=required_checkbox.isChecked() if required_checkbox else True
                )
                
                parameters.append(parameter)
                
            except Exception as e:
                logger.warning(f"Error extracting parameter from row {row}: {e}")
                continue
        
        return parameters
    
    def _test_template(self):
        """Test the query template."""
        try:
            # Create template from form data
            template = self._create_template_from_form()
            if not template:
                return
            
            # For now, just show template info - could be enhanced with actual execution
            info = f"""
Template: {template.name}
Connection: {template.connection_name}
Parameters: {len(template.parameters)}
Expected Columns: {len(template.expected_columns)}

SQL Query Preview:
{template.sql_query[:200]}{'...' if len(template.sql_query) > 200 else ''}

Template structure is valid!

Note: To fully test, save the template and execute it with sample parameters.
            """.strip()
            
            QMessageBox.information(self, "Template Test", info)
            
        except Exception as e:
            QMessageBox.critical(self, "Test Failed", f"Template test failed: {str(e)}")
    
    def _create_template_from_form(self) -> Optional[ERPQueryTemplate]:
        """Create template object from form data."""
        try:
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Validation", "Template name is required.")
                return None
            
            sql = self.sql_edit.toPlainText().strip()
            if not sql:
                QMessageBox.warning(self, "Validation", "SQL query is required.")
                return None
            
            connection_name = self.connection_combo.currentData()
            if not connection_name:
                QMessageBox.warning(self, "Validation", "Database connection is required.")
                return None
            
            # Extract parameters
            parameters = self._extract_parameters_from_table()
            
            # Extract expected columns
            expected_columns = []
            columns_text = self.expected_columns_edit.text().strip()
            if columns_text:
                expected_columns = [col.strip() for col in columns_text.split(',') if col.strip()]
            
            template = ERPQueryTemplate(
                name=name,
                description=self.description_edit.toPlainText().strip(),
                sql_query=sql,
                parameters=parameters,
                connection_name=connection_name,
                expected_columns=expected_columns,
                category=self.category_combo.currentText(),
                is_active=self.is_active_checkbox.isChecked()
            )
            
            return template
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create template: {str(e)}")
            return None
    
    def _save_template(self):
        """Save the query template."""
        template = self._create_template_from_form()
        if template:
            self.template = template
            self.accept()
