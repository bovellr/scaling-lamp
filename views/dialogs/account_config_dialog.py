# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# ACCOUNT CONFIGURATION DIALOG
# ============================================================================

# views/dialogs/account_config_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLineEdit, QComboBox, QPushButton, QTableWidget, 
                               QTableWidgetItem, QGroupBox, QMessageBox, QLabel,
                               QHeaderView, QAbstractItemView, QSplitter)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont
import json
from pathlib import Path
import uuid


class AccountConfigDialog(QDialog):
    """Dialog for managing bank account configurations"""
    
    # Signal emitted when accounts are updated
    accounts_updated = Signal(dict)  # new_accounts_config
    
    def __init__(self, current_accounts_config=None, parent=None):
        super().__init__(parent)
        self.current_accounts_config = current_accounts_config or {}
        self.modified_accounts = self.current_accounts_config.copy()
        
        self.setup_ui()
        self.load_accounts_to_table()
        
        # Track if changes were made
        self.changes_made = False
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Bank Account Configuration")
        self.setMinimumSize(900, 600)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Bank Account Configuration")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("padding: 15px; background-color: #f0f0f0; border-radius: 5px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Create splitter for table and form
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Account list
        self._create_account_list_section(splitter)
        
        # Right side: Account details form
        self._create_account_form_section(splitter)
        
        # Set splitter proportions
        splitter.setSizes([400, 500])
        layout.addWidget(splitter)
        
        # Buttons
        self._create_buttons_section(layout)
    
    def _create_account_list_section(self, parent):
        """Create the account list section"""
        list_widget = QGroupBox("Bank Accounts")
        list_layout = QVBoxLayout(list_widget)
        
        # Account table
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(3)
        self.accounts_table.setHorizontalHeaderLabels(["Account Name", "Account Number", "Currency"])
        
        # Table settings
        self.accounts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.accounts_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.accounts_table.setAlternatingRowColors(True)
        
        # Resize columns
        header = self.accounts_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 150)
        header.resizeSection(1, 120)
        
        # Connect selection
        self.accounts_table.itemSelectionChanged.connect(self.on_account_selected)
        
        list_layout.addWidget(self.accounts_table)
        
        # List buttons
        list_buttons_layout = QHBoxLayout()
        
        self.btn_new_account = QPushButton("New Account")
        self.btn_delete_account = QPushButton("Delete Account")
        self.btn_duplicate_account = QPushButton("Duplicate")
        
        self.btn_new_account.clicked.connect(self.new_account)
        self.btn_delete_account.clicked.connect(self.delete_account)
        self.btn_duplicate_account.clicked.connect(self.duplicate_account)
        
        list_buttons_layout.addWidget(self.btn_new_account)
        list_buttons_layout.addWidget(self.btn_duplicate_account)
        list_buttons_layout.addWidget(self.btn_delete_account)
        
        list_layout.addLayout(list_buttons_layout)
        
        parent.addWidget(list_widget)
    
    def _create_account_form_section(self, parent):
        """Create the account form section"""
        form_widget = QGroupBox("Account Details")
        form_layout = QVBoxLayout(form_widget)
        
        # Form
        self.form_layout = QFormLayout()
        
        # Account Name
        self.edit_account_name = QLineEdit()
        self.edit_account_name.textChanged.connect(self.on_form_changed)
        self.form_layout.addRow("Account Name:", self.edit_account_name)
        
        # Account Number
        self.edit_account_number = QLineEdit()
        self.edit_account_number.setPlaceholderText("e.g., 12345678")
        self.edit_account_number.textChanged.connect(self.on_form_changed)
        self.form_layout.addRow("Account Number:", self.edit_account_number)
        
        # Sort Code
        self.edit_sort_code = QLineEdit()
        self.edit_sort_code.setPlaceholderText("e.g., 12-34-56")
        self.edit_sort_code.textChanged.connect(self.on_form_changed)
        self.form_layout.addRow("Sort Code:", self.edit_sort_code)
        
        # Currency
        self.combo_currency = QComboBox()
        self.combo_currency.addItems(["GBP", "USD", "EUR", "CAD", "AUD", "JPY"])
        self.combo_currency.currentTextChanged.connect(self.on_form_changed)
        self.form_layout.addRow("Currency:", self.combo_currency)
        
        # Statement Transformer
        self.combo_transformer = QComboBox()
        self.combo_transformer.setEditable(True)
        self.combo_transformer.addItems([
            "standard_uk_bank",
            "business_uk_bank", 
            "usd_bank",
            "savings_uk_bank",
            "lloyds_transformer",
            "hsbc_transformer",
            "barclays_transformer",
            "natwest_transformer",
            "santander_transformer"
        ])
        self.combo_transformer.currentTextChanged.connect(self.on_form_changed)
        self.form_layout.addRow("Statement Transformer:", self.combo_transformer)
        
        # ERP Account Code
        self.edit_erp_code = QLineEdit()
        self.edit_erp_code.setPlaceholderText("e.g., 1001")
        self.edit_erp_code.textChanged.connect(self.on_form_changed)
        self.form_layout.addRow("ERP Account Code:", self.edit_erp_code)
        
        # ERP Account Name
        self.edit_erp_name = QLineEdit()
        self.edit_erp_name.setPlaceholderText("e.g., Main Bank Account")
        self.edit_erp_name.textChanged.connect(self.on_form_changed)
        self.form_layout.addRow("ERP Account Name:", self.edit_erp_name)
        
        # Statement Format
        self.combo_statement_format = QComboBox()
        self.combo_statement_format.setEditable(True)
        self.combo_statement_format.addItems([
            "UK_STANDARD",
            "UK_BUSINESS", 
            "US_STANDARD",
            "UK_SAVINGS",
            "EUROPEAN_STANDARD"
        ])
        self.combo_statement_format.currentTextChanged.connect(self.on_form_changed)
        self.form_layout.addRow("Statement Format:", self.combo_statement_format)
        
        form_layout.addLayout(self.form_layout)
        
        # Form buttons
        form_buttons_layout = QHBoxLayout()
        
        self.btn_save_account = QPushButton("Save Account")
        self.btn_reset_form = QPushButton("Reset Form")
        
        self.btn_save_account.clicked.connect(self.save_current_account)
        self.btn_reset_form.clicked.connect(self.reset_form)
        
        # Initially disable save button
        self.btn_save_account.setEnabled(False)
        
        form_buttons_layout.addWidget(self.btn_save_account)
        form_buttons_layout.addWidget(self.btn_reset_form)
        form_buttons_layout.addStretch()
        
        form_layout.addLayout(form_buttons_layout)
        
        parent.addWidget(form_widget)
    
    def _create_buttons_section(self, layout):
        """Create dialog buttons"""
        buttons_layout = QHBoxLayout()
        
        # Import/Export buttons
        self.btn_import_config = QPushButton("Import Config")
        self.btn_export_config = QPushButton("Export Config")
        
        self.btn_import_config.clicked.connect(self.import_configuration)
        self.btn_export_config.clicked.connect(self.export_configuration)
        
        buttons_layout.addWidget(self.btn_import_config)
        buttons_layout.addWidget(self.btn_export_config)
        buttons_layout.addStretch()
        
        # Dialog buttons
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")
        
        self.btn_ok.clicked.connect(self.accept_changes)
        self.btn_cancel.clicked.connect(self.reject_changes)
        
        # Style the main buttons
        self.btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        
        buttons_layout.addWidget(self.btn_ok)
        buttons_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(buttons_layout)
    
    def load_accounts_to_table(self):
        """Load accounts into the table"""
        self.accounts_table.setRowCount(len(self.modified_accounts))
        
        for row, (account_name, config) in enumerate(self.modified_accounts.items()):
            # Account name
            name_item = QTableWidgetItem(account_name)
            self.accounts_table.setItem(row, 0, name_item)
            
            # Account number
            number_item = QTableWidgetItem(config.get('account_number', ''))
            self.accounts_table.setItem(row, 1, number_item)
            
            # Currency
            currency_item = QTableWidgetItem(config.get('currency', ''))
            self.accounts_table.setItem(row, 2, currency_item)
    
    @Slot()
    def on_account_selected(self):
        """Handle account selection in table"""
        current_row = self.accounts_table.currentRow()
        if current_row >= 0:
            # Get account name from first column
            account_name = self.accounts_table.item(current_row, 0).text()
            if account_name in self.modified_accounts:
                self.load_account_to_form(account_name)
    
    def load_account_to_form(self, account_name):
        """Load account details into the form"""
        if account_name not in self.modified_accounts:
            return
        
        config = self.modified_accounts[account_name]
        
        # Block signals to prevent triggering changes
        self.block_form_signals(True)
        
        self.edit_account_name.setText(account_name)
        self.edit_account_number.setText(config.get('account_number', ''))
        self.edit_sort_code.setText(config.get('sort_code', ''))
        self.combo_currency.setCurrentText(config.get('currency', 'GBP'))
        self.combo_transformer.setCurrentText(config.get('transformer', 'standard_uk_bank'))
        self.edit_erp_code.setText(config.get('erp_account_code', ''))
        self.edit_erp_name.setText(config.get('erp_account_name', ''))
        self.combo_statement_format.setCurrentText(config.get('statement_format', 'UK_STANDARD'))
        
        # Re-enable signals
        self.block_form_signals(False)
        
        # Store current account being edited
        self.current_editing_account = account_name
    
    def block_form_signals(self, block):
        """Block/unblock form signals"""
        widgets = [
            self.edit_account_name, self.edit_account_number, self.edit_sort_code,
            self.combo_currency, self.combo_transformer, self.edit_erp_code,
            self.edit_erp_name, self.combo_statement_format
        ]
        
        for widget in widgets:
            widget.blockSignals(block)
    
    @Slot()
    def on_form_changed(self):
        """Handle form field changes"""
        # Enable save button when form is modified
        self.btn_save_account.setEnabled(True)
        self.changes_made = True
    
    @Slot()
    def new_account(self):
        """Create a new account"""
        # Clear form
        self.reset_form()
        
        # Set default values
        self.edit_account_name.setText("New Account")
        self.combo_currency.setCurrentText("GBP")
        self.combo_transformer.setCurrentText("standard_uk_bank")
        self.combo_statement_format.setCurrentText("UK_STANDARD")
        
        # Clear selection in table
        self.accounts_table.clearSelection()
        
        # Mark as new account
        self.current_editing_account = None
    
    @Slot()
    def duplicate_account(self):
        """Duplicate the selected account"""
        current_row = self.accounts_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an account to duplicate.")
            return
        
        # Get current account
        account_name = self.accounts_table.item(current_row, 0).text()
        if account_name in self.modified_accounts:
            # Create duplicate with new name
            new_name = f"{account_name} (Copy)"
            counter = 1
            while new_name in self.modified_accounts:
                new_name = f"{account_name} (Copy {counter})"
                counter += 1
            
            # Copy configuration
            self.modified_accounts[new_name] = self.modified_accounts[account_name].copy()
            
            # Refresh table and select new account
            self.load_accounts_to_table()
            self.select_account_in_table(new_name)
            self.changes_made = True
    
    @Slot()
    def delete_account(self):
        """Delete the selected account"""
        current_row = self.accounts_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an account to delete.")
            return
        
        account_name = self.accounts_table.item(current_row, 0).text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete the account '{account_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove from config
            if account_name in self.modified_accounts:
                del self.modified_accounts[account_name]
                
                # Refresh table
                self.load_accounts_to_table()
                
                # Clear form
                self.reset_form()
                
                self.changes_made = True
    
    @Slot()
    def save_current_account(self):
        """Save the current account being edited"""
        # Validate form
        if not self.validate_form():
            return
        
        # Get form data
        account_name = self.edit_account_name.text().strip()
        
        # Check for duplicate names (except current)
        if (account_name in self.modified_accounts and 
            account_name != getattr(self, 'current_editing_account', None)):
            QMessageBox.warning(self, "Duplicate Name", 
                              f"An account named '{account_name}' already exists.")
            return
        
        # Create configuration
        config = {
            'account_number': self.edit_account_number.text().strip(),
            'sort_code': self.edit_sort_code.text().strip(),
            'currency': self.combo_currency.currentText(),
            'transformer': self.combo_transformer.currentText(),
            'erp_account_code': self.edit_erp_code.text().strip(),
            'erp_account_name': self.edit_erp_name.text().strip(),
            'statement_format': self.combo_statement_format.currentText()
        }
        
        # Handle rename if needed
        old_name = getattr(self, 'current_editing_account', None)
        if old_name and old_name != account_name and old_name in self.modified_accounts:
            # Remove old entry
            del self.modified_accounts[old_name]
        
        # Save configuration
        self.modified_accounts[account_name] = config
        
        # Refresh table
        self.load_accounts_to_table()
        
        # Select the saved account
        self.select_account_in_table(account_name)
        
        # Disable save button
        self.btn_save_account.setEnabled(False)
        
        self.changes_made = True
        
        QMessageBox.information(self, "Account Saved", f"Account '{account_name}' saved successfully.")
    
    def validate_form(self):
        """Validate form data"""
        if not self.edit_account_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Account name is required.")
            self.edit_account_name.setFocus()
            return False
        
        if not self.edit_account_number.text().strip():
            QMessageBox.warning(self, "Validation Error", "Account number is required.")
            self.edit_account_number.setFocus()
            return False
        
        if not self.edit_erp_code.text().strip():
            QMessageBox.warning(self, "Validation Error", "ERP account code is required.")
            self.edit_erp_code.setFocus()
            return False
        
        return True
    
    def select_account_in_table(self, account_name):
        """Select an account in the table by name"""
        for row in range(self.accounts_table.rowCount()):
            item = self.accounts_table.item(row, 0)
            if item and item.text() == account_name:
                self.accounts_table.selectRow(row)
                break
    
    @Slot()
    def reset_form(self):
        """Reset the form to empty state"""
        self.block_form_signals(True)
        
        self.edit_account_name.clear()
        self.edit_account_number.clear()
        self.edit_sort_code.clear()
        self.combo_currency.setCurrentText("GBP")
        self.combo_transformer.setCurrentText("standard_uk_bank")
        self.edit_erp_code.clear()
        self.edit_erp_name.clear()
        self.combo_statement_format.setCurrentText("UK_STANDARD")
        
        self.block_form_signals(False)
        
        self.btn_save_account.setEnabled(False)
        self.current_editing_account = None
    
    @Slot()
    def import_configuration(self):
        """Import account configuration from file"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Account Configuration", "",
            "JSON files (*.json);;All files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported_config = json.load(f)
                
                # Validate structure
                if not isinstance(imported_config, dict):
                    raise ValueError("Invalid configuration format")
                
                # Merge with existing configuration
                for account_name, config in imported_config.items():
                    if account_name in self.modified_accounts:
                        reply = QMessageBox.question(
                            self, "Account Exists",
                            f"Account '{account_name}' already exists. Overwrite?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            continue
                    
                    self.modified_accounts[account_name] = config
                
                # Refresh table
                self.load_accounts_to_table()
                self.changes_made = True
                
                QMessageBox.information(self, "Import Successful", 
                                      f"Configuration imported from {Path(file_path).name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", 
                                   f"Failed to import configuration:\n{str(e)}")
    
    @Slot()
    def export_configuration(self):
        """Export account configuration to file"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Account Configuration", "bank_accounts_config.json",
            "JSON files (*.json);;All files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.modified_accounts, f, indent=2)
                
                QMessageBox.information(self, "Export Successful", 
                                      f"Configuration exported to {Path(file_path).name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", 
                                   f"Failed to export configuration:\n{str(e)}")
    
    @Slot()
    def accept_changes(self):
        """Accept changes and close dialog"""
        if self.changes_made:
            # Emit signal with updated configuration
            self.accounts_updated.emit(self.modified_accounts)
        
        self.accept()
    
    @Slot()
    def reject_changes(self):
        """Reject changes and close dialog"""
        if self.changes_made:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        self.reject()