# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# LOW CONFIDENCE REVIEW DIALOG
# ============================================================================

# views/dialogs/low_confidence_review_dialog.py
"""
Advanced dialog for reviewing and editing low confidence matches
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                            QPushButton, QLabel, QTextEdit, QComboBox, QFrame, QSplitter,
                            QGroupBox, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
                            QMessageBox, QHeaderView, QButtonGroup, QRadioButton)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont, QColor, QBrush
from typing import List, Dict, Optional
from datetime import datetime

from models.data_models import TransactionMatch, MatchStatus

class MatchReviewWidget(QFrame):
    """Widget for reviewing individual match details"""
    
    match_decision_made = Signal(object, str, str)  # match, decision, comment
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_match: Optional[TransactionMatch] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the match review interface"""
        layout = QVBoxLayout(self)
        
        # Match details section
        details_group = QGroupBox("Match Details")
        details_layout = QFormLayout(details_group)
        
        # Bank transaction details
        self.bank_date_label = QLabel()
        self.bank_desc_label = QLabel()
        self.bank_amount_label = QLabel()
        self.bank_ref_label = QLabel()
        
        details_layout.addRow("Bank Date:", self.bank_date_label)
        details_layout.addRow("Bank Description:", self.bank_desc_label)
        details_layout.addRow("Bank Amount:", self.bank_amount_label)
        details_layout.addRow("Bank Reference:", self.bank_ref_label)
        
        # Separator
        details_layout.addRow(QFrame())
        
        # ERP transaction details
        self.erp_date_label = QLabel()
        self.erp_desc_label = QLabel()
        self.erp_amount_label = QLabel()
        self.erp_ref_label = QLabel()
        
        details_layout.addRow("ERP Date:", self.erp_date_label)
        details_layout.addRow("ERP Description:", self.erp_desc_label)
        details_layout.addRow("ERP Amount:", self.erp_amount_label)
        details_layout.addRow("ERP Reference:", self.erp_ref_label)
        
        # Separator
        details_layout.addRow(QFrame())
        
        # Match metrics
        self.confidence_label = QLabel()
        self.similarity_label = QLabel()
        self.issues_label = QLabel()
        
        details_layout.addRow("Confidence Score:", self.confidence_label)
        details_layout.addRow("Similarity Score:", self.similarity_label)
        details_layout.addRow("Identified Issues:", self.issues_label)
        
        layout.addWidget(details_group)
        
        # Decision section
        decision_group = QGroupBox("Review Decision")
        decision_layout = QVBoxLayout(decision_group)
        
        # Decision buttons
        decision_buttons_layout = QHBoxLayout()
        self.decision_group = QButtonGroup()
        
        self.accept_radio = QRadioButton("Accept Match")
        self.reject_radio = QRadioButton("Reject Match")
        self.modify_radio = QRadioButton("Modify Match")
        
        self.decision_group.addButton(self.accept_radio, 0)
        self.decision_group.addButton(self.reject_radio, 1)
        self.decision_group.addButton(self.modify_radio, 2)
        
        decision_buttons_layout.addWidget(self.accept_radio)
        decision_buttons_layout.addWidget(self.reject_radio)
        decision_buttons_layout.addWidget(self.modify_radio)
        decision_buttons_layout.addStretch()
        
        decision_layout.addLayout(decision_buttons_layout)
        
        # Comment section
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        self.comment_edit.setPlaceholderText("Add comments about this match decision...")
        
        decision_layout.addWidget(QLabel("Comments:"))
        decision_layout.addWidget(self.comment_edit)
        
        # Action buttons
        action_buttons_layout = QHBoxLayout()
        self.apply_decision_btn = QPushButton("Apply Decision")
        self.skip_btn = QPushButton("Skip for Now")
        
        self.apply_decision_btn.clicked.connect(self._apply_decision)
        self.skip_btn.clicked.connect(self._skip_match)
        
        action_buttons_layout.addWidget(self.apply_decision_btn)
        action_buttons_layout.addWidget(self.skip_btn)
        action_buttons_layout.addStretch()
        
        decision_layout.addLayout(action_buttons_layout)
        layout.addWidget(decision_group)
    
    def set_match(self, match: TransactionMatch):
        """Set the match to be reviewed"""
        self._current_match = match
        self._populate_match_details()
    
    def _populate_match_details(self):
        """Populate the UI with match details"""
        if not self._current_match:
            return
            
        match = self._current_match
        
        # Bank transaction details
        self.bank_date_label.setText(str(match.bank_transaction.date))
        self.bank_desc_label.setText(match.bank_transaction.description)
        self.bank_amount_label.setText(f"{match.bank_transaction.amount:.2f}")
        self.bank_ref_label.setText(getattr(match.bank_transaction, 'reference', ''))
        
        # ERP transaction details
        self.erp_date_label.setText(str(match.erp_transaction.date))
        self.erp_desc_label.setText(match.erp_transaction.description)
        self.erp_amount_label.setText(f"{match.erp_transaction.amount:.2f}")
        self.erp_ref_label.setText(getattr(match.erp_transaction, 'reference', ''))
        
        # Match metrics
        self.confidence_label.setText(f"{match.confidence_score:.3f}")
        
        # Color code confidence
        if match.confidence_score >= 0.7:
            color = "green"
        elif match.confidence_score >= 0.4:
            color = "orange"
        else:
            color = "red"
        self.confidence_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        
        # Similarity and issues (these would come from enhanced matching engine)
        self.similarity_label.setText("N/A")  # Would be populated by ML engine
        self.issues_label.setText(self._identify_issues(match))
        
        # Reset decision
        self.decision_group.setExclusive(False)
        self.accept_radio.setChecked(False)
        self.reject_radio.setChecked(False)
        self.modify_radio.setChecked(False)
        self.decision_group.setExclusive(True)
        
        # Clear comment
        self.comment_edit.clear()
    
    def _identify_issues(self, match: TransactionMatch) -> str:
        """Identify potential issues with the match"""
        issues = []
        
        # Date difference check
        if hasattr(match.bank_transaction, 'date') and hasattr(match.erp_transaction, 'date'):
            date_diff = abs((match.bank_transaction.date - match.erp_transaction.date).days)
            if date_diff > 7:
                issues.append(f"Date difference: {date_diff} days")
        
        # Amount difference check
        amount_diff = abs(match.bank_transaction.amount - match.erp_transaction.amount)
        if amount_diff > 0.01:  # More than 1 cent difference
            issues.append(f"Amount difference: {amount_diff:.2f}")
        
        # Description similarity check
        bank_desc = match.bank_transaction.description.lower()
        erp_desc = match.erp_transaction.description.lower()
        if len(set(bank_desc.split()) & set(erp_desc.split())) < 2:
            issues.append("Low description similarity")
        
        return "; ".join(issues) if issues else "No issues identified"
    
    @Slot()
    def _apply_decision(self):
        """Apply the review decision"""
        if not self._current_match:
            return
            
        if self.accept_radio.isChecked():
            decision = "accept"
        elif self.reject_radio.isChecked():
            decision = "reject"
        elif self.modify_radio.isChecked():
            decision = "modify"
        else:
            QMessageBox.warning(self, "Decision Required", "Please select a decision for this match.")
            return
        
        comment = self.comment_edit.toPlainText().strip()
        self.match_decision_made.emit(self._current_match, decision, comment)
    
    @Slot()
    def _skip_match(self):
        """Skip this match for now"""
        if self._current_match:
            self.match_decision_made.emit(self._current_match, "skip", "")

class LowConfidenceReviewDialog(QDialog):
    """Advanced dialog for reviewing low confidence matches"""
    
    # Signals
    matches_reviewed = Signal(list)  # List of updated matches
    review_completed = Signal()
    
    def __init__(self, matches: List[TransactionMatch], parent=None):
        super().__init__(parent)
        self.matches = matches.copy()
        self.current_index = 0
        self.reviewed_matches: List[TransactionMatch] = []
        self.skipped_matches: List[TransactionMatch] = []
        
        self.setWindowTitle("Review Low Confidence Matches")
        self.setModal(True)
        self.resize(1200, 800)
        
        self._setup_ui()
        self._load_first_match()
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Header with progress
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Review Low Confidence Matches")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignRight)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.progress_label)
        
        layout.addLayout(header_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Match list
        self.matches_list_widget = self._create_matches_list()
        splitter.addWidget(self.matches_list_widget)
        
        # Right side: Match review widget
        self.match_review_widget = MatchReviewWidget()
        self.match_review_widget.match_decision_made.connect(self._handle_match_decision)
        splitter.addWidget(self.match_review_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("← Previous")
        self.next_btn = QPushButton("Next →")
        self.save_progress_btn = QPushButton("Save Progress")
        self.finish_btn = QPushButton("Finish Review")
        self.cancel_btn = QPushButton("Cancel")
        
        # Connect buttons
        self.prev_btn.clicked.connect(self._previous_match)
        self.next_btn.clicked.connect(self._next_match)
        self.save_progress_btn.clicked.connect(self._save_progress)
        self.finish_btn.clicked.connect(self._finish_review)
        self.cancel_btn.clicked.connect(self.reject)
        
        bottom_layout.addWidget(self.prev_btn)
        bottom_layout.addWidget(self.next_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.save_progress_btn)
        bottom_layout.addWidget(self.finish_btn)
        bottom_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(bottom_layout)
        
        self._update_navigation_buttons()
    
    def _create_matches_list(self) -> QGroupBox:
        """Create the matches list widget"""
        group = QGroupBox("Matches to Review")
        layout = QVBoxLayout(group)
        
        self.matches_table = QTableWidget()
        self.matches_table.setColumnCount(4)
        self.matches_table.setHorizontalHeaderLabels(["#", "Bank Amount", "ERP Amount", "Confidence"])
        
        # Populate matches table
        self.matches_table.setRowCount(len(self.matches))
        for row, match in enumerate(self.matches):
            self.matches_table.setItem(row, 0, QTableWidgetItem(f"{row + 1}"))
            self.matches_table.setItem(row, 1, QTableWidgetItem(f"{match.bank_transaction.amount:.2f}"))
            self.matches_table.setItem(row, 2, QTableWidgetItem(f"{match.erp_transaction.amount:.2f}"))
            
            # Confidence with color coding
            conf_item = QTableWidgetItem(f"{match.confidence_score:.3f}")
            if match.confidence_score >= 0.5:
                conf_item.setBackground(QBrush(QColor(255, 255, 200)))  # Light yellow
            else:
                conf_item.setBackground(QBrush(QColor(255, 200, 200)))  # Light red
            self.matches_table.setItem(row, 3, conf_item)
        
        # Configure table
        self.matches_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.matches_table.setSelectionMode(QTableWidget.SingleSelection)
        self.matches_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Connect selection
        self.matches_table.itemSelectionChanged.connect(self._on_match_selected)
        
        layout.addWidget(self.matches_table)
        
        # Summary info
        self.matches_summary = QLabel()
        layout.addWidget(self.matches_summary)
        self._update_matches_summary()
        
        return group
    
    def _load_first_match(self):
        """Load the first match for review"""
        if self.matches:
            self.current_index = 0
            self._load_current_match()
            self.matches_table.selectRow(0)
    
    def _load_current_match(self):
        """Load the current match into the review widget"""
        if 0 <= self.current_index < len(self.matches):
            match = self.matches[self.current_index]
            self.match_review_widget.set_match(match)
            self._update_progress_label()
        
        self._update_navigation_buttons()
    
    def _update_progress_label(self):
        """Update the progress label"""
        total = len(self.matches)
        current = self.current_index + 1
        reviewed = len(self.reviewed_matches)
        skipped = len(self.skipped_matches)
        
        self.progress_label.setText(
            f"Match {current} of {total} | Reviewed: {reviewed} | Skipped: {skipped}"
        )
    
    def _update_navigation_buttons(self):
        """Update navigation button states"""
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.matches) - 1)
    
    def _update_matches_summary(self):
        """Update matches summary info"""
        total = len(self.matches)
        reviewed = len(self.reviewed_matches)
        skipped = len(self.skipped_matches)
        remaining = total - reviewed - skipped
        
        self.matches_summary.setText(
            f"Total: {total} | Reviewed: {reviewed} | Skipped: {skipped} | Remaining: {remaining}"
        )
    
    @Slot()
    def _on_match_selected(self):
        """Handle match selection from table"""
        current_row = self.matches_table.currentRow()
        if 0 <= current_row < len(self.matches):
            self.current_index = current_row
            self._load_current_match()
    
    @Slot(object, str, str)
    def _handle_match_decision(self, match: TransactionMatch, decision: str, comment: str):
        """Handle match decision from review widget"""
        # Update match based on decision
        if decision == "accept":
            match.status = MatchStatus.MATCHED
            match.reviewer_comment = comment
            if match not in self.reviewed_matches:
                self.reviewed_matches.append(match)
        elif decision == "reject":
            match.status = MatchStatus.REJECTED
            match.reviewer_comment = comment
            if match not in self.reviewed_matches:
                self.reviewed_matches.append(match)
        elif decision == "modify":
            # For now, just mark as reviewed with comment
            match.reviewer_comment = f"MODIFY: {comment}"
            if match not in self.reviewed_matches:
                self.reviewed_matches.append(match)
        elif decision == "skip":
            if match not in self.skipped_matches:
                self.skipped_matches.append(match)
        
        # Update UI
        self._update_match_row_appearance(self.current_index, decision)
        self._update_matches_summary()
        self._update_progress_label()
        
        # Auto-advance to next match
        if self.current_index < len(self.matches) - 1:
            self._next_match()
    
    def _update_match_row_appearance(self, row: int, decision: str):
        """Update the appearance of a match row based on decision"""
        if decision == "accept":
            color = QColor(200, 255, 200)  # Light green
        elif decision == "reject":
            color = QColor(255, 200, 200)  # Light red
        elif decision == "modify":
            color = QColor(200, 200, 255)  # Light blue
        elif decision == "skip":
            color = QColor(255, 255, 200)  # Light yellow
        else:
            return
        
        for col in range(self.matches_table.columnCount()):
            item = self.matches_table.item(row, col)
            if item:
                item.setBackground(QBrush(color))
    
    @Slot()
    def _previous_match(self):
        """Navigate to previous match"""
        if self.current_index > 0:
            self.current_index -= 1
            self._load_current_match()
            self.matches_table.selectRow(self.current_index)
    
    @Slot()
    def _next_match(self):
        """Navigate to next match"""
        if self.current_index < len(self.matches) - 1:
            self.current_index += 1
            self._load_current_match()
            self.matches_table.selectRow(self.current_index)
    
    @Slot()
    def _save_progress(self):
        """Save current progress"""
        # Emit intermediate results
        self.matches_reviewed.emit(self.reviewed_matches)
        QMessageBox.information(self, "Progress Saved", 
                              f"Progress saved: {len(self.reviewed_matches)} matches reviewed.")
    
    @Slot()
    def _finish_review(self):
        """Finish the review process"""
        if len(self.reviewed_matches) + len(self.skipped_matches) < len(self.matches):
            reply = QMessageBox.question(
                self, "Incomplete Review",
                f"You have reviewed {len(self.reviewed_matches)} out of {len(self.matches)} matches.\n"
                f"{len(self.skipped_matches)} matches were skipped.\n\n"
                "Do you want to finish the review with the current progress?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Emit final results
        all_processed = self.reviewed_matches + self.skipped_matches
        self.matches_reviewed.emit(all_processed)
        self.review_completed.emit()
        self.accept()
