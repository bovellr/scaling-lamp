# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# VIEWS - ERP Database Dialogs and Widgets
# ================================

# views/dialogs/database_connection_dialog.py
"""
Dialog for configuring ERP database connections.
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLineEdit, QSpinBox, QComboBox, QPushButton, 
                            QTextEdit, QLabel, QGroupBox, QCheckBox,
                            QTabWidget, QWidget, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from models.database_models import DatabaseConnection
from viewmodels.erp_database_viewmodel import ERPDatabaseViewModel

class DatabaseConnectionDialog(QDialog):
    """Dialog for creating/editing database connections."""
    
    def __init__(self, parent=None, connection: DatabaseConnection = None):
        super().__init__(parent)
        self.connection = connection
        self.is_editing = connection is not None
        
        self.setWindowTitle("Edit Database Connection" if self.is_editing else "New Database Connection")
        self.setModal(True)
        self.resize(500, 400)
        
        self._setup_ui()
        if self.is_editing:
            self._populate_fields()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Tabs for organized input
        tabs = QTabWidget()
        
        # Basic Connection Tab
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Production ERP")
        
        self.connection_type_combo = QComboBox()
        self.connection_type_combo.addItems(['oracle', 'sqlserver', 'postgresql', 'mysql'])
        self.connection_type_combo.currentTextChanged.connect(self._on_connection_type_changed)
        
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("e.g., erp-server.company.com")
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(1521)  # Oracle default
        
        self.database_edit = QLineEdit()
        self.database_edit.setPlaceholderText("Database name or SID")
        
        self.service_name_edit = QLineEdit()
        self.service_name_edit.setPlaceholderText("Oracle service name (optional)")
        
        self.schema_edit = QLineEdit()
        self.schema_edit.setPlaceholderText("Default schema (optional)")
        
        basic_layout.addRow("Connection Name:", self.name_edit)
        basic_layout.addRow("Database Type:", self.connection_type_combo)
        basic_layout.addRow("Host:", self.host_edit)
        basic_layout.addRow("Port:", self.port_spin)
        basic_layout.addRow("Database/SID:", self.database_edit)
        basic_layout.addRow("Service Name:", self.service_name_edit)
        basic_layout.addRow("Schema:", self.schema_edit)
        
        tabs.addTab(basic_tab, "Connection")
        
        # Authentication Tab
        auth_tab = QWidget()
        auth_layout = QFormLayout(auth_tab)
        
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        auth_layout.addRow("Username:", self.username_edit)
        auth_layout.addRow("Password:", self.password_edit)
        
        # Security note
        security_note = QLabel(
            "Passwords are encrypted and stored securely.\n"
            "Connection details are saved locally only."
        )
        security_note.setStyleSheet("QLabel { color: #666; font-size: 9pt; padding: 10px; }")
        auth_layout.addRow(security_note)
        
        tabs.addTab(auth_tab, "Authentication")
        
        # Advanced Tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # Custom connection string
        conn_str_group = QGroupBox("Custom Connection String")
        conn_str_layout = QVBoxLayout(conn_str_group)
        
        conn_str_layout.addWidget(QLabel("Override automatic connection string (advanced users):"))
        self.connection_string_edit = QTextEdit()
        self.connection_string_edit.setMaximumHeight(80)
        self.connection_string_edit.setPlaceholderText(
            "e.g., oracle+cx_oracle://user:pass@host:port/?service_name=service"
        )
        conn_str_layout.addWidget(self.connection_string_edit)
        
        advanced_layout.addWidget(conn_str_group)
        
        # Connection options
        options_group = QGroupBox("Options")
        options_layout = QFormLayout(options_group)
        
        self.is_active_checkbox = QCheckBox()
        self.is_active_checkbox.setChecked(True)
        
        options_layout.addRow("Active:", self.is_active_checkbox)
        advanced_layout.addWidget(options_group)
        
        advanced_layout.addStretch()
        tabs.addTab(advanced_tab, "Advanced")
        
        layout.addWidget(tabs)
        
        # Test connection section
        test_group = QGroupBox("Connection Test")
        test_layout = QVBoxLayout(test_group)
        
        test_button_layout = QHBoxLayout()
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self._test_connection)
        test_button_layout.addWidget(self.test_button)
        test_button_layout.addStretch()
        
        self.test_result_label = QLabel("")
        self.test_result_label.setWordWrap(True)
        
        test_layout.addLayout(test_button_layout)
        test_layout.addWidget(self.test_result_label)
        
        layout.addWidget(test_group)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        self.save_button.clicked.connect(self._save_connection)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def _populate_fields(self):
        """Populate fields with existing connection data."""
        if not self.connection:
            return
        
        self.name_edit.setText(self.connection.name)
        self.connection_type_combo.setCurrentText(self.connection.connection_type)
        self.host_edit.setText(self.connection.host)
        self.port_spin.setValue(self.connection.port)
        self.database_edit.setText(self.connection.database)
        self.username_edit.setText(self.connection.username)
        # Don't populate password for security
        
        if self.connection.service_name:
            self.service_name_edit.setText(self.connection.service_name)
        if self.connection.schema:
            self.schema_edit.setText(self.connection.schema)
        if self.connection.connection_string:
            self.connection_string_edit.setPlainText(self.connection.connection_string)
        
        self.is_active_checkbox.setChecked(self.connection.is_active)
    
    def _on_connection_type_changed(self, connection_type: str):
        """Update default port when connection type changes."""
        default_ports = {
            'oracle': 1521,
            'sqlserver': 1433,
            'postgresql': 5432,
            'mysql': 3306
        }
        
        self.port_spin.setValue(default_ports.get(connection_type, 1521))
        
        # Show/hide Oracle-specific fields
        oracle_visible = (connection_type == 'oracle')
        self.service_name_edit.setVisible(oracle_visible)
    
    def _test_connection(self):
        """Test the database connection."""
        try:
            # Create temporary connection from current form data
            temp_connection = DatabaseConnection(
                name="temp_test",
                connection_type=self.connection_type_combo.currentText(),
                host=self.host_edit.text().strip(),
                port=self.port_spin.value(),
                database=self.database_edit.text().strip(),
                username=self.username_edit.text().strip(),
                password=self.password_edit.text(),
                service_name=self.service_name_edit.text().strip() or None,
                schema=self.schema_edit.text().strip() or None,
                connection_string=self.connection_string_edit.toPlainText().strip() or None
            )
            
            # Validate required fields
            if not all([temp_connection.host, temp_connection.database, temp_connection.username]):
                self.test_result_label.setText("Please fill in required fields (host, database, username)")
                self.test_result_label.setStyleSheet("QLabel { color: red; }")
                return
            
            # Test connection in separate thread
            self.test_button.setEnabled(False)
            self.test_button.setText("Testing...")
            self.test_result_label.setText("Testing connection...")
            self.test_result_label.setStyleSheet("QLabel { color: blue; }")
            
            # Create test thread
            self.test_thread = ConnectionTestThread(temp_connection)
            self.test_thread.test_complete.connect(self._on_test_complete)
            self.test_thread.start()
            
        except Exception as e:
            self._on_test_complete(False, f"Test setup failed: {str(e)}")
    
    def _on_test_complete(self, success: bool, message: str):
        """Handle connection test completion."""
        self.test_button.setEnabled(True)
        self.test_button.setText("Test Connection")
        
        if success:
            self.test_result_label.setText(message)
            self.test_result_label.setStyleSheet("QLabel { color: green; }")
        else:
            self.test_result_label.setText(message)
            self.test_result_label.setStyleSheet("QLabel { color: red; }")
    
    def _save_connection(self):
        """Save the connection configuration."""
        try:
            # Validate inputs
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Validation Error", "Connection name is required.")
                return
            
            host = self.host_edit.text().strip()
            database = self.database_edit.text().strip()
            username = self.username_edit.text().strip()
            
            if not all([host, database, username]):
                QMessageBox.warning(self, "Validation Error", "Host, database, and username are required.")
                return
            
            # Create connection object
            connection = DatabaseConnection(
                name=name,
                connection_type=self.connection_type_combo.currentText(),
                host=host,
                port=self.port_spin.value(),
                database=database,
                username=username,
                password=self.password_edit.text(),
                service_name=self.service_name_edit.text().strip() or None,
                schema=self.schema_edit.text().strip() or None,
                connection_string=self.connection_string_edit.toPlainText().strip() or None,
                is_active=self.is_active_checkbox.isChecked()
            )
            
            # Store connection for retrieval
            self.connection = connection
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create connection: {str(e)}")

class ConnectionTestThread(QThread):
    """Thread for testing database connections without blocking UI."""
    
    test_complete = Signal(bool, str)  # success, message
    
    def __init__(self, connection: DatabaseConnection):
        super().__init__()
        self.connection = connection
    
    def run(self):
        """Test the connection in background thread."""
        try:
            from models.erp_database_service import ERPDatabaseService
            
            service = ERPDatabaseService()
            service.add_connection(self.connection)
            success, message = service.test_connection(self.connection.name)
            
            self.test_complete.emit(success, message)
            
        except Exception as e:
            self.test_complete.emit(False, f"Connection test failed: {str(e)}")
