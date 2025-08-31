# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
"""Main application window"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,QMenu ,QTabWidget, 
                               QStatusBar, QLabel, QComboBox, QPushButton, QDateEdit, QSlider, 
                               QGroupBox, QMessageBox,QFileDialog, QScrollArea, QDialog, QStyle)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction
from pathlib import Path
import logging
import os
import pandas as pd

from .dialogs.dialog_manager import DialogManager
from .dialogs.account_config_dialog import AccountConfigDialog
from .widgets.file_upload_widget import FileUploadWidget
from .widgets.action_buttons_widget import ActionButtonsWidget
from .widgets.filters_widget import FiltersWidget
from .widgets.ai_results_widget import AiResultsWidget
from .widgets.transaction_tables_widget import TransactionTablesWidget
from .widgets.summary_cards_widget import SummaryCardsWidget
from .widgets.account_export_widget import AccountExportWidget
from .widgets.reports_widget import ReportsWidget
from .widgets.erp_data_widget import ERPDataWidget

from viewmodels.erp_database_viewmodel import ERPDatabaseViewModel
from viewmodels.upload_viewmodel import UploadViewModel
from viewmodels.matching_viewmodel import MatchingViewModel
from models.data_models import TransactionData
from services.account_service import AccountService

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, settings=None, event_bus=None):
        super().__init__()
        self.settings = settings
        self.event_bus = event_bus
        # Initialize state variables
        self._init_state_variables()
        self.setup_ui()
    
    # State variables
    def _init_state_variables(self):
        """Initialize state variables"""
        self.bank_data = None
        self.ledger_data = None
        self.preview_data = None
        self.reconciliation_data = None
        self.reconciliation_results = None
        self.reconciliation_status = None
        self.reconciliation_progress = None
        
        # ViewModels
        self.erp_viewmodel = ERPDatabaseViewModel()
        self.upload_viewmodel = UploadViewModel()
        self.matching_viewmodel = MatchingViewModel()

        # Account configuration service
        self.account_service = AccountService(event_bus=self.event_bus)
        self.account_manager = self.account_service.account_manager
        self.bank_accounts_config = self.account_service.bank_accounts_config

        # Current selected account
        self.current_bank_account = None

    # UI setup
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("Bank Reconciliation AI")
        self.setMinimumSize(1200, 900)
        
        # Dialog handler
        self.dialog_manager = DialogManager(self)
       
        
        # Create main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        
        # Build menu and toolbar
        self._build_menu_toolbar()

        # Create header section
        self._create_header_with_account_selector(self.main_layout)
    
        # Create tab widget section
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)
        self.main_layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_file_upload_tab()
        self._create_erp_data_tab()
        self._create_matching_reconciliation_tab()
        self._create_summary_reports_tab()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Select a tab to begin")

        # Apply styles
        self._apply_styles()
        
    def _create_header_with_account_selector(self, layout):
        """Add welcome header with bank account selector"""
        # Create header container
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Welcome label (left side)
        welcome = QLabel("Bank Reconciliation")
        welcome.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        header_layout.addWidget(welcome)
        
        # Stretch to push account selector to right
        header_layout.addStretch()
        
        # Account selector section (right side)
        account_section = QWidget()
        account_layout = QVBoxLayout(account_section)
        account_layout.setSpacing(5)
        
        # Account selector label with manage button
        label_layout = QHBoxLayout()
        account_label = QLabel("Bank Account:")
        account_label.setStyleSheet("font-weight: bold; color: #34495e;")
        label_layout.addWidget(account_label)
        
        # Manage accounts button
        self.btn_manage_accounts = QPushButton()
        self.btn_manage_accounts.setToolTip("Manage Bank Accounts")
        self.btn_manage_accounts.setIcon(
            self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        )
        self.btn_manage_accounts.setMaximumSize(30, 25)
        self.btn_manage_accounts.clicked.connect(self.open_account_config_dialog)
        self.btn_manage_accounts.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            """
        )
        label_layout.addWidget(self.btn_manage_accounts)
    
        account_layout.addLayout(label_layout)
        
        # Account selector combobox
        self.combo_bank_account = QComboBox()
        self.combo_bank_account.setMinimumWidth(250)
        self.combo_bank_account.addItem("Select Bank Account...", None)
        
        # Populate with bank accounts
        for account_name, config in self.bank_accounts_config.items():
            display_text = f"{account_name} ({config['account_number'][-4:]})"
            self.combo_bank_account.addItem(display_text, account_name)
        
        # Connect account selection handler
        self.combo_bank_account.currentTextChanged.connect(self.on_bank_account_changed)
        
        # Style the combobox
        self.combo_bank_account.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background-color: white;
                font-size: 12px;
                font-weight: 500;
            }
            QComboBox:hover {
                border-color: #2980b9;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
        
        account_layout.addWidget(self.combo_bank_account)
        header_layout.addWidget(account_section)
        
        # Style the entire header
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ecf0f1, stop:1 #bdc3c7);
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        
        layout.addWidget(header_widget)

    def _create_file_upload_tab(self):
        """Create the file upload tab"""
        # Create upload widget
        self.upload_widget = FileUploadWidget(viewmodel=self.upload_viewmodel)
        self.upload_widget.file_transformed.connect(self.on_bank_statement_ready)
        
        # Create scroll area for the upload widget
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.upload_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Add to tab widget
        self.tab_widget.addTab(scroll_area, "Bank Statement")    

    def _create_erp_data_tab(self):
        """Create the ERP data tab"""
        # Main widget for this tab
        self.erp_widget = ERPDataWidget()
        self.erp_widget.erp_data_loaded.connect(self.on_erp_data_ready)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.erp_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Add to tab widget
        self.tab_widget.addTab(scroll_area, "ERP Transactions")

    def _create_matching_reconciliation_tab(self):
        """Create the matching & reconciliation tab"""
        # Main widget for this tab
        matching_widget = QWidget()
        layout = QVBoxLayout(matching_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Action buttons section
        self.action_buttons = ActionButtonsWidget()
        self.btn_import_bank = self.action_buttons.btn_import_bank
        self.btn_import_gl = self.action_buttons.btn_import_gl
        self.btn_auto_match = self.action_buttons.btn_auto_match
        self.btn_train_model = self.action_buttons.btn_train_model
        self.btn_import_training = self.action_buttons.btn_import_training
        self.btn_import_bank.clicked.connect(self.import_bank_statement)
        self.btn_import_gl.clicked.connect(self.import_ledger_data)
        self.btn_auto_match.clicked.connect(self.run_reconciliation)
        self.btn_train_model.clicked.connect(self.train_ai_model)
        self.btn_import_training.clicked.connect(self.import_training_data)
        layout.addWidget(self.action_buttons)

        # Filters section
        self.filters_widget = FiltersWidget()
        layout.addWidget(self.filters_widget)
        self.combo_transaction_type = self.filters_widget.combo_transaction_type
        self.date_from = self.filters_widget.date_from
        self.date_to = self.filters_widget.date_to
        self.slider_confidence = self.filters_widget.slider_confidence
        self.label_confidence_value = self.filters_widget.label_confidence_value
        
        # AI Results section
        self.ai_results_widget = AiResultsWidget()
        layout.addWidget(self.ai_results_widget)
        self.lbl_high = self.ai_results_widget.lbl_high
        self.lbl_med = self.ai_results_widget.lbl_med
        self.lbl_low = self.ai_results_widget.lbl_low
        self.lbl_accuracy = self.ai_results_widget.lbl_accuracy
        self.lbl_precision = self.ai_results_widget.lbl_precision
        self.btn_review_low = self.ai_results_widget.btn_review_low
        self.btn_export_model = self.ai_results_widget.btn_export_model
        self.btn_review_low.clicked.connect(self.review_low_confidence)
        self.btn_export_model.clicked.connect(self.export_ai_model)
        
        # Transaction tables section
        self.transaction_tables = TransactionTablesWidget()
        layout.addWidget(self.transaction_tables)
        self.table_book = self.transaction_tables.table_book
        self.table_bank = self.transaction_tables.table_bank
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(matching_widget)
        scroll_area.setWidgetResizable(True)

        # Add to tab widget
        self.tab_widget.addTab(scroll_area, "Matching & Reconciliation")
 
    def _create_summary_reports_tab(self):
        """Create the summary & reports tab"""
        # Main widget for this tab
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Summary cards section
        self.summary_cards_widget = SummaryCardsWidget()
        layout.addWidget(self.summary_cards_widget)
        self.cards = self.summary_cards_widget.cards
        
        # Account selector and export section
        self.account_export_widget = AccountExportWidget()
        layout.addWidget(self.account_export_widget)
        self.combo_account = self.account_export_widget.combo_account
        self.btn_export = self.account_export_widget.btn_export
        self.btn_export.clicked.connect(self.export_report)
        
        # Reports and export options
        self.reports_widget = ReportsWidget()
        layout.addWidget(self.reports_widget)
        self.combo_export_format = self.reports_widget.combo_export_format
        
        # Add stretch
        layout.addStretch()
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(reports_widget)
        scroll_area.setWidgetResizable(True)
        
        # Add to tab widget
        self.tab_widget.addTab(scroll_area, "Summary & Reports")
        
    def _build_menu_toolbar(self):
        """Build the menu and toolbar"""
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("File")
        self._add_action(file_menu, "Import Bank Statement", self.import_bank_statement)
        self._add_action(file_menu, "Import Ledger Data", self.import_ledger_data)
        self._add_action(file_menu, "Import Training Data", self.import_training_data)
        file_menu.addSeparator()
        self._add_action(file_menu, "Exit", self.close)
        
        # Account configuration submenu
        account_submenu = file_menu.addMenu("Account Configuration")
        self._add_action(account_submenu, "Manage Bank Accounts...", self.open_account_config_dialog)
        self._add_action(account_submenu, "Import Account Config...", self.import_account_config)
        self._add_action(account_submenu, "Export Account Config...", self.export_account_config)
        account_submenu.addSeparator()
        self._add_action(account_submenu, "Reset to Defaults", self.reset_account_config)
    
        # View Menu
        view_menu = menu_bar.addMenu("View")
        self._add_action(view_menu, "Threshold Settings", self.dialog_manager.open_threshold_dialog)
        self._add_action(view_menu, "Oracle Connection Settings", self.dialog_manager.open_oracle_dialog)
        view_menu.addSeparator()
        self._add_action(view_menu, "Refresh Account List", self.refresh_account_list)

        # Run Menu
        run_menu = menu_bar.addMenu("Run")
        self._add_action(run_menu, "Train AI Model", self.train_ai_model)
        self._add_action(run_menu, "Run Reconciliation", self.run_reconciliation)
        
        # Help Menu
        help_menu = menu_bar.addMenu("Help")
        self._add_action(help_menu, "About", lambda: QMessageBox.about(self, "About", "Bank Reconciliation AI v1.0"))
        self._add_action(help_menu, "User Manual", lambda: logger.info("Open PDF manual"))

    def _add_action(self, menu: QMenu, label: str, slot=None):
        """Helper to add an action to a menu and connect it to a slot."""
        action = QAction(label, self)
        if slot:
            action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _apply_styles(self):
        qss_path = os.path.join("resources", "styles", "main.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.centralWidget().setStyleSheet(f.read())
        
        # Additional tab-specific styling
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
                border-bottom: 2px solid #007acc;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)


    # ==========================================================================
    # BANK ACCOUNT SELECTION LOGIC
    # ==========================================================================
    
    @Slot()
    def on_bank_account_changed(self):
        """Handle bank account selection change"""
        current_data = self.combo_bank_account.currentData()
        
        if current_data is None:
            # "Select Bank Account..." was chosen
            self.current_bank_account = None
            self.status_bar.showMessage("Please select a bank account to begin")
            self._update_ui_for_account_selection(None)
            return
        
        # Valid account selected
        self.current_bank_account = current_data
        account_config = self.bank_accounts_config[current_data]
        
        # Update status bar
        self.status_bar.showMessage(
            f"Selected: {current_data} | "
            f"Account: {account_config['account_number']} | "
            f"ERP Code: {account_config['erp_account_code']}"
        )
        
        # Update UI elements based on selected account
        self._update_ui_for_account_selection(account_config)
        
        # Log the selection for debugging
        logger.info(f"Bank account selected: {current_data}")
        logger.debug(f"Configuration: {account_config}")
    
    def _update_ui_for_account_selection(self, account_config):
        """Update UI elements based on selected bank account"""
        if account_config is None:
            # Disable features when no account selected
            self._set_reconciliation_features_enabled(False)
            return
        
        # Enable features when account is selected
        self._set_reconciliation_features_enabled(True)
        
        # Update any account-specific UI elements
        if hasattr(self, 'cards') and self.cards:
            # Update currency symbols on summary cards based on account currency
            currency_symbol = "£" if account_config['currency'] == "GBP" else "$"
            for card in self.cards:
                # This would update the card display - you'd need to implement this in SummaryCard
                card.update_value(currency_symbol)
        
        # Update file upload widget with account-specific information
        if hasattr(self, 'upload_widget'):
            # Pass account configuration to upload widget
            if hasattr(self.upload_widget, 'set_account_config'):
                self.upload_widget.set_account_config(account_config)
    
    def _set_reconciliation_features_enabled(self, enabled):
        """Enable/disable reconciliation features based on account selection"""
        # Define widgets that should be enabled/disabled
        widgets_to_toggle = []
        
        # Add action buttons if they exist
        if hasattr(self, 'btn_import_bank'):
            widgets_to_toggle.extend([
                self.btn_import_bank,
                self.btn_import_gl, 
                self.btn_auto_match,
                self.btn_train_model
            ])
        
        # Add other widgets as needed
        if hasattr(self, 'btn_export'):
            widgets_to_toggle.append(self.btn_export)
        
        # Enable/disable all widgets
        for widget in widgets_to_toggle:
            if widget:
                widget.setEnabled(enabled)
      
    def _df_to_transactions(self, df):
        """Convert a DataFrame to a list of TransactionData objects."""
        transactions = []
        if df is None or df.empty:
            return transactions
        for _, row in df.iterrows():
            date = row.get('date') or row.get('Date')
            description = row.get('description') or row.get('Description')
            amount = row.get('amount') or row.get('Amount')
            if pd.isna(date) or pd.isna(description) or pd.isna(amount):
                continue
            try:
                transactions.append(
                    TransactionData(
                        date=str(date),
                        description=str(description),
                        amount=float(amount)
                    )
                )
            except Exception:
                continue
        return transactions
    
    # ==========================================================================
    # SLOT IMPLEMENTATIONS
    # ==========================================================================
    
    @Slot()
    def open_account_config_dialog(self):
        """Open the account configuration dialog"""
        dialog = AccountConfigDialog(self.bank_accounts_config, self)
        dialog.accounts_updated.connect(self.on_accounts_updated)
        
        if dialog.exec() == QDialog.Accepted:
            self.status_bar.showMessage("Account configuration updated successfully")
        else:
            self.status_bar.showMessage("Account configuration cancelled")

    @Slot(dict)
    def on_accounts_updated(self, new_accounts_config):
        """Handle updated account configuration"""
        try:
            # Save to file
            if self.account_manager.save_accounts(new_accounts_config):
                # Update internal configuration
                self.bank_accounts_config = new_accounts_config
                
                # Refresh account selector
                self.refresh_account_selector()
                
                self.status_bar.showMessage("Account configuration saved successfully")
                
                QMessageBox.information(
                    self, "Configuration Updated",
                    f"Account configuration updated successfully!\n"
                    f"Total accounts: {len(new_accounts_config)}"
                )
            else:
                QMessageBox.critical(
                    self, "Save Error",
                    "Failed to save account configuration to file."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, "Update Error",
                f"Failed to update account configuration:\n{str(e)}"
            )

    def refresh_account_selector(self):
        """Refresh the account selector combobox"""
        # Remember current selection
        current_selection = self.combo_bank_account.currentData()
        
        # Clear and repopulate
        self.combo_bank_account.clear()
        self.combo_bank_account.addItem("Select Bank Account...", None)
        
        # Add accounts from current configuration
        for account_name, config in self.bank_accounts_config.items():
            display_text = f"{account_name} ({config['account_number'][-4:]})"
            self.combo_bank_account.addItem(display_text, account_name)
        
        # Restore selection if still exists
        if current_selection and current_selection in self.bank_accounts_config:
            for i in range(self.combo_bank_account.count()):
                if self.combo_bank_account.itemData(i) == current_selection:
                    self.combo_bank_account.setCurrentIndex(i)
                    break
        else:
            # Selection no longer exists, clear current account
            self.current_bank_account = None
            self.status_bar.showMessage("Please select a bank account to begin")

    @Slot()
    def refresh_account_list(self):
        """Refresh account list from file"""
        try:
            # Reload from file
            self.bank_accounts_config = self.account_manager.load_accounts()
            
            # Refresh selector
            self.refresh_account_selector()
            
            self.status_bar.showMessage(f"Account list refreshed - {len(self.bank_accounts_config)} accounts loaded")
            
        except Exception as e:
            QMessageBox.critical(
                self, "Refresh Error",
                f"Failed to refresh account list:\n{str(e)}"
            )

    @Slot()
    def import_account_config(self):
        """Import account configuration from external file"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Account Configuration", "",
            "JSON files (*.json);;All files (*.*)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r') as f:
                    imported_config = json.load(f)
                
                # Validate structure
                if not isinstance(imported_config, dict):
                    raise ValueError("Invalid configuration format")
                
                # Merge with existing configuration
                conflicts = []
                for account_name in imported_config:
                    if account_name in self.bank_accounts_config:
                        conflicts.append(account_name)
                
                if conflicts:
                    reply = QMessageBox.question(
                        self, "Import Conflicts",
                        f"The following accounts already exist:\n{', '.join(conflicts)}\n\n"
                        "Do you want to overwrite them?",
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                        QMessageBox.Cancel
                    )
                    
                    if reply == QMessageBox.Cancel:
                        return
                    elif reply == QMessageBox.No:
                        # Only import non-conflicting accounts
                        imported_config = {k: v for k, v in imported_config.items() if k not in conflicts}
                
                # Merge configurations
                self.bank_accounts_config.update(imported_config)
                
                # Save merged configuration
                if self.account_manager.save_accounts(self.bank_accounts_config):
                    self.refresh_account_selector()
                    
                    QMessageBox.information(
                        self, "Import Successful",
                        f"Successfully imported {len(imported_config)} account configurations."
                    )
                else:
                    QMessageBox.critical(self, "Save Error", "Failed to save imported configuration.")
                    
            except Exception as e:
                QMessageBox.critical(
                    self, "Import Error",
                    f"Failed to import account configuration:\n{str(e)}"
                )

    @Slot()
    def export_account_config(self):
        """Export current account configuration to file"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Account Configuration", "bank_accounts_config.json",
            "JSON files (*.json);;All files (*.*)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'w') as f:
                    json.dump(self.bank_accounts_config, f, indent=2)
                
                QMessageBox.information(
                    self, "Export Successful",
                    f"Account configuration exported to:\n{file_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error",
                    f"Failed to export account configuration:\n{str(e)}"
                )

    @Slot()
    def reset_account_config(self):
        """Reset account configuration to defaults"""
        reply = QMessageBox.question(
            self, "Reset Configuration",
            "This will reset all account configurations to defaults.\n"
            "All custom accounts will be lost.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Load default configuration
                default_config = self.account_manager.default_accounts.copy()
                
                # Save defaults
                if self.account_manager.save_accounts(default_config):
                    self.bank_accounts_config = default_config
                    self.refresh_account_selector()
                    
                    QMessageBox.information(
                        self, "Reset Successful",
                        "Account configuration has been reset to defaults."
                    )
                else:
                    QMessageBox.critical(self, "Reset Error", "Failed to save default configuration.")
                    
            except Exception as e:
                QMessageBox.critical(
                    self, "Reset Error",
                    f"Failed to reset account configuration:\n{str(e)}"
                )    

    @Slot(object)
    def on_bank_statement_ready(self, statement):
        """Handle transformed bank statement from upload tab"""
        self.bank_data = statement
        self.status_bar.showMessage(
            f"Bank statement ready: {getattr(statement, 'bank_name', 'Statement')}"
        )
        
        # Switch to ERP tab after statement is ready
        self.tab_widget.setCurrentIndex(1)
        
        QMessageBox.information(
            self,
            "Bank Statement Ready",
            "Bank statement loaded.\n"
            "Please import ERP ledger data and click 'Auto Reconcile' to begin.",
        )
        
        self.update_reconcile_button_state()

    
    @Slot()
    def on_erp_data_ready(self, erp_transactions):
        """Handle ERP data being loaded and ready"""
        self.ledger_data = self._transactions_to_dataframe(erp_transactions)
    
        self.status_bar.showMessage(
            f"ERP data loaded: {len(erp_transactions)} transactions"
        )
        
        # Update reconcile button state
        self.update_reconcile_button_state()
        
        # Log the data loading
        logger.info(f"ERP data ready: {len(erp_transactions)} transactions")
        
        # Optionally show a message to user
        QMessageBox.information(
            self,
            "ERP Data Ready",
            f"ERP data loaded successfully!\n"
            f"Transactions: {len(erp_transactions)}\n"
            "You can now run reconciliation."
        )

    def _transactions_to_dataframe(self, transactions):
        """Convert list of TransactionData to DataFrame"""
        if not transactions:
            return None
        
        data = []
        for txn in transactions:
            data.append({
                'date': txn.date,
                'description': txn.description, 
                'amount': txn.amount,
                'reference': getattr(txn, 'reference', '') or ''
            })
        
        return pd.DataFrame(data)

    def update_reconcile_button_state(self):
        """Enable Auto Reconcile only when both datasets are available."""
        can_reconcile = self.bank_data is not None and self.ledger_data is not None
        self.btn_auto_match.setEnabled(can_reconcile)
    
    @Slot()
    def import_bank_statement(self):
        """Import bank statement using account-specific transformer"""
        # Check if account is selected
        if self.current_bank_account is None:
            QMessageBox.warning(
                self, "No Account Selected", 
                "Please select a bank account first."
            )
            return
        
        account_config = self.account_service.get_current_account_config(self.current_bank_account)
        transformer = self.account_service.get_statement_transformer(self.current_bank_account)
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Import Bank Statement - {self.current_bank_account}", "",
            "Excel files (*.xlsx *.xls);;CSV files (*.csv);;All files (*.*)"
        )
        
        if file_path:
            try:
                # Use UploadViewModel to transform the statement
                self.status_bar.showMessage(
                    f"Processing {Path(file_path).name} using {transformer} transformer..."
                )
                
                template = self.upload_viewmodel.get_template_by_type(transformer)
                if template is None:
                    mapping = {
                        'standard_uk_bank': 'lloyds',
                        'Natwest_bank': 'rbs/natwest',
                        'Charity_bank': 'lloyds',
                    }
                    template = self.upload_viewmodel.get_template_by_type(
                        mapping.get(transformer, transformer)
                    )

                if template is None:
                    raise ValueError(f"No transformer available for {transformer}")

                self.upload_viewmodel.selected_template = template
                if not self.upload_viewmodel.upload_file(file_path):
                    raise ValueError(self.upload_viewmodel.error_message)
                if not self.upload_viewmodel.transform_statement():
                    raise ValueError(self.upload_viewmodel.error_message)

                statement = self.upload_viewmodel.transformed_statement
                self.bank_data = statement.to_dataframe() if statement else None

                self.status_bar.showMessage(
                    f"Bank statement imported: {Path(file_path).name} | "
                    f"Account: {self.current_bank_account}"
                )
                
                self.update_reconcile_button_state()

                logger.info(f"Bank statement imported: {file_path}")
                logger.info(f"Using transformer: {transformer}")
                logger.debug(f"Account config: {account_config}")
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Import Error", 
                    f"Failed to import bank statement:\n{str(e)}"
                )
    
    @Slot()
    def import_ledger_data(self):
        """Import ledger data for the selected account"""
        # Check if account is selected
        if self.current_bank_account is None:
            QMessageBox.warning(
                self, "No Account Selected", 
                "Please select a bank account first."
            )
            return
        
        account_config = self.account_service.get_current_account_config(self.current_bank_account)
        erp_account_code = self.account_service.get_erp_account_code(self.current_bank_account)
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Import Ledger Data - {account_config['erp_account_name']}", "",
            "Excel files (*.xlsx *.xls);;CSV files (*.csv);;All files (*.*)"
        )
        
        if file_path:
            try:
                # Here you would filter ledger data by ERP account code
                self.status_bar.showMessage(
                    f"Processing {Path(file_path).name} for ERP account {erp_account_code}..."
                )
                
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                account_col = None
                for col in df.columns:
                    if col.lower() in ['accountcode', 'account_code', 'erpaccount', 'erp_account_code']:
                        account_col = col
                        break

                if account_col:
                    self.ledger_data = df[df[account_col].astype(str) == str(erp_account_code)]
                else:
                    self.ledger_data = df

                self.status_bar.showMessage(
                    f"Ledger data imported: {Path(file_path).name} | "
                    f"ERP Account: {erp_account_code}"
                )
                
                self.update_reconcile_button_state()
                logger.info(f"Ledger data imported: {file_path}")
                logger.info(f"ERP account code: {erp_account_code}")
                logger.info(f"ERP account name: {account_config['erp_account_name']}")
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Import Error", 
                    f"Failed to import ledger data:\n{str(e)}"
                )

    @Slot()
    def import_training_data(self):
        """Import training data"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Training Data", "",
            "Excel files (*.xlsx *.xls);;CSV files (*.csv);;All files (*.*)"
        )

    @Slot()
    def run_reconciliation(self):
        """Run the reconciliation process for the selected account"""
        # Check if account is selected
        if self.current_bank_account is None:
            QMessageBox.warning(
                self, "No Account Selected", 
                "Please select a bank account first."
            )
            return
        
        account_config = self.account_service.get_current_account_config(self.current_bank_account)
        
        # Check if data has been imported
        if self.bank_data is None or self.ledger_data is None:
            QMessageBox.warning(
                self, "Missing Data", 
                "Please import both bank statement and ledger data first."
            )
            return
        
        self.status_bar.showMessage(f"Running reconciliation for {self.current_bank_account}...")
        
        try:
            bank_tx = self._df_to_transactions(self.bank_data)
            erp_tx = self._df_to_transactions(self.ledger_data)
            self.matching_viewmodel.load_transactions(bank_tx, erp_tx)
            matches = self.matching_viewmodel.run_auto_match()
            self.reconciliation_results = matches
            
            QMessageBox.information(
                self, "Reconciliation Started", 
                f"Reconciliation process started for:\n"
                f"Account: {self.current_bank_account}\n"
                f"Currency: {account_config['currency']}\n"
                f"ERP Account: {account_config['erp_account_code']}"
            )
            
            logger.info(f"Running reconciliation for account: {self.current_bank_account}")
            logger.debug(f"Account configuration: {account_config}")
            
        except Exception as e:
            QMessageBox.critical(
                self, "Reconciliation Error", 
                f"Failed to run reconciliation:\n{str(e)}"
            )
    
    @Slot()
    def train_ai_model(self):
        """Train the AI model"""
        self.status_bar.showMessage("Training AI model...")
        
        try:
            self.matching_viewmodel.train_model()
            QMessageBox.information(self, "AI Training", "AI model training started!")
            logger.info("Training AI model")
        except Exception as e:
            QMessageBox.critical(
                self, "Training Error",
                f"Failed to train model:\n{str(e)}"
            )

    
    @Slot()
    def review_low_confidence(self):
        """Review low confidence matches"""
        matches = self.reconciliation_results or []
        threshold = getattr(self.settings, 'medium_confidence_threshold', 0.6) if self.settings else 0.6
        low_matches = [m for m in matches if m.confidence_score < threshold]
        if not low_matches:
            QMessageBox.information(self, "Review", "No low confidence matches to review")
            return

        details = "\n".join(
            f"{m.bank_transaction.description} ↔ {m.erp_transaction.description} ({m.confidence_score:.2f})"
            for m in low_matches[:10]
        )
        QMessageBox.information(
            self,
            "Low Confidence Matches",
            f"The following matches require review:\n{details}"
        )
        logger.info("Reviewing low confidence matches")
    
    @Slot()
    def export_ai_model(self):
        """Export the AI model"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export AI Model", "ai_model.pkl",
            "Pickle files (*.pkl);;All files (*.*)"
        )
        if file_path:
            self.status_bar.showMessage(f"AI model exported to: {Path(file_path).name}")
            logger.info(f"AI model exported: {file_path}")
    
    @Slot()
    def export_report(self):
        """Export reconciliation report"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Report", "reconciliation_report.xlsx",
            "Excel files (*.xlsx);;PDF files (*.pdf);;CSV files (*.csv);;All files (*.*)"
        )
        if file_path:
            self.status_bar.showMessage(f"Report exported to: {Path(file_path).name}")
            logger.info(f"Report exported: {file_path}")