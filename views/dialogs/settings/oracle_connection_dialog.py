# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# views/dialogs/settings/oracle_connection_dialog.py
"""Enhanced Oracle connection dialog.

This dialog persists connection details while storing passwords securely in the
operating system's keyring via the :mod:`keyring` library. Only non-sensitive
fields are written to :class:`~PySide6.QtCore.QSettings`.
"""
import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QComboBox, QPushButton, QHBoxLayout, QLabel,
                               QSpinBox, QCheckBox, QTextEdit, QGroupBox,
                               QMessageBox, QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal, QSettings
from PySide6.QtGui import QFont

from config.constants import ORGANIZATION_NAME, APP_NAME

try:  # pragma: no cover - optional dependency
    import keyring
    KEYRING_AVAILABLE = True
except Exception:  # pragma: no cover - handle missing keyring
    keyring = None
    KEYRING_AVAILABLE = False

logger = logging.getLogger(__name__)

KEYRING_SERVICE = f"{APP_NAME}_OracleConnection"

class ConnectionTestThread(QThread):
    """Thread for testing Oracle connection without blocking UI"""
    result_ready = Signal(bool, str)
    progress_update = Signal(str)
    
    def __init__(self, connection_details):
        super().__init__()
        self.connection_details = connection_details
    
    def run(self):
        try:
            self.progress_update.emit("Validating connection parameters...")
            self.msleep(500)  # Small delay for user feedback
            
            # Basic validation
            required_fields = ['host', 'port', 'username']
            missing_fields = [field for field in required_fields 
                            if not self.connection_details.get(field)]
            
            if missing_fields:
                self.result_ready.emit(False, f"Missing required fields: {', '.join(missing_fields)}")
                return
            
            self.progress_update.emit("Testing network connectivity...")
            self.msleep(1000)
            
            # TODO: Replace with actual cx_Oracle connection test
            # For now, simulate connection test
            try:
                try:
                    import oracledb
                except Exception:
                    import cx_Oracle as oracledb  # type: ignore
                        
            except Exception as e:  # pragma: no cover - import error handling
                self.result_ready.emit(False, f"Oracle client library not available: {str(e)}")
                return

            host = self.connection_details['host']
            port = self.connection_details['port']
            username = self.connection_details['username']
            password = self.connection_details['password']

            if self.connection_details['connection_type'] == 'SID':
                sid = self.connection_details.get('sid')
                dsn = oracledb.makedsn(host, port, sid=sid)
            else:
                service_name = self.connection_details.get('service_name')
                dsn = oracledb.makedsn(host, port, service_name=service_name)

            self.progress_update.emit("Establishing database connection...")
            connection = cursor = None
            try:
                connection = oracledb.connect(user=username, password=password, dsn=dsn)
                self.progress_update.emit("Testing database access...")
                cursor = connection.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.fetchone()
                
            except Exception as e:
                # This would catch actual cx_Oracle exceptions
                self.result_ready.emit(False, f"Database connection failed: {str(e)}")
                return
            finally:  # pragma: no cover - cleanup
                try:
                    if cursor:
                        cursor.close()
                    if connection:
                        connection.close()
                except Exception:
                    pass

            self.progress_update.emit("Connection successful!")
            self.msleep(500)
            self.result_ready.emit(True, "Connection test successful! Database is accessible.")

        except Exception as e:
            self.result_ready.emit(False, f"Connection test error: {str(e)}")

class OracleConnectionDialog(QDialog):
    """Enhanced Oracle connection configuration dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Oracle ERP Connection")
        self.setMinimumSize(650, 600)
        self.setModal(True)
        
        # Connection test thread
        self.test_thread = None
        
        self.setup_ui()
        self.connect_signals()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("Configure Oracle ERP Database Connection")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 6px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(header_label)
        
        # Connection details group
        connection_group = QGroupBox("Database Connection Details")
        connection_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #34495e;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: white;
            }
        """)
        form_layout = QFormLayout(connection_group)
        form_layout.setSpacing(10)
        
        # Host/Server
        self.host = QLineEdit()
        self.host.setPlaceholderText("e.g., oracle.company.com or 192.168.1.100")
        self.host.setStyleSheet(self._get_input_style())
        form_layout.addRow("Host/Server:", self.host)
        
        # Port
        port_layout = QHBoxLayout()
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(1521)
        self.port.setStyleSheet(self._get_input_style())
        port_layout.addWidget(self.port)
        port_layout.addStretch()
        form_layout.addRow("Port:", port_layout)
        
        # Connection type
        self.connection_type = QComboBox()
        self.connection_type.addItems(["SID", "Service Name"])
        self.connection_type.setStyleSheet(self._get_input_style())
        self.connection_type.currentTextChanged.connect(self.on_connection_type_changed)
        form_layout.addRow("Connection Type:", self.connection_type)
        
        # SID
        self.sid = QLineEdit()
        self.sid.setPlaceholderText("e.g., ORCL, XE, PROD")
        self.sid.setStyleSheet(self._get_input_style())
        form_layout.addRow("SID:", self.sid)
        
        # Service Name
        self.service_name = QLineEdit()
        self.service_name.setPlaceholderText("e.g., orcl.company.com")
        self.service_name.setStyleSheet(self._get_input_style())
        self.service_name.setVisible(False)
        self.service_name_label = form_layout.labelForField(self.service_name)
        form_layout.addRow("Service Name:", self.service_name)
        
        layout.addWidget(connection_group)
        
        # Authentication group
        auth_group = QGroupBox("Authentication Details")
        auth_group.setStyleSheet(connection_group.styleSheet())
        auth_layout = QFormLayout(auth_group)
        auth_layout.setSpacing(10)
        
        # Username
        self.username = QLineEdit()
        self.username.setPlaceholderText("Database username")
        self.username.setStyleSheet(self._get_input_style())
        auth_layout.addRow("Username:", self.username)
        
        # Password
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Enter password")
        self.password.setStyleSheet(self._get_input_style())
        auth_layout.addRow("Password:", self.password)
        
        # Additional options
        options_layout = QHBoxLayout()
        
        self.use_ssl = QCheckBox("Use SSL/TLS Connection")
        self.use_ssl.setStyleSheet("QCheckBox { font-weight: normal; }")
        options_layout.addWidget(self.use_ssl)
        
        self.save_password = QCheckBox("Save Password (encrypted)")
        self.save_password.setStyleSheet("QCheckBox { font-weight: normal; }")
        options_layout.addWidget(self.save_password)
        
        options_layout.addStretch()
        auth_layout.addRow("Options:", options_layout)
        
        layout.addWidget(auth_group)
        
        # Connection test section
        test_group = QGroupBox("Connection Test")
        test_group.setStyleSheet(connection_group.styleSheet())
        test_layout = QVBoxLayout(test_group)
        
        # Test button and progress
        test_button_layout = QHBoxLayout()
        self.btn_test = QPushButton("Test Connection")
        self.btn_test.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        test_button_layout.addWidget(self.btn_test)
        test_button_layout.addStretch()
        test_layout.addLayout(test_button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        test_layout.addWidget(self.progress_bar)
        
        # Progress status
        self.progress_status = QLabel("")
        self.progress_status.setAlignment(Qt.AlignCenter)
        self.progress_status.setStyleSheet("color: #7f8c8d; font-style: italic;")
        test_layout.addWidget(self.progress_status)
        
        # Test results
        self.test_results = QTextEdit()
        self.test_results.setMaximumHeight(100)
        self.test_results.setReadOnly(True)
        self.test_results.setPlaceholderText("Connection test results will appear here...")
        self.test_results.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 8px;
                background-color: #f8f9fa;
                font-family: Consolas, Monaco, monospace;
                font-size: 11px;
            }
        """)
        test_layout.addWidget(self.test_results)
        
        layout.addWidget(test_group)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        # Help button
        self.btn_help = QPushButton("Help")
        self.btn_help.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.btn_help.clicked.connect(self.show_help)
        
        self.btn_save = QPushButton("Save & Close")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        button_layout.addWidget(self.btn_help)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
    
    def _get_input_style(self):
        """Get consistent input field styling"""
        return """
            QLineEdit, QSpinBox, QComboBox {
                padding: 8px 12px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                font-size: 11px;
                background-color: white;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #3498db;
            }
            QLineEdit:hover, QSpinBox:hover, QComboBox:hover {
                border-color: #85929e;
            }
        """
    
    def connect_signals(self):
        """Connect UI signals"""
        self.btn_test.clicked.connect(self.test_connection)
        self.btn_save.clicked.connect(self.save_and_close)
        self.btn_cancel.clicked.connect(self.reject)
    
    def on_connection_type_changed(self, connection_type):
        """Handle connection type change"""
        if connection_type == "SID":
            self.sid.setVisible(True)
            self.service_name.setVisible(False)
        else:
            self.sid.setVisible(False)
            self.service_name.setVisible(True)
    
    def test_connection(self):
        """Test the Oracle connection"""
        # Validate required fields
        validation_errors = []
        
        if not self.host.text().strip():
            validation_errors.append("Host is required")
        if not self.username.text().strip():
            validation_errors.append("Username is required")
        if not self.password.text().strip():
            validation_errors.append("Password is required")
        
        connection_type = self.connection_type.currentText()
        if connection_type == "SID" and not self.sid.text().strip():
            validation_errors.append("SID is required when using SID connection type")
        if connection_type == "Service Name" and not self.service_name.text().strip():
            validation_errors.append("Service Name is required when using Service Name connection type")
        
        if validation_errors:
            self.show_test_result(False, "Validation errors:\n• " + "\n• ".join(validation_errors))
            return
        
        # Disable test button and show progress
        self.btn_test.setEnabled(False)
        self.btn_test.setText("Testing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.test_results.clear()
        
        # Prepare connection details
        connection_details = {
            'host': self.host.text().strip(),
            'port': self.port.value(),
            'username': self.username.text().strip(),
            'password': self.password.text(),
            'connection_type': connection_type,
            'sid': self.sid.text().strip() if connection_type == "SID" else None,
            'service_name': self.service_name.text().strip() if connection_type == "Service Name" else None,
            'use_ssl': self.use_ssl.isChecked()
        }
        
        # Start connection test in background thread
        self.test_thread = ConnectionTestThread(connection_details)
        self.test_thread.result_ready.connect(self.on_test_result)
        self.test_thread.progress_update.connect(self.on_progress_update)
        self.test_thread.start()
    
    def on_progress_update(self, message):
        """Handle progress update from test thread"""
        self.progress_status.setText(message)
    
    def on_test_result(self, success, message):
        """Handle connection test result"""
        self.show_test_result(success, message)
        
        # Re-enable test button and hide progress
        self.btn_test.setEnabled(True)
        self.btn_test.setText("Test Connection")
        self.progress_bar.setVisible(False)
        self.progress_status.clear()
        
        # Clean up thread
        if self.test_thread:
            self.test_thread.quit()
            self.test_thread.wait()
            self.test_thread = None
    
    def show_test_result(self, success, message):
        """Show connection test result"""
        if success:
            self.test_results.setStyleSheet(self.test_results.styleSheet() + """
                QTextEdit {
                    color: #27ae60;
                    background-color: #d5f4e6;
                    border-color: #27ae60;
                }
            """)
            self.test_results.setText(message)
        else:
            self.test_results.setStyleSheet(self.test_results.styleSheet() + """
                QTextEdit {
                    color: #e74c3c;
                    background-color: #fadbd8;
                    border-color: #e74c3c;
                }
            """)
            self.test_results.setText(message)
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
Oracle Connection Help

Connection Details:
• Host/Server: The Oracle database server hostname or IP address
• Port: Database port (usually 1521)
• Connection Type: Choose between SID or Service Name
• SID: System Identifier (e.g., ORCL, XE)
• Service Name: Full service name (e.g., orcl.company.com)

Authentication:
• Username: Database username with appropriate permissions
• Password: Database password
• SSL/TLS: Enable for encrypted connections
• Save Password: Stores password securely (encrypted)

Common Issues:
• Network connectivity: Ensure server is reachable
• Firewall: Port 1521 must be open
• TNS Names: Verify SID/Service Name is correct
• Permissions: User must have necessary database privileges

For ERP integration, ensure your database user has:
• SELECT permissions on relevant tables
• Access to financial/GL data views
        """
        
        QMessageBox.information(self, "Oracle Connection Help", help_text)
    
    def save_and_close(self):
        """Save connection settings and close dialog"""
        # Validate required fields
        if not self.host.text().strip():
            QMessageBox.warning(self, "Validation Error", "Host is required")
            self.host.setFocus()
            return
        
        if not self.username.text().strip():
            QMessageBox.warning(self, "Validation Error", "Username is required")
            self.username.setFocus()
            return
        
        connection_type = self.connection_type.currentText()
        if connection_type == "SID" and not self.sid.text().strip():
            QMessageBox.warning(self, "Validation Error", "SID is required when using SID connection type")
            self.sid.setFocus()
            return
        
        if connection_type == "Service Name" and not self.service_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Service Name is required when using Service Name connection type")
            self.service_name.setFocus()
            return
        
        # Save settings
        self.save_settings()
        
        # Show confirmation
        QMessageBox.information(
            self, "Settings Saved", 
            "Oracle connection settings have been saved successfully!"
        )
        
        # Accept dialog
        self.accept()
    
    def get_connection_details(self):
        """Return current connection details.

        The returned dictionary includes the plain-text password for in-memory
        use only. :meth:`save_settings` is responsible for placing the password
        into the system keyring when requested, ensuring it is never persisted
        in plain text.
        """
        connection_type = self.connection_type.currentText()
        return {
            "host": self.host.text().strip(),
            "port": self.port.value(),
            "username": self.username.text().strip(),
            "password": self.password.text(),
            "connection_type": connection_type,
            "sid": self.sid.text().strip() if connection_type == "SID" else None,
            "service_name": self.service_name.text().strip()
            if connection_type == "Service Name"
            else None,
            "use_ssl": self.use_ssl.isChecked(),
            "save_password": self.save_password.isChecked(),
        }
    
    def load_settings(self):
        """Load existing connection settings from QSettings and keyring."""
        settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        settings.beginGroup("OracleConnection")
        self.host.setText(settings.value("host", "localhost"))
        self.port.setValue(int(settings.value("port", 1521)))
        conn_type = settings.value("connection_type", "SID")
        self.connection_type.setCurrentText(conn_type)
        self.sid.setText(settings.value("sid", "ORCL"))
        self.service_name.setText(settings.value("service_name", ""))
        username = settings.value("username", "")
        self.username.setText(username)
        if settings.value("save_password", False, type=bool) and keyring:
            stored = keyring.get_password(KEYRING_SERVICE, username)
            if stored:
                self.password.setText(stored)
                self.save_password.setChecked(True)
        self.use_ssl.setChecked(settings.value("use_ssl", False, type=bool))
        settings.endGroup()
    
    def save_settings(self):
        """Persist connection settings using QSettings and keyring."""
        details = self.get_connection_details()
        
        settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        settings.beginGroup("OracleConnection")

        for key, value in details.items():
            if key in {"password"}:
                continue  # Never persist raw passwords in QSettings
            settings.setValue(key, value)
        settings.endGroup()
        
        if keyring:
            if KEYRING_AVAILABLE and keyring:
                if details.get("save_password"):
                    keyring.set_password(
                        KEYRING_SERVICE, details.get("username", ""), details.get("password", "")
                    )
                else:
                    try:
                        keyring.delete_password(KEYRING_SERVICE, details.get("username", ""))
                    except Exception as e:
                        logger.warning("Keyring deletion failed: %s", e)
            
    def closeEvent(self, event):
        """Handle dialog close event"""
        # Clean up any running threads
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.quit()
            self.test_thread.wait()
        event.accept()