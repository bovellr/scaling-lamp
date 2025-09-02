# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# MAIN WINDOW
# ============================================================================

# views/enhanced_main_window.py
"""
Corrected Enhanced main window that properly integrates with existing architecture
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QStatusBar, QLabel, QComboBox, QMessageBox, QScrollArea,
                            QProgressBar, QMenu, QPushButton, QGroupBox)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QAction
from pathlib import Path
import logging
from typing import List, Optional, Dict, Any

# Import services
from services.data_service import DataService
from services.import_service import EnhancedImportService

# Import enhanced widgets
from views.widgets.enhanced_file_upload_widget import EnhancedFileUploadWidget
from views.widgets.streamlined_action_buttons_widget import StreamlinedActionButtonsWidget
from views.widgets.enhanced_transaction_tables_widget import EnhancedTransactionTablesWidget

# Import existing widgets (keep what works)
from views.widgets.erp_data_widget import ERPDataWidget
from views.widgets.filters_widget import FiltersWidget
from views.widgets.ai_results_widget import AiResultsWidget
from views.widgets.summary_cards_widget import SummaryCardsWidget
from views.widgets.reports_widget import ReportsWidget

# Import dialogs
from views.dialogs.low_confidence_review_dialog import LowConfidenceReviewDialog
from views.dialogs.dialog_manager import DialogManager

# Import ViewModels
from viewmodels.matching_viewmodel import MatchingViewModel
from viewmodels.upload_viewmodel import UploadViewModel
from viewmodels.erp_database_viewmodel import ERPDatabaseViewModel

# Import models
from models.data_models import TransactionData, TransactionMatch

logger = logging.getLogger(__name__)

class EnhancedMainWindow(QMainWindow):
    """Enhanced main window with proper integration to existing architecture"""
    
    def __init__(self, settings=None, event_bus=None):
        super().__init__()
        self.settings = settings
        self.event_bus = event_bus
        
        # Initialize services (single source of truth)
        self.data_service = DataService()
        
        # Initialize existing ViewModels (keep what works)
        self.upload_viewmodel = UploadViewModel()
        self.erp_viewmodel = ERPDatabaseViewModel()
        self.matching_viewmodel = MatchingViewModel()
        
        # Initialize import service with existing ViewModels
        self.import_service = EnhancedImportService(
            self.data_service, 
            self.upload_viewmodel,
            self.erp_viewmodel
        )
        
        # Initialize dialog manager
        self.dialog_manager = DialogManager(self)
        
        # State tracking
        self.current_bank_account: Optional[str] = None
        
        self._setup_ui()
        self._connect_services()
        
        logger.info("Enhanced main window initialized")
    
    def _setup_ui(self):
        """Setup the enhanced UI with improved architecture"""
        self.setWindowTitle("Bank Reconciliation AI - Enhanced")
        self.setMinimumSize(1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Build menu
        self._build_enhanced_menu()
        
        # Create header with account selector
        self._create_enhanced_header(main_layout)
        
        # Create tabbed interface
        self._create_enhanced_tabs(main_layout)
        
        # Setup status bar
        self._setup_enhanced_status_bar()
        
        # Apply enhanced styling
        self._apply_enhanced_styles()
    
    def _create_enhanced_header(self, parent_layout):
        """Create enhanced header with better account management"""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # App title and version
        title_label = QLabel("Bank Reconciliation AI")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        version_label = QLabel("v2.0 Enhanced")
        version_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        
        title_layout = QVBoxLayout()
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        
        # Account selector (enhanced)
        account_layout = QVBoxLayout()
        account_label = QLabel("Bank Account:")
        account_label.setStyleSheet("font-weight: bold; color: #34495e;")
        
        self.account_combo = QComboBox()
        self.account_combo.addItems(["Select Account...", "Main Current Account", "Savings Account", "Business Account"])
        self.account_combo.currentTextChanged.connect(self._on_account_changed)
        
        # Enhanced account combo styling
        self.account_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 15px;
                border: 2px solid #3498db;
                border-radius: 8px;
                background-color: white;
                font-size: 13px;
                font-weight: 500;
                min-width: 200px;
            }
            QComboBox:hover {
                border-color: #2980b9;
                background-color: #ecf0f1;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                width: 14px;
                height: 14px;
            }
        """)
        
        account_layout.addWidget(account_label)
        account_layout.addWidget(self.account_combo)
        
        # Status indicators
        self.data_status_label = QLabel("Status: No data loaded")
        self.data_status_label.setStyleSheet("""
            QLabel {
                padding: 8px 12px;
                background-color: #f39c12;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        
        # Layout header components
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addLayout(account_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.data_status_label)
        
        # Enhanced header styling
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ecf0f1, stop:1 #bdc3c7);
                border-radius: 10px;
                margin: 5px;
            }
        """)
        
        parent_layout.addWidget(header_widget)
    
    def _create_enhanced_tabs(self, parent_layout):
        """Create enhanced tabbed interface"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)
        
        # Enhanced tab styling
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                margin-top: -1px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d5dbdb;
            }
        """)
        
        # Create enhanced tabs
        self._create_enhanced_data_import_tab()
        self._create_enhanced_erp_tab()
        self._create_enhanced_reconciliation_tab()
        self._create_enhanced_reports_tab()
        
        parent_layout.addWidget(self.tab_widget)
    
    def _create_enhanced_data_import_tab(self):
        """Create enhanced data import tab with dual preview"""
        # Use the enhanced file upload widget
        self.enhanced_upload_widget = EnhancedFileUploadWidget(
            self.data_service, self.import_service
        )
        
        # Connect enhanced widget signals
        self.enhanced_upload_widget.both_sources_ready.connect(self._on_both_sources_ready)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.enhanced_upload_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.tab_widget.addTab(scroll_area, "📁 Data Import & Preview")
    
    def _create_enhanced_erp_tab(self):
        """Create enhanced ERP tab (kept as-is since it's well designed)"""
        self.erp_widget = ERPDataWidget()
        # Connect the existing signal properly
        if hasattr(self.erp_widget, 'erp_data_loaded'):
            self.erp_widget.erp_data_loaded.connect(self._on_erp_data_from_widget)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.erp_widget)
        scroll_area.setWidgetResizable(True)
        
        self.tab_widget.addTab(scroll_area, "🏢 ERP Transactions")
    
    def _create_matching_reconciliation_tab(self):
        """REPLACE this entire method with the version below"""
        # Main widget for this tab
        matching_widget = QWidget()
        layout = QVBoxLayout(matching_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # STREAMLINED Action buttons section (NO duplicate imports)
        action_group = QGroupBox("Reconciliation Operations")
        action_layout = QVBoxLayout(action_group)
        
        # Row 1: Primary reconciliation button
        row1 = QHBoxLayout()
        self.btn_auto_match = QPushButton("Auto Reconcile")
        self.btn_auto_match.setEnabled(False)
        self.btn_auto_match.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.btn_auto_match.clicked.connect(self.run_reconciliation)
        
        row1.addStretch()
        row1.addWidget(self.btn_auto_match)
        row1.addStretch()
        
        # Row 2: Training buttons
        row2 = QHBoxLayout()
        self.btn_train_model = QPushButton("Train AI Model")
        self.btn_import_training = QPushButton("Import Training Data")
        self.btn_train_model.clicked.connect(self.train_ai_model)
        self.btn_import_training.clicked.connect(self.import_training_data)
        
        row2.addWidget(self.btn_train_model)
        row2.addWidget(self.btn_import_training)
        row2.addStretch()
        
        action_layout.addLayout(row1)
        action_layout.addLayout(row2)
        layout.addWidget(action_group)

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
        
        
        self.transaction_tables = EnhancedTransactionTablesWidget()
        
        # Connect enhanced table signals
        self.transaction_tables.review_requested.connect(self._open_review_dialog)
        self.transaction_tables.match_action_requested.connect(self._handle_match_action)
        
        layout.addWidget(self.transaction_tables)
        
        # Keep your existing table references for backward compatibility
        # (Enhanced widget doesn't have these, but we'll add dummy properties)
        self.table_book = None  # Legacy reference
        self.table_bank = None  # Legacy reference
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(matching_widget)
        scroll_area.setWidgetResizable(True)

        # Add to tab widget
        self.tab_widget.addTab(scroll_area, "Matching & Reconciliation")
    
    def _create_enhanced_reports_tab(self):
        """Create enhanced reports tab"""
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Summary cards
        self.summary_cards = SummaryCardsWidget()
        layout.addWidget(self.summary_cards)
        
        # Reports widget
        self.reports_widget = ReportsWidget()
        layout.addWidget(self.reports_widget)
        
        layout.addStretch()
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(reports_widget)
        scroll_area.setWidgetResizable(True)
        
        self.tab_widget.addTab(scroll_area, "📊 Reports & Analytics")
    
    def _build_enhanced_menu(self):
        """Build enhanced menu system"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Data submenu
        data_submenu = file_menu.addMenu("Data Management")
        self._add_menu_action(data_submenu, "Clear All Data", self._clear_all_data, "Ctrl+Alt+C")
        self._add_menu_action(data_submenu, "Export Combined Data", self._export_combined_data)
        data_submenu.addSeparator()
        self._add_menu_action(data_submenu, "Import Settings", self._import_settings)
        self._add_menu_action(data_submenu, "Export Settings", self._export_settings)
        
        file_menu.addSeparator()
        self._add_menu_action(file_menu, "Exit", self.close, "Ctrl+Q")
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        self._add_menu_action(tools_menu, "Data Validation", self._validate_data)
        self._add_menu_action(tools_menu, "Matching Statistics", self._show_matching_stats)
        tools_menu.addSeparator()
        self._add_menu_action(tools_menu, "Threshold Settings", self.dialog_manager.open_threshold_dialog)
        self._add_menu_action(tools_menu, "ML Model Settings", self._open_ml_settings)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        self._add_menu_action(view_menu, "Refresh All Data", self._refresh_all_data, "F5")
        self._add_menu_action(view_menu, "Reset Window Layout", self._reset_layout)
        view_menu.addSeparator()
        self._add_menu_action(view_menu, "Show Data Summary", self._show_data_summary)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        self._add_menu_action(help_menu, "User Guide", self._show_user_guide)
        self._add_menu_action(help_menu, "Keyboard Shortcuts", self._show_shortcuts)
        help_menu.addSeparator()
        self._add_menu_action(help_menu, "About", self._show_about)
    
    def _add_menu_action(self, menu, text: str, slot, shortcut: str = None):
        """Helper to add menu action with optional shortcut"""
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action
    
    def _setup_enhanced_status_bar(self):
        """Setup enhanced status bar with multiple indicators"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Main status message
        self.status_bar.showMessage("Ready - Enhanced Bank Reconciliation System")
        
        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Data status indicators
        self.bank_status_indicator = QLabel("Bank: ❌")
        self.erp_status_indicator = QLabel("ERP: ❌")
        self.reconciliation_status_indicator = QLabel("Reconciled: ❌")
        
        self.status_bar.addPermanentWidget(self.bank_status_indicator)
        self.status_bar.addPermanentWidget(self.erp_status_indicator)
        self.status_bar.addPermanentWidget(self.reconciliation_status_indicator)
    
    def _apply_enhanced_styles(self):
        """Apply enhanced application-wide styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #495057;
                font-size: 13px;
            }
            
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:pressed {
                background-color: #004085;
            }
            
            QPushButton:disabled {
                background-color: #6c757d;
                color: #dee2e6;
            }
            
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
            
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f8f9fa;
            }
            
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
    
    def _connect_services(self):
        """Connect to all services and handle their signals"""
        # Data service connections
        self.data_service.bank_data_loaded.connect(self._on_bank_data_service_update)
        self.data_service.erp_data_loaded.connect(self._on_erp_data_service_update)
        self.data_service.reconciliation_completed.connect(self._on_reconciliation_service_update)
        self.data_service.data_cleared.connect(self._on_data_cleared)
        
        # Import service connections
        self.import_service.import_started.connect(self._on_import_started)
        self.import_service.import_completed.connect(self._on_import_completed)
        self.import_service.import_failed.connect(self._on_import_failed)
    
    # ================================================================================================
    # EVENT HANDLERS - Properly integrated with existing architecture
    # ================================================================================================
    
    @Slot(str)
    def _on_account_changed(self, account_name: str):
        """Handle account selection change"""
        if account_name == "Select Account...":
            self.current_bank_account = None
            self._update_account_dependent_features(False)
            return
            
        self.current_bank_account = account_name
        self._update_account_dependent_features(True)
        
        # Update status
        self.status_bar.showMessage(f"Account selected: {account_name}")
        
        # Clear previous data when switching accounts
        if self.data_service.bank_statement or self.data_service.erp_transactions:
            reply = QMessageBox.question(
                self, "Clear Data",
                "Switching accounts will clear current data. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.data_service.clear_data('all')
        
        logger.info(f"Account changed to: {account_name}")
    
    def _update_account_dependent_features(self, enabled: bool):
        """Enable/disable features based on account selection"""
        # Update streamlined actions
        if hasattr(self, 'streamlined_actions'):
            self.streamlined_actions.setEnabled(enabled)
        
        # Update data status
        if enabled:
            self.data_status_label.setText("Status: Account selected, ready for data")
            self.data_status_label.setStyleSheet("""
                QLabel {
                    padding: 8px 12px;
                    background-color: #28a745;
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
        else:
            self.data_status_label.setText("Status: Select an account first")
            self.data_status_label.setStyleSheet("""
                QLabel {
                    padding: 8px 12px;
                    background-color: #f39c12;
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
    
    @Slot(object, object)
    def _on_both_sources_ready(self, bank_statement, erp_transactions):
        """Handle when both data sources are ready"""
        self.status_bar.showMessage("✓ Both data sources loaded - Ready for reconciliation!")
        
        # Update streamlined actions
        self.streamlined_actions.set_data_ready(True)
        
        # Update status indicators
        self.bank_status_indicator.setText("Bank: ✅")
        self.erp_status_indicator.setText("ERP: ✅")
        
        # Switch to reconciliation tab
        QTimer.singleShot(1000, lambda: self.tab_widget.setCurrentIndex(2))
        
        logger.info("Both data sources ready for reconciliation")
    
    @Slot(object)
    def _on_bank_data_service_update(self, statement):
        """Handle bank data service update"""
        self.bank_status_indicator.setText("Bank: ✅")
        count = len(statement.transactions) if statement else 0
        self.status_bar.showMessage(f"Bank data loaded: {count} transactions")
    
    @Slot(list)
    def _on_erp_data_service_update(self, transactions):
        """Handle ERP data service update"""
        self.erp_status_indicator.setText("ERP: ✅")
        self.status_bar.showMessage(f"ERP data loaded: {len(transactions)} transactions")
    
    @Slot(list)
    def _on_erp_data_from_widget(self, transactions):
        """Handle ERP data from the ERP widget (existing pattern)"""
        # This maintains compatibility with your existing ERP widget
        self.data_service.set_erp_data(transactions)
    
    @Slot(list)
    def _on_reconciliation_service_update(self, matches):
        """Handle reconciliation completion"""
        self.reconciliation_status_indicator.setText("Reconciled: ✅")
        self.status_bar.showMessage(f"Reconciliation completed: {len(matches)} matches found")
        
        # Populate enhanced transaction tables
        self._populate_enhanced_tables(matches)
    
    @Slot(str)
    def _on_data_cleared(self, data_type):
        """Handle data clearing"""
        if data_type in ['bank', 'all']:
            self.bank_status_indicator.setText("Bank: ❌")
        if data_type in ['erp', 'all']:
            self.erp_status_indicator.setText("ERP: ❌")
        if data_type in ['reconciliation', 'all']:
            self.reconciliation_status_indicator.setText("Reconciled: ❌")
        
        self.status_bar.showMessage(f"Data cleared: {data_type}")
        
        # Update streamlined actions
        self.streamlined_actions.set_data_ready(
            self.data_service.is_ready_for_reconciliation
        )
    
    def _populate_enhanced_tables(self, matches: List[TransactionMatch]):
        """Populate enhanced transaction tables with reconciliation results"""
        # Get unmatched transactions
        matched_bank_ids = {getattr(m.bank_transaction, 'id', id(m.bank_transaction)) for m in matches}
        matched_erp_ids = {getattr(m.erp_transaction, 'id', id(m.erp_transaction)) for m in matches}
        
        # Get all transactions
        all_bank = self.data_service.bank_statement.transactions if self.data_service.bank_statement else []
        all_erp = self.data_service.erp_transactions
        
        # Find unmatched
        unmatched_bank = [t for t in all_bank if getattr(t, 'id', id(t)) not in matched_bank_ids]
        unmatched_erp = [t for t in all_erp if getattr(t, 'id', id(t)) not in matched_erp_ids]
        
        # Populate enhanced tables
        self.enhanced_transaction_tables.populate_reconciliation_results(
            matches, unmatched_bank, unmatched_erp
        )
        
        # Update AI results widget
        self._update_ai_results_display(matches)
    
    def _update_ai_results_display(self, matches: List[TransactionMatch]):
        """Update AI results display"""
        high_confidence = len([m for m in matches if m.confidence_score >= 0.8])
        medium_confidence = len([m for m in matches if 0.5 <= m.confidence_score < 0.8])
        low_confidence = len([m for m in matches if m.confidence_score < 0.5])
        
        # Update AI results widget (if it has these methods)
        if hasattr(self.ai_results_widget, 'update_results'):
            self.ai_results_widget.update_results({
                'high_confidence': high_confidence,
                'medium_confidence': medium_confidence,
                'low_confidence': low_confidence,
                'total_matches': len(matches)
            })
    
    # ================================================================================================
    # ACTION HANDLERS - Integrated with existing ViewModels
    # ================================================================================================
    
    @Slot()
    def _train_ai_model(self):
        """Train AI model using existing MatchingViewModel"""
        if not self.data_service.is_ready_for_reconciliation:
            QMessageBox.warning(self, "Training Error", 
                              "Both bank and ERP data must be loaded before training.")
            return
        
        self.streamlined_actions.set_operation_in_progress("AI Model Training", True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        try:
            # Load transactions into existing matching viewmodel
            bank_transactions = self.data_service.bank_statement.transactions
            erp_transactions = self.data_service.erp_transactions
            
            self.matching_viewmodel.load_transactions(bank_transactions, erp_transactions)
            
            # Train model using existing logic
            self.matching_viewmodel.train_model()
            
            QMessageBox.information(self, "Training Complete", 
                                  "AI model training completed successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Training Error", f"Training failed: {str(e)}")
            logger.error(f"AI model training failed: {e}")
        finally:
            self.streamlined_actions.set_operation_in_progress("AI Model Training", False)
            self.progress_bar.setVisible(False)
    
    @Slot()
    def _import_training_data(self):
        """Import training data using existing import service"""
        if self.import_service.import_training_data(self):
            QMessageBox.information(self, "Training Data", "Training data imported successfully!")
    
    @Slot()
    def _run_reconciliation(self):
        """Run reconciliation using existing MatchingViewModel"""
        if not self.data_service.is_ready_for_reconciliation:
            QMessageBox.warning(self, "Reconciliation Error",
                              "Both bank and ERP data must be loaded before reconciliation.")
            return
        
        self.streamlined_actions.set_operation_in_progress("Auto Reconciliation", True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        try:
            # Load data into existing matching viewmodel
            bank_transactions = self.data_service.bank_statement.transactions
            erp_transactions = self.data_service.erp_transactions
            
            self.matching_viewmodel.load_transactions(bank_transactions, erp_transactions)
            
            # Run matching using existing logic
            confidence_threshold = 0.5  # Could get this from filters widget
            if hasattr(self.filters_widget, 'get_confidence_threshold'):
                confidence_threshold = self.filters_widget.get_confidence_threshold()
            
            matches = self.matching_viewmodel.run_auto_match(confidence_threshold)
            
            # Store results in data service
            self.data_service.set_reconciliation_results(matches)
            
            QMessageBox.information(self, "Reconciliation Complete",
                                  f"Reconciliation completed!\n"
                                  f"Found {len(matches)} potential matches.")
            
        except Exception as e:
            QMessageBox.critical(self, "Reconciliation Error", f"Reconciliation failed: {str(e)}")
            logger.error(f"Reconciliation failed: {e}")
        finally:
            self.streamlined_actions.set_operation_in_progress("Auto Reconciliation", False)
            self.progress_bar.setVisible(False)
    
    @Slot(list)
    def _open_review_dialog(self, matches: List[TransactionMatch]):
        """Open review dialog for low confidence matches"""
        if not matches:
            QMessageBox.information(self, "Review", "No matches require review.")
            return
        
        review_dialog = LowConfidenceReviewDialog(matches, self)
        review_dialog.matches_reviewed.connect(self._on_matches_reviewed)
        review_dialog.review_completed.connect(self._on_review_completed)
        
        if review_dialog.exec() == review_dialog.Accepted:
            logger.info(f"Review dialog completed for {len(matches)} matches")
    
    @Slot()
    def _review_low_confidence_matches(self):
        """Review low confidence matches from AI results"""
        matches = self.data_service.reconciliation_results
        low_confidence_matches = [m for m in matches if m.confidence_score < 0.5]
        
        if low_confidence_matches:
            self._open_review_dialog(low_confidence_matches)
        else:
            QMessageBox.information(self, "Review", "No low confidence matches found.")
    
    @Slot(list)
    def _on_matches_reviewed(self, reviewed_matches: List[TransactionMatch]):
        """Handle reviewed matches"""
        # Update the matches in data service
        all_matches = self.data_service.reconciliation_results
        
        # Update matches with review results
        for reviewed_match in reviewed_matches:
            for i, match in enumerate(all_matches):
                if (getattr(match.bank_transaction, 'id', id(match.bank_transaction)) == 
                    getattr(reviewed_match.bank_transaction, 'id', id(reviewed_match.bank_transaction)) and 
                    getattr(match.erp_transaction, 'id', id(match.erp_transaction)) == 
                    getattr(reviewed_match.erp_transaction, 'id', id(reviewed_match.erp_transaction))):
                    all_matches[i] = reviewed_match
                    break
        
        # Update data service
        self.data_service.set_reconciliation_results(all_matches)
        
        self.status_bar.showMessage(f"Reviewed {len(reviewed_matches)} matches")
    
    @Slot()
    def _on_review_completed(self):
        """Handle review completion"""
        self.status_bar.showMessage("Match review completed")
        # Refresh tables to show updated match statuses
        if self.data_service.reconciliation_results:
            self._populate_enhanced_tables(self.data_service.reconciliation_results)
    
    @Slot(object, str)
    def _handle_match_action(self, match_or_transaction, action: str):
        """Handle various match actions"""
        logger.info(f"Handling match action: {action}")
        
        if action == "view":
            self._view_match_details(match_or_transaction)
        elif action == "edit":
            self._edit_match(match_or_transaction)
        elif action == "reject":
            self._reject_match(match_or_transaction)
        elif action == "accept":
            self._accept_match(match_or_transaction)
        elif action == "comment":
            self._add_match_comment(match_or_transaction)
        elif action == "manual_match":
            self._manual_match_transaction(match_or_transaction)
        elif action == "exception":
            self._mark_as_exception(match_or_transaction)
    
    def _view_match_details(self, match):
        """View detailed match information"""
        QMessageBox.information(self, "Match Details", f"Viewing details for match with confidence: {match.confidence_score:.3f}")
    
    def _edit_match(self, match):
        """Edit match details"""
        QMessageBox.information(self, "Edit Match", "Match editing dialog would open here")
    
    def _reject_match(self, match):
        """Reject a match"""
        from models.data_models import MatchStatus
        match.status = MatchStatus.REJECTED
        self._refresh_transaction_tables()
        self.status_bar.showMessage("Match rejected")
    
    def _accept_match(self, match):
        """Accept a match"""
        from models.data_models import MatchStatus
        match.status = MatchStatus.MATCHED
        self._refresh_transaction_tables()
        self.status_bar.showMessage("Match accepted")
    
    def _add_match_comment(self, match):
        """Add comment to match"""
        QMessageBox.information(self, "Add Comment", "Comment dialog would open here")
    
    def _manual_match_transaction(self, transaction):
        """Manually match a transaction"""
        QMessageBox.information(self, "Manual Match", "Manual matching dialog would open here")
    
    def _mark_as_exception(self, transaction):
        """Mark transaction as exception"""
        QMessageBox.information(self, "Exception", f"Transaction marked as exception: {transaction.description}")
    
    def _refresh_transaction_tables(self):
        """Refresh transaction tables after changes"""
        if self.data_service.reconciliation_results:
            self._populate_enhanced_tables(self.data_service.reconciliation_results)
    
    # ================================================================================================
    # IMPORT/EXPORT AND SERVICE HANDLERS
    # ================================================================================================
    
    @Slot(str)
    def _on_import_started(self, import_type):
        """Handle import start"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_bar.showMessage(f"Importing {import_type} data...")
    
    @Slot(object)
    def _on_import_completed(self, result):
        """Handle import completion"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Import completed successfully")
    
    @Slot(str)
    def _on_import_failed(self, error_message):
        """Handle import failure"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Import failed: {error_message}")
        QMessageBox.critical(self, "Import Error", f"Import failed:\n{error_message}")
    
    # ================================================================================================
    # MENU ACTIONS - Placeholder implementations
    # ================================================================================================
    
    @Slot()
    def _clear_all_data(self):
        """Clear all application data"""
        reply = QMessageBox.question(
            self, "Clear All Data",
            "Are you sure you want to clear all loaded data?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.data_service.clear_data('all')
            if hasattr(self, 'enhanced_transaction_tables'):
                self.enhanced_transaction_tables._clear_all_results()
            self.status_bar.showMessage("All data cleared")
    
    @Slot()
    def _export_combined_data(self):
        """Export combined data"""
        QMessageBox.information(self, "Export", "Combined data export functionality")
    
    @Slot()
    def _validate_data(self):
        """Validate loaded data"""
        summary = self.data_service.get_data_summary()
        
        validation_report = f"""
        DATA VALIDATION REPORT
        =====================
        
        Bank Data: {'✓ Valid' if summary['bank_loaded'] else '✗ Not Loaded'}
        - Transactions: {summary['bank_count']}
        - Date Range: {summary.get('bank_date_range', 'N/A')}
        
        ERP Data: {'✓ Valid' if summary['erp_loaded'] else '✗ Not Loaded'}  
        - Transactions: {summary['erp_count']}
        - Date Range: {summary.get('erp_date_range', 'N/A')}
        
        Reconciliation Status: {'✓ Ready' if summary['ready_for_reconciliation'] else '✗ Not Ready'}
        """
        
        QMessageBox.information(self, "Data Validation", validation_report)
    
    @Slot()
    def _show_matching_stats(self):
        """Show matching statistics"""
        if not self.data_service.reconciliation_results:
            QMessageBox.information(self, "Statistics", "No reconciliation results available.")
            return
        
        matches = self.data_service.reconciliation_results
        high = len([m for m in matches if m.confidence_score >= 0.8])
        medium = len([m for m in matches if 0.5 <= m.confidence_score < 0.8])  
        low = len([m for m in matches if m.confidence_score < 0.5])
        
        stats = f"""
        MATCHING STATISTICS
        ==================
        
        Total Matches: {len(matches)}
        
        By Confidence Level:
        - High (≥80%): {high}
        - Medium (50-79%): {medium}
        - Low (<50%): {low}
        
        Overall Accuracy: {(high / len(matches) * 100):.1f}%
        """
        
        QMessageBox.information(self, "Matching Statistics", stats)
    
    @Slot()
    def _refresh_all_data(self):
        """Refresh all loaded data"""
        self.status_bar.showMessage("Refreshing all data...")
        QTimer.singleShot(1000, lambda: self.status_bar.showMessage("Data refreshed"))
    
    @Slot()
    def _show_data_summary(self):
        """Show comprehensive data summary"""
        summary = self.data_service.get_data_summary()
        
        summary_text = f"""
        COMPREHENSIVE DATA SUMMARY
        =========================
        
        Bank Statement:
        - Loaded: {'Yes' if summary['bank_loaded'] else 'No'}
        - Transaction Count: {summary['bank_count']}
        - Total Amount: {summary.get('bank_total_amount', 0):,.2f}
        - Date Range: {summary.get('bank_date_range', 'N/A')}
        - Currency: {summary.get('bank_currency', 'Unknown')}
        
        ERP Data:
        - Loaded: {'Yes' if summary['erp_loaded'] else 'No'}
        - Transaction Count: {summary['erp_count']}
        - Total Amount: {summary.get('erp_total_amount', 0):,.2f}
        - Date Range: {summary.get('erp_date_range', 'N/A')}
        
        Reconciliation:
        - Status: {'Ready' if summary['ready_for_reconciliation'] else 'Not Ready'}
        - Completed Matches: {summary['reconciliation_count']}
        
        Current Account: {self.current_bank_account or 'None Selected'}
        """
        
        QMessageBox.information(self, "Data Summary", summary_text)
    
    @Slot()
    def _show_about(self):
        """Show about dialog"""
        about_text = """
        <h3>Enhanced Bank Reconciliation AI</h3>
        <p><b>Version:</b> 2.0 Enhanced</p>
        <p><b>Description:</b> Advanced bank reconciliation system with AI-powered matching</p>
        
        <p><b>Key Features:</b></p>
        <ul>
        <li>Dual data preview (Bank & ERP)</li>
        <li>AI-powered transaction matching</li>
        <li>Low confidence match review</li>
        <li>Comprehensive reconciliation reporting</li>
        <li>Enhanced user interface</li>
        </ul>
        
        <p><b>Architecture:</b> Clean MVVM with centralized services</p>
        <p><b>Technology:</b> PySide6, Python, Machine Learning</p>
        """
        
        QMessageBox.about(self, "About Enhanced Bank Reconciliation AI", about_text)
    
    # Placeholder implementations for other menu actions
    @Slot()
    def _import_settings(self):
        QMessageBox.information(self, "Settings", "Import settings functionality")
    
    @Slot()
    def _export_settings(self):
        QMessageBox.information(self, "Settings", "Export settings functionality")
    
    @Slot()
    def _open_ml_settings(self):
        QMessageBox.information(self, "ML Settings", "ML model settings dialog")
    
    @Slot()
    def _reset_layout(self):
        QMessageBox.information(self, "Layout", "Window layout reset")
    
    @Slot()
    def _show_user_guide(self):
        QMessageBox.information(self, "User Guide", "User guide would open here")
    
    @Slot()
    def _show_shortcuts(self):
        shortcuts = """
        KEYBOARD SHORTCUTS
        ==================
        
        File Operations:
        Ctrl+Q - Exit application
        Ctrl+Alt+C - Clear all data
        F5 - Refresh all data
        
        Navigation:
        Ctrl+1 - Data Import tab
        Ctrl+2 - ERP Transactions tab
        Ctrl+3 - Reconciliation tab
        Ctrl+4 - Reports tab
        
        Operations:
        Ctrl+R - Run reconciliation
        Ctrl+T - Train AI model
        Ctrl+L - Review low confidence
        """
        
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts)