# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# ENHANCED FILE UPLOAD WIDGET
# ============================================================================

# views/widgets/enhanced_file_upload_widget.py
"""
Fixed Enhanced file upload widget with correct interface
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
                            QLabel, QComboBox, QTextEdit, QProgressBar, QTableWidget,
                            QTableWidgetItem, QTabWidget, QFrame, QSplitter, QMessageBox)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont
from typing import Optional
import pandas as pd

from services.data_service import DataService
from services.import_service import EnhancedImportService

class EnhancedFileUploadWidget(QWidget):
    """Enhanced file upload widget with dual preview capabilities and correct interface"""
    
    # Signals
    bank_data_ready = Signal(object)
    erp_data_ready = Signal(object)
    both_sources_ready = Signal(object, object)
    
    def __init__(self, data_service: DataService, import_service: EnhancedImportService, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.import_service = import_service
        self._setup_ui()
        self._connect_services()
    
    def _setup_ui(self):
        """Setup the enhanced UI with dual preview"""
        layout = QVBoxLayout(self)
        
        # Header
        self._create_header(layout)
        
        # File upload section
        self._create_upload_section(layout)
        
        # Enhanced preview section with tabs
        self._create_preview_section(layout)
        
        # Action buttons
        self._create_action_buttons(layout)
    
    def _create_header(self, parent_layout):
        """Create header section"""
        header_label = QLabel("Data Import & Preview")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        parent_layout.addWidget(header_label)
    
    def _create_upload_section(self, parent_layout):
        """Create file upload section"""
        upload_group = QGroupBox("File Upload")
        upload_layout = QHBoxLayout(upload_group)
        
        # Bank upload
        bank_section = QVBoxLayout()
        bank_label = QLabel("Bank Statement")
        bank_label.setStyleSheet("font-weight: bold;")
        self.bank_file_label = QLabel("No file selected")
        self.bank_upload_btn = QPushButton("Upload Bank Statement")
        self.bank_upload_btn.clicked.connect(self._upload_bank_file)
        
        bank_section.addWidget(bank_label)
        bank_section.addWidget(self.bank_file_label)
        bank_section.addWidget(self.bank_upload_btn)
        
        # ERP upload
        erp_section = QVBoxLayout()
        erp_label = QLabel("ERP Data")
        erp_label.setStyleSheet("font-weight: bold;")
        self.erp_file_label = QLabel("No file selected")
        self.erp_upload_btn = QPushButton("Upload ERP Data")
        self.erp_upload_btn.clicked.connect(self._upload_erp_file)
        
        erp_section.addWidget(erp_label)
        erp_section.addWidget(self.erp_file_label)
        erp_section.addWidget(self.erp_upload_btn)
        
        upload_layout.addLayout(bank_section)
        upload_layout.addWidget(self._create_separator())
        upload_layout.addLayout(erp_section)
        
        parent_layout.addWidget(upload_group)
    
    def _create_separator(self) -> QFrame:
        """Create a vertical separator"""
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        return separator
    
    def _create_preview_section(self, parent_layout):
        """Create enhanced preview section with tabs"""
        preview_group = QGroupBox("Data Preview & Summary")
        preview_layout = QVBoxLayout(preview_group)
        
        # Summary cards
        self._create_summary_cards(preview_layout)
        
        # Tabbed preview
        self.preview_tabs = QTabWidget()
        
        # Bank preview tab
        self.bank_preview_tab = self._create_bank_preview_tab()
        self.preview_tabs.addTab(self.bank_preview_tab, "Bank Data")
        
        # ERP preview tab
        self.erp_preview_tab = self._create_erp_preview_tab()
        self.preview_tabs.addTab(self.erp_preview_tab, "ERP Data")
        
        # Data comparison tab
        self.comparison_tab = self._create_comparison_tab()
        self.preview_tabs.addTab(self.comparison_tab, "Data Summary")
        
        preview_layout.addWidget(self.preview_tabs)
        parent_layout.addWidget(preview_group)
    
    def _create_summary_cards(self, parent_layout):
        """Create summary cards for quick overview"""
        cards_layout = QHBoxLayout()
        
        # Bank summary card
        self.bank_summary_card = QFrame()
        self.bank_summary_card.setFrameStyle(QFrame.Box)
        self.bank_summary_card.setStyleSheet("""
            QFrame { 
                background-color: #e3f2fd; 
                border: 2px solid #2196f3; 
                border-radius: 8px; 
                padding: 10px; 
            }
        """)
        bank_card_layout = QVBoxLayout(self.bank_summary_card)
        self.bank_summary_label = QLabel("Bank Data\nNot Loaded")
        self.bank_summary_label.setAlignment(Qt.AlignCenter)
        bank_card_layout.addWidget(self.bank_summary_label)
        
        # ERP summary card
        self.erp_summary_card = QFrame()
        self.erp_summary_card.setFrameStyle(QFrame.Box)
        self.erp_summary_card.setStyleSheet("""
            QFrame { 
                background-color: #e8f5e8; 
                border: 2px solid #4caf50; 
                border-radius: 8px; 
                padding: 10px; 
            }
        """)
        erp_card_layout = QVBoxLayout(self.erp_summary_card)
        self.erp_summary_label = QLabel("ERP Data\nNot Loaded")
        self.erp_summary_label.setAlignment(Qt.AlignCenter)
        erp_card_layout.addWidget(self.erp_summary_label)
        
        # Reconciliation status card
        self.status_card = QFrame()
        self.status_card.setFrameStyle(QFrame.Box)
        self.status_card.setStyleSheet("""
            QFrame { 
                background-color: #fff3e0; 
                border: 2px solid #ff9800; 
                border-radius: 8px; 
                padding: 10px; 
            }
        """)
        status_card_layout = QVBoxLayout(self.status_card)
        self.status_label = QLabel("Status\nWaiting for Data")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_card_layout.addWidget(self.status_label)
        
        cards_layout.addWidget(self.bank_summary_card)
        cards_layout.addWidget(self.erp_summary_card)
        cards_layout.addWidget(self.status_card)
        
        parent_layout.addLayout(cards_layout)
    
    def _create_bank_preview_tab(self) -> QWidget:
        """Create bank data preview tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Bank data table
        self.bank_preview_table = QTableWidget()
        self.bank_preview_table.setMaximumHeight(300)
        layout.addWidget(self.bank_preview_table)
        
        # Bank data info
        self.bank_info_text = QTextEdit()
        self.bank_info_text.setMaximumHeight(100)
        self.bank_info_text.setReadOnly(True)
        layout.addWidget(self.bank_info_text)
        
        return tab
    
    def _create_erp_preview_tab(self) -> QWidget:
        """Create ERP data preview tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # ERP data table
        self.erp_preview_table = QTableWidget()
        self.erp_preview_table.setMaximumHeight(300)
        layout.addWidget(self.erp_preview_table)
        
        # ERP data info
        self.erp_info_text = QTextEdit()
        self.erp_info_text.setMaximumHeight(100)
        self.erp_info_text.setReadOnly(True)
        layout.addWidget(self.erp_info_text)
        
        return tab
    
    def _create_comparison_tab(self) -> QWidget:
        """Create data comparison tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Comparison summary
        self.comparison_text = QTextEdit()
        self.comparison_text.setReadOnly(True)
        layout.addWidget(self.comparison_text)
        
        return tab
    
    def _create_action_buttons(self, parent_layout):
        """Create action buttons section"""
        buttons_group = QGroupBox("Actions")
        buttons_layout = QHBoxLayout(buttons_group)
        
        self.clear_all_btn = QPushButton("Clear All Data")
        self.export_combined_btn = QPushButton("Export Combined Data")
        self.ready_for_reconciliation_btn = QPushButton("Ready for Reconciliation")
        
        self.clear_all_btn.clicked.connect(self._clear_all_data)
        self.export_combined_btn.clicked.connect(self._export_combined_data)
        self.ready_for_reconciliation_btn.clicked.connect(self._ready_for_reconciliation)
        
        # Initially disabled
        self.export_combined_btn.setEnabled(False)
        self.ready_for_reconciliation_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.clear_all_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.export_combined_btn)
        buttons_layout.addWidget(self.ready_for_reconciliation_btn)
        
        parent_layout.addWidget(buttons_group)
    
    def _connect_services(self):
        """Connect to data and import services"""
        # Connect to data service signals
        self.data_service.bank_data_loaded.connect(self._on_bank_data_loaded)
        self.data_service.erp_data_loaded.connect(self._on_erp_data_loaded)
        
        # Connect to import service signals
        self.import_service.import_started.connect(self._on_import_started)
        self.import_service.import_completed.connect(self._on_import_completed)
        self.import_service.import_failed.connect(self._on_import_failed)
    
    # ================================================================================================
    # PUBLIC INTERFACE METHODS (Expected by EnhancedMainWindow)
    # ================================================================================================
    
    def upload_bank_file(self) -> bool:
        """Public method expected by main window - delegates to private method"""
        return self._upload_bank_file()
    
    def upload_erp_file(self) -> bool:
        """Public method expected by main window - delegates to private method"""
        return self._upload_erp_file()
    
    # ================================================================================================
    # SLOT IMPLEMENTATIONS
    # ================================================================================================
    
    @Slot()
    def _upload_bank_file(self) -> bool:
        """Handle bank file upload"""
        if self.import_service.import_bank_statement_with_dialog(self):
            self.bank_file_label.setText("Uploading...")
            self.bank_upload_btn.setEnabled(False)
            return True
        return False
    
    @Slot()
    def _upload_erp_file(self) -> bool:
        """Handle ERP file upload"""
        if self.import_service.import_erp_data_with_dialog(self):
            self.erp_file_label.setText("Uploading...")
            self.erp_upload_btn.setEnabled(False)
            return True
        return False
    
    @Slot(object)
    def _on_bank_data_loaded(self, statement):
        """Handle bank data loaded"""
        self.bank_file_label.setText(f"✓ Bank statement loaded ({len(statement.transactions)} transactions)")
        self.bank_upload_btn.setEnabled(True)
        
        # Update bank summary card
        self.bank_summary_label.setText(f"Bank Data\n{len(statement.transactions)} transactions")
        self.bank_summary_card.setStyleSheet("""
            QFrame { 
                background-color: #e8f5e8; 
                border: 2px solid #4caf50; 
                border-radius: 8px; 
                padding: 10px; 
            }
        """)
        
        # Populate bank preview table
        self._populate_bank_preview(statement)
        
        # Update status
        self._update_status()
        
        # Emit signal
        self.bank_data_ready.emit(statement)
    
    @Slot(object)
    def _on_erp_data_loaded(self, transactions):
        """Handle ERP data loaded"""
        self.erp_file_label.setText(f"✓ ERP data loaded ({len(transactions)} transactions)")
        self.erp_upload_btn.setEnabled(True)
        
        # Update ERP summary card
        self.erp_summary_label.setText(f"ERP Data\n{len(transactions)} transactions")
        self.erp_summary_card.setStyleSheet("""
            QFrame { 
                background-color: #e8f5e8; 
                border: 2px solid #4caf50; 
                border-radius: 8px; 
                padding: 10px; 
            }
        """)
        
        # Populate ERP preview table
        self._populate_erp_preview(transactions)
        
        # Update status
        self._update_status()
        
        # Emit signal
        self.erp_data_ready.emit(transactions)
    
    def _populate_bank_preview(self, statement):
        """Populate bank preview table"""
        df = statement.to_dataframe()
        
        self.bank_preview_table.setRowCount(min(10, len(df)))  # Show first 10 rows
        self.bank_preview_table.setColumnCount(len(df.columns))
        self.bank_preview_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for row in range(min(10, len(df))):
            for col in range(len(df.columns)):
                item = QTableWidgetItem(str(df.iloc[row, col]))
                self.bank_preview_table.setItem(row, col, item)
        
        # Update info text
        info = f"""
        Bank Statement Summary:
        - Total Transactions: {len(df)}
        - Date Range: {df['date'].min()} to {df['date'].max()}
        - Total Amount: {df['amount'].sum():,.2f}
        - Currency: {getattr(statement, 'currency', 'Unknown')}
        """
        self.bank_info_text.setText(info)
    
    def _populate_erp_preview(self, transactions):
        """Populate ERP preview table"""
        # Convert to DataFrame for display
        df = pd.DataFrame([{
            'date': t.date,
            'description': t.description,
            'amount': t.amount,
            'reference': getattr(t, 'reference', '')
        } for t in transactions[:10]])  # Show first 10 rows
        
        if not df.empty:
            self.erp_preview_table.setRowCount(len(df))
            self.erp_preview_table.setColumnCount(len(df.columns))
            self.erp_preview_table.setHorizontalHeaderLabels(df.columns.tolist())
            
            for row in range(len(df)):
                for col in range(len(df.columns)):
                    item = QTableWidgetItem(str(df.iloc[row, col]))
                    self.erp_preview_table.setItem(row, col, item)
        
        # Update info text
        total_amount = sum(t.amount for t in transactions)
        dates = [t.date for t in transactions if t.date]
        date_range = f"{min(dates)} to {max(dates)}" if dates else "No dates"
        
        info = f"""
        ERP Data Summary:
        - Total Transactions: {len(transactions)}
        - Date Range: {date_range}
        - Total Amount: {total_amount:,.2f}
        - Sample shown: First 10 transactions
        """
        self.erp_info_text.setText(info)
    
    def _update_status(self):
        """Update reconciliation status"""
        if self.data_service.is_ready_for_reconciliation:
            self.status_label.setText("Status\nReady for Reconciliation!")
            self.status_card.setStyleSheet("""
                QFrame { 
                    background-color: #e8f5e8; 
                    border: 2px solid #4caf50; 
                    border-radius: 8px; 
                    padding: 10px; 
                }
            """)
            self.ready_for_reconciliation_btn.setEnabled(True)
            self.export_combined_btn.setEnabled(True)
            
            # Update comparison tab
            self._update_comparison_tab()
            
            # Emit both sources ready signal
            self.both_sources_ready.emit(
                self.data_service.bank_statement,
                self.data_service.erp_transactions
            )
        else:
            missing = []
            if not self.data_service.bank_statement:
                missing.append("Bank Statement")
            if not self.data_service.erp_transactions:
                missing.append("ERP Data")
            
            self.status_label.setText(f"Status\nWaiting for:\n{', '.join(missing)}")
    
    def _update_comparison_tab(self):
        """Update data comparison tab"""
        summary = self.data_service.get_data_summary()
        
        comparison_text = f"""
        DATA COMPARISON SUMMARY
        =======================
        
        Bank Statement:
        - Transactions: {summary['bank_count']}
        - Date Range: {summary.get('bank_date_range', 'N/A')}
        - Total Amount: {summary.get('bank_total_amount', 0):,.2f}
        - Currency: {summary.get('bank_currency', 'Unknown')}
        
        ERP Data:
        - Transactions: {summary['erp_count']}
        - Date Range: {summary.get('erp_date_range', 'N/A')}
        - Total Amount: {summary.get('erp_total_amount', 0):,.2f}
        
        Reconciliation Readiness:
        - Ready: {'✓ Yes' if summary['ready_for_reconciliation'] else '✗ No'}
        - Previous Results: {summary['reconciliation_count']} matches
        
        NEXT STEPS:
        {'→ Ready to run reconciliation!' if summary['ready_for_reconciliation'] else '→ Complete data loading first'}
        """
        
        self.comparison_text.setText(comparison_text)
    
    @Slot(str)
    def _on_import_started(self, import_type):
        """Handle import started"""
        if import_type == 'bank':
            self.bank_upload_btn.setText("Uploading...")
            self.bank_upload_btn.setEnabled(False)
        elif import_type == 'erp':
            self.erp_upload_btn.setText("Uploading...")
            self.erp_upload_btn.setEnabled(False)
    
    @Slot(object)
    def _on_import_completed(self, result):
        """Handle import completed"""
        self.bank_upload_btn.setText("Upload Bank Statement")
        self.erp_upload_btn.setText("Upload ERP Data")
        self.bank_upload_btn.setEnabled(True)
        self.erp_upload_btn.setEnabled(True)
    
    @Slot(str)
    def _on_import_failed(self, error_message):
        """Handle import failed"""
        self.bank_upload_btn.setText("Upload Bank Statement")
        self.erp_upload_btn.setText("Upload ERP Data")
        self.bank_upload_btn.setEnabled(True)
        self.erp_upload_btn.setEnabled(True)
        
        # Show error in status
        self.status_label.setText(f"Status\nError: {error_message[:30]}...")
        QMessageBox.critical(self, "Import Error", f"Import failed:\n{error_message}")
    
    @Slot()
    def _clear_all_data(self):
        """Clear all loaded data"""
        self.data_service.clear_data('all')
        
        # Reset UI
        self.bank_file_label.setText("No file selected")
        self.erp_file_label.setText("No file selected")
        self.bank_summary_label.setText("Bank Data\nNot Loaded")
        self.erp_summary_label.setText("ERP Data\nNot Loaded")
        self.status_label.setText("Status\nWaiting for Data")
        
        # Reset card styling
        self.bank_summary_card.setStyleSheet("""
            QFrame { 
                background-color: #e3f2fd; 
                border: 2px solid #2196f3; 
                border-radius: 8px; 
                padding: 10px; 
            }
        """)
        self.erp_summary_card.setStyleSheet("""
            QFrame { 
                background-color: #e8f5e8; 
                border: 2px solid #4caf50; 
                border-radius: 8px; 
                padding: 10px; 
            }
        """)
        self.status_card.setStyleSheet("""
            QFrame { 
                background-color: #fff3e0; 
                border: 2px solid #ff9800; 
                border-radius: 8px; 
                padding: 10px; 
            }
        """)
        
        # Clear tables
        self.bank_preview_table.setRowCount(0)
        self.erp_preview_table.setRowCount(0)
        
        # Clear text areas
        self.bank_info_text.clear()
        self.erp_info_text.clear()
        self.comparison_text.clear()
        
        # Reset buttons
        self.export_combined_btn.setEnabled(False)
        self.ready_for_reconciliation_btn.setEnabled(False)
    
    @Slot()
    def _export_combined_data(self):
        """Export combined data for external analysis"""
        QMessageBox.information(self, "Export", "Export functionality to be implemented")
    
    @Slot()
    def _ready_for_reconciliation(self):
        """Signal that data is ready for reconciliation"""
        if self.data_service.is_ready_for_reconciliation:
            QMessageBox.information(self, "Ready", "Data is ready for reconciliation!\nSwitching to reconciliation tab...")
            # The main window will handle tab switching