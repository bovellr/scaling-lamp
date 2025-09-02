# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# ENHANCED TRANSACTION TABLES WIDGET
# ============================================================================

# views/widgets/enhanced_transaction_tables_widget.py
"""
Enhanced transaction tables widget with tabbed interface for different match categories
"""
from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QPushButton, QLabel, QFrame,
                            QAbstractItemView, QMenu, QMessageBox)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QAction, QColor, QBrush
from typing import List, Dict, Any, Optional
import pandas as pd

from models.data_models import TransactionMatch, TransactionData, MatchStatus

class MatchResultsTable(QTableWidget):
    """Enhanced table widget for displaying transaction match results"""
    
    # Signals
    match_selected = Signal(object)  # TransactionMatch
    match_action_requested = Signal(object, str)  # TransactionMatch, action
    
    def __init__(self, table_type: str, parent=None):
        super().__init__(parent)
        self.table_type = table_type
        self._setup_table()
        self._setup_context_menu()
        
    def _setup_table(self):
        """Setup table structure based on type"""
        if self.table_type == "matched":
            headers = ["Bank Date", "Bank Description", "Bank Amount", 
                      "ERP Date", "ERP Description", "ERP Amount", 
                      "Confidence", "Status", "Actions"]
        elif self.table_type in ["unmatched_bank", "unmatched_erp"]:
            headers = ["Date", "Description", "Amount", "Reference", "Status"]
        elif self.table_type == "review":
            headers = ["Bank Date", "Bank Description", "Bank Amount",
                      "ERP Date", "ERP Description", "ERP Amount",
                      "Confidence", "Issues", "Actions"]
        else:
            headers = ["Date", "Description", "Amount", "Status"]
            
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table appearance
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        
        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Apply styling
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                border: 1px solid #c0c0c0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        
        # Connect signals
        self.itemSelectionChanged.connect(self._on_selection_changed)
        
    def _setup_context_menu(self):
        """Setup context menu for table actions"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def populate_matched_data(self, matches: List[TransactionMatch]):
        """Populate table with matched transaction data"""
        self.setRowCount(len(matches))
        
        for row, match in enumerate(matches):
            self._populate_match_row(row, match)
            
    def populate_unmatched_data(self, transactions: List[TransactionData], data_type: str):
        """Populate table with unmatched transaction data"""
        self.setRowCount(len(transactions))
        
        for row, transaction in enumerate(transactions):
            self._populate_unmatched_row(row, transaction, data_type)
    
    def _populate_match_row(self, row: int, match: TransactionMatch):
        """Populate a row with match data"""
        # Bank transaction data
        self.setItem(row, 0, QTableWidgetItem(str(match.bank_transaction.date)))
        self.setItem(row, 1, QTableWidgetItem(match.bank_transaction.description))
        self.setItem(row, 2, QTableWidgetItem(f"{match.bank_transaction.amount:.2f}"))
        
        # ERP transaction data
        self.setItem(row, 3, QTableWidgetItem(str(match.erp_transaction.date)))
        self.setItem(row, 4, QTableWidgetItem(match.erp_transaction.description))
        self.setItem(row, 5, QTableWidgetItem(f"{match.erp_transaction.amount:.2f}"))
        
        # Confidence score with color coding
        confidence_item = QTableWidgetItem(f"{match.confidence_score:.3f}")
        if match.confidence_score >= 0.8:
            confidence_item.setBackground(QBrush(QColor(200, 255, 200)))  # Light green
        elif match.confidence_score >= 0.5:
            confidence_item.setBackground(QBrush(QColor(255, 255, 200)))  # Light yellow
        else:
            confidence_item.setBackground(QBrush(QColor(255, 200, 200)))  # Light red
        self.setItem(row, 6, confidence_item)
        
        # Status
        status_item = QTableWidgetItem(match.status.value if match.status else "PENDING")
        self.setItem(row, 7, status_item)
        
        # Store match object for later retrieval
        self.setItem(row, 8, QTableWidgetItem(""))  # Placeholder for actions
        self.item(row, 0).setData(Qt.UserRole, match)
    
    def _populate_unmatched_row(self, row: int, transaction: TransactionData, data_type: str):
        """Populate a row with unmatched transaction data"""
        self.setItem(row, 0, QTableWidgetItem(str(transaction.date)))
        self.setItem(row, 1, QTableWidgetItem(transaction.description))
        self.setItem(row, 2, QTableWidgetItem(f"{transaction.amount:.2f}"))
        self.setItem(row, 3, QTableWidgetItem(getattr(transaction, 'reference', '')))
        self.setItem(row, 4, QTableWidgetItem("UNMATCHED"))
        
        # Store transaction object
        self.item(row, 0).setData(Qt.UserRole, transaction)
        
        # Color code unmatched items
        if data_type == "bank":
            color = QColor(255, 240, 240)  # Light red for unmatched bank
        else:
            color = QColor(240, 240, 255)  # Light blue for unmatched ERP
            
        for col in range(self.columnCount()):
            if self.item(row, col):
                self.item(row, col).setBackground(QBrush(color))
    
    @Slot()
    def _on_selection_changed(self):
        """Handle row selection change"""
        current_row = self.currentRow()
        if current_row >= 0 and self.item(current_row, 0):
            data = self.item(current_row, 0).data(Qt.UserRole)
            if data:
                self.match_selected.emit(data)
    
    @Slot()
    def _show_context_menu(self, position):
        """Show context menu at position"""
        item = self.itemAt(position)
        if not item:
            return
            
        row = item.row()
        data = self.item(row, 0).data(Qt.UserRole)
        if not data:
            return
            
        menu = QMenu(self)
        
        if self.table_type == "matched":
            if isinstance(data, TransactionMatch):
                menu.addAction("View Details", lambda: self.match_action_requested.emit(data, "view"))
                menu.addAction("Edit Match", lambda: self.match_action_requested.emit(data, "edit"))
                menu.addAction("Reject Match", lambda: self.match_action_requested.emit(data, "reject"))
                menu.addSeparator()
                menu.addAction("Add Comment", lambda: self.match_action_requested.emit(data, "comment"))
        elif self.table_type in ["unmatched_bank", "unmatched_erp"]:
            menu.addAction("Manual Match", lambda: self.match_action_requested.emit(data, "manual_match"))
            menu.addAction("Mark as Exception", lambda: self.match_action_requested.emit(data, "exception"))
        elif self.table_type == "review":
            menu.addAction("Accept Match", lambda: self.match_action_requested.emit(data, "accept"))
            menu.addAction("Reject Match", lambda: self.match_action_requested.emit(data, "reject"))
            menu.addAction("Edit Match", lambda: self.match_action_requested.emit(data, "edit"))
            
        menu.exec(self.mapToGlobal(position))

class EnhancedTransactionTablesWidget(QGroupBox):
    """Enhanced transaction tables with tabbed interface and comprehensive match display"""
    
    # Signals
    match_action_requested = Signal(object, str)
    manual_match_requested = Signal(object)
    review_requested = Signal(list)  # List of low confidence matches
    
    def __init__(self, parent=None):
        super().__init__("Transaction Analysis Results", parent)
        self._setup_ui()
        self._current_matches: List[TransactionMatch] = []
        self._unmatched_bank: List[TransactionData] = []
        self._unmatched_erp: List[TransactionData] = []
        
    def _setup_ui(self):
        """Setup the tabbed interface"""
        layout = QVBoxLayout(self)
        
        # Summary header
        self.summary_frame = self._create_summary_frame()
        layout.addWidget(self.summary_frame)
        
        # Tabbed tables
        self.tables_tabs = QTabWidget()
        
        # Matched transactions tab
        self.matched_table = MatchResultsTable("matched")
        self.matched_table.match_action_requested.connect(self.match_action_requested.emit)
        self.tables_tabs.addTab(self.matched_table, "✓ Matched (0)")
        
        # Unmatched bank transactions tab
        self.unmatched_bank_table = MatchResultsTable("unmatched_bank")
        self.unmatched_bank_table.match_action_requested.connect(self._handle_unmatched_action)
        self.tables_tabs.addTab(self.unmatched_bank_table, "⚠ Unmatched Bank (0)")
        
        # Unmatched ERP transactions tab
        self.unmatched_erp_table = MatchResultsTable("unmatched_erp")
        self.unmatched_erp_table.match_action_requested.connect(self._handle_unmatched_action)
        self.tables_tabs.addTab(self.unmatched_erp_table, "⚠ Unmatched ERP (0)")
        
        # Review required tab
        self.review_table = MatchResultsTable("review")
        self.review_table.match_action_requested.connect(self._handle_review_action)
        self.tables_tabs.addTab(self.review_table, "⚡ Review Required (0)")
        
        layout.addWidget(self.tables_tabs)
        
        # Action buttons
        self.action_buttons = self._create_action_buttons()
        layout.addWidget(self.action_buttons)
    
    def _create_summary_frame(self) -> QFrame:
        """Create summary statistics frame"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        
        self.matched_count_label = QLabel("Matched: 0")
        self.unmatched_bank_count_label = QLabel("Unmatched Bank: 0")
        self.unmatched_erp_count_label = QLabel("Unmatched ERP: 0")
        self.review_count_label = QLabel("Review Required: 0")
        self.accuracy_label = QLabel("Accuracy: 0%")
        
        # Style labels
        for label in [self.matched_count_label, self.unmatched_bank_count_label, 
                     self.unmatched_erp_count_label, self.review_count_label, self.accuracy_label]:
            label.setStyleSheet("font-weight: bold; padding: 5px;")
        
        layout.addWidget(self.matched_count_label)
        layout.addWidget(QFrame())  # Separator
        layout.addWidget(self.unmatched_bank_count_label)
        layout.addWidget(QFrame())  # Separator
        layout.addWidget(self.unmatched_erp_count_label)
        layout.addWidget(QFrame())  # Separator
        layout.addWidget(self.review_count_label)
        layout.addStretch()
        layout.addWidget(self.accuracy_label)
        
        return frame
    
    def _create_action_buttons(self) -> QFrame:
        """Create action buttons frame"""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        
        self.export_results_btn = QPushButton("Export Results")
        self.review_all_btn = QPushButton("Review All Low Confidence")
        self.manual_match_btn = QPushButton("Manual Match")
        self.clear_results_btn = QPushButton("Clear Results")
        
        # Connect signals
        self.review_all_btn.clicked.connect(self._review_all_low_confidence)
        self.export_results_btn.clicked.connect(self._export_results)
        self.clear_results_btn.clicked.connect(self._clear_all_results)
        
        layout.addWidget(self.export_results_btn)
        layout.addWidget(self.review_all_btn)
        layout.addWidget(self.manual_match_btn)
        layout.addStretch()
        layout.addWidget(self.clear_results_btn)
        
        return frame
    
    def populate_reconciliation_results(self, matches: List[TransactionMatch], 
                                      unmatched_bank: List[TransactionData],
                                      unmatched_erp: List[TransactionData]):
        """Populate all tables with reconciliation results"""
        
        # Store data
        self._current_matches = matches
        self._unmatched_bank = unmatched_bank
        self._unmatched_erp = unmatched_erp
        
        # Classify matches by confidence
        high_confidence = [m for m in matches if m.confidence_score >= 0.8]
        medium_confidence = [m for m in matches if 0.5 <= m.confidence_score < 0.8]
        low_confidence = [m for m in matches if m.confidence_score < 0.5]
        
        # Populate matched table (high confidence only)
        self.matched_table.populate_matched_data(high_confidence)
        
        # Populate unmatched tables
        self.unmatched_bank_table.populate_unmatched_data(unmatched_bank, "bank")
        self.unmatched_erp_table.populate_unmatched_data(unmatched_erp, "erp")
        
        # Populate review table (medium + low confidence)
        review_matches = medium_confidence + low_confidence
        self.review_table.populate_matched_data(review_matches)
        
        # Update tab labels with counts
        self.tables_tabs.setTabText(0, f"✓ Matched ({len(high_confidence)})")
        self.tables_tabs.setTabText(1, f"⚠ Unmatched Bank ({len(unmatched_bank)})")
        self.tables_tabs.setTabText(2, f"⚠ Unmatched ERP ({len(unmatched_erp)})")
        self.tables_tabs.setTabText(3, f"⚡ Review Required ({len(review_matches)})")
        
        # Update summary
        self._update_summary(high_confidence, unmatched_bank, unmatched_erp, review_matches)
        
        # Enable/disable action buttons
        self.review_all_btn.setEnabled(len(review_matches) > 0)
        self.export_results_btn.setEnabled(len(matches) > 0)
    
    def _update_summary(self, matched: List[TransactionMatch], unmatched_bank: List[TransactionData],
                       unmatched_erp: List[TransactionData], review: List[TransactionMatch]):
        """Update summary statistics"""
        total_bank = len(matched) + len(unmatched_bank) + len(review)
        total_erp = len(matched) + len(unmatched_erp) + len(review)
        
        accuracy = (len(matched) / max(total_bank, 1)) * 100
        
        self.matched_count_label.setText(f"Matched: {len(matched)}")
        self.unmatched_bank_count_label.setText(f"Unmatched Bank: {len(unmatched_bank)}")
        self.unmatched_erp_count_label.setText(f"Unmatched ERP: {len(unmatched_erp)}")
        self.review_count_label.setText(f"Review Required: {len(review)}")
        self.accuracy_label.setText(f"Accuracy: {accuracy:.1f}%")
        
        # Color code accuracy
        if accuracy >= 80:
            color = "green"
        elif accuracy >= 60:
            color = "orange"
        else:
            color = "red"
        self.accuracy_label.setStyleSheet(f"font-weight: bold; color: {color}; padding: 5px;")
    
    @Slot(object, str)
    def _handle_unmatched_action(self, transaction: TransactionData, action: str):
        """Handle actions on unmatched transactions"""
        if action == "manual_match":
            self.manual_match_requested.emit(transaction)
        elif action == "exception":
            # Handle exception marking
            QMessageBox.information(self, "Exception", f"Transaction marked as exception: {transaction.description}")
    
    @Slot(object, str)
    def _handle_review_action(self, match: TransactionMatch, action: str):
        """Handle actions on matches requiring review"""
        if action == "accept":
            match.status = MatchStatus.MATCHED
            # Move to matched table
            self._refresh_tables()
        elif action == "reject":
            match.status = MatchStatus.REJECTED
            # Remove from review table
            self._refresh_tables()
        elif action == "edit":
            # Open edit dialog
            self.match_action_requested.emit(match, "edit")
    
    @Slot()
    def _review_all_low_confidence(self):
        """Open review dialog for all low confidence matches"""
        review_matches = []
        for row in range(self.review_table.rowCount()):
            if self.review_table.item(row, 0):
                match = self.review_table.item(row, 0).data(Qt.UserRole)
                if isinstance(match, TransactionMatch):
                    review_matches.append(match)
        
        if review_matches:
            self.review_requested.emit(review_matches)
        else:
            QMessageBox.information(self, "Review", "No matches require review.")
    
    @Slot()
    def _export_results(self):
        """Export reconciliation results"""
        # Implementation for exporting results
        QMessageBox.information(self, "Export", "Results export functionality to be implemented.")
    
    @Slot()
    def _clear_all_results(self):
        """Clear all results from tables"""
        self.matched_table.setRowCount(0)
        self.unmatched_bank_table.setRowCount(0)
        self.unmatched_erp_table.setRowCount(0)
        self.review_table.setRowCount(0)
        
        # Reset tab labels
        self.tables_tabs.setTabText(0, "✓ Matched (0)")
        self.tables_tabs.setTabText(1, "⚠ Unmatched Bank (0)")
        self.tables_tabs.setTabText(2, "⚠ Unmatched ERP (0)")
        self.tables_tabs.setTabText(3, "⚡ Review Required (0)")
        
        # Reset summary
        self.matched_count_label.setText("Matched: 0")
        self.unmatched_bank_count_label.setText("Unmatched Bank: 0")
        self.unmatched_erp_count_label.setText("Unmatched ERP: 0")
        self.review_count_label.setText("Review Required: 0")
        self.accuracy_label.setText("Accuracy: 0%")
    
    def _refresh_tables(self):
        """Refresh all tables after data changes"""
        # This would re-populate tables with updated data
        # Implementation depends on how you want to handle real-time updates
        pass