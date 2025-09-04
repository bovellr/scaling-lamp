# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
# views/widgets/file_upload_widget.py
"""
File upload widget integrated with bank transformation.
"""

import sys
import logging
import pandas as pd

from pathlib import Path
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, 
                            QLabel, QComboBox, QFileDialog, QTextEdit, QProgressBar,  
                            QTableWidget, QTableWidgetItem, QMessageBox, QRadioButton, 
                            QButtonGroup, QDateEdit, QSpinBox, QCheckBox, QFrame)
from PySide6.QtCore import Signal, Slot, QDate
from PySide6.QtGui import QFont

from viewmodels.upload_viewmodel import UploadViewModel
from models.data_models import BankTemplate

logger = logging.getLogger(__name__)

class FileUploadWidget(QWidget):
    """PySide6 version of file upload widget."""
    
    # Signals - using PySide6 Signal
    file_uploaded = Signal(str, str)  # file_type, file_path
    file_transformed = Signal(object)  # Emits BankStatement when transformation complete
    processing_error = Signal(str, str)     # source_type, error_message  
    bank_data_ready = Signal(object, dict)  # statement, result_info
    
    def __init__(self, viewmodel: Optional[UploadViewModel] = None, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel if viewmodel is not None else UploadViewModel()
        self.bank_file_path = None
        
        self._setup_ui()
        self._bind_viewmodel()

        logger.info("FileUploadWidget initialized")
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Header (new)
        self._create_header(layout)

        # Template selection group
        self._create_template_section(layout)

        # Bank statement upload group
        self._create_bank_upload_section(layout)

        # Transformation group
        self._create_transformation_section(layout)

        # Results group
        self._create_results_section(layout)

        # Action buttons
        self._create_action_buttons(layout)

    def _create_header(self, parent_layout):
        """Create the header section of the widget."""
        header_label = QLabel("Bank Statement Import")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        parent_layout.addWidget(header_label)
        
    def _create_template_section(self, parent_layout):
        """Create the template selection section of the widget."""
        template_group = QGroupBox("1. Select Bank Template")
        template_layout = QVBoxLayout(template_group)
        
        self.template_combo = QComboBox()
        self.template_combo.currentTextChanged.connect(self._on_template_changed)
        template_layout.addWidget(QLabel("Bank Type:"))
        template_layout.addWidget(self.template_combo)
        
        template_buttons = QHBoxLayout()
        self.refresh_templates_btn = QPushButton("Refresh Templates")
        self.create_template_btn = QPushButton("Create New Template")
        self.edit_template_btn = QPushButton("Edit Template")
        self.delete_template_btn = QPushButton("Delete Template")
        
        self.refresh_templates_btn.clicked.connect(self._refresh_templates)
        self.create_template_btn.clicked.connect(self._create_template)
        self.edit_template_btn.clicked.connect(self._edit_template)
        self.delete_template_btn.clicked.connect(self._delete_template)
        
        # Initially disable edit and delete buttons (no template selected)
        self.edit_template_btn.setEnabled(False)
        self.delete_template_btn.setEnabled(False)
        
        template_buttons.addWidget(self.refresh_templates_btn)
        template_buttons.addWidget(self.create_template_btn)
        template_buttons.addWidget(self.edit_template_btn)
        template_buttons.addWidget(self.delete_template_btn)
        template_buttons.addStretch()
        template_layout.addLayout(template_buttons)
        
        parent_layout.addWidget(template_group)
        
    def _create_bank_upload_section(self, parent_layout):
        """Create the bank statement upload section of the widget."""
        
        # File upload group
        upload_group = QGroupBox("2. Upload Bank Statement")
        upload_layout = QVBoxLayout(upload_group)
        
        file_layout = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(self.file_path_label)
        file_layout.addWidget(self.browse_btn)
        upload_layout.addLayout(file_layout)
        
        parent_layout.addWidget(upload_group)


    def _create_transformation_section(self, parent_layout):
        """Create the transformation section of the widget."""
        transform_group = QGroupBox("3. Process Data")
        transform_layout = QVBoxLayout(transform_group)

        # Button layout (enhanced )
        button_layout = QHBoxLayout()

        self.transform_btn = QPushButton("Transform Bank Statement")
        self.transform_btn.clicked.connect(self._transform_statement)
        self.transform_btn.setEnabled(False)
        button_layout.addWidget(self.transform_btn)
        
        button_layout.addStretch()
        transform_layout.addLayout(button_layout)

        # Existing progress bar (preserved)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        transform_layout.addWidget(self.progress_bar)
        
        # Existing status label (preserved)
        self.status_label = QLabel("")
        transform_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(transform_group)

    def _create_results_section(self, parent_layout):
        """Create the results section of the widget."""
        results_group = QGroupBox("4. Data Summary & Preview")
        results_layout = QVBoxLayout(results_group)

        # NEW: Summary cards (following your label pattern)
        summary_layout = QHBoxLayout()
        
        self.bank_summary_label = QLabel("Bank: No data")
        self.bank_summary_label.setStyleSheet("padding: 8px; background-color: #f0f0f0; border: 1px solid #ccc;")
        summary_layout.addWidget(self.bank_summary_label)
        
        results_layout.addLayout(summary_layout)
        
        # Existing results text (preserved)
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(160)
        results_layout.addWidget(self.results_text)
        
        # Existing results table (preserved)
        self.results_table = QTableWidget()
        self.results_table.setVisible(False)
        results_layout.addWidget(self.results_table)
        
        parent_layout.addWidget(results_group)

    def _create_action_buttons(self, parent_layout):
        """Create the action buttons section of the widget."""
        button_layout = QHBoxLayout()

        # Existing action buttons (preserved)
        self.use_for_reconciliation_btn = QPushButton("Use for Reconciliation")
        self.export_btn = QPushButton("Export Transformed Data")
        self.use_for_reconciliation_btn.clicked.connect(self._use_for_reconciliation)
        self.export_btn.clicked.connect(self._export_data)
        self.use_for_reconciliation_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        # NEW: Clear buttons
        self.clear_bank_btn = QPushButton("Clear Bank")
        self.clear_bank_btn.clicked.connect(self._clear_bank_data)
        
        button_layout.addWidget(self.use_for_reconciliation_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_bank_btn)
                
        parent_layout.addLayout(button_layout)

    # ========================================================================
    # VIEWMODEL BINDING - Enhanced version of your existing binding
    # ========================================================================    
     
        
    def _bind_viewmodel(self):
        """Bind ViewModel properties to UI elements."""
        # Property change notifications work the same way
        self.viewmodel.bind_property_changed('available_templates', self._update_templates)
        self.viewmodel.bind_property_changed('is_loading', self._update_loading_state)
        self.viewmodel.bind_property_changed('error_message', self._update_error_message)
        self.viewmodel.bind_property_changed('transformed_statement', self._update_results)
        self.viewmodel.bind_property_changed('transformation_result', self._update_status)
        
        # NEW: Enhanced signal bindings (if your ViewModel has these signals)
        if hasattr(self.viewmodel, 'transformation_completed'):
            self.viewmodel.transformation_completed.connect(self._on_bank_transformation_completed)
        
        if hasattr(self.viewmodel, 'transformation_failed'):
            self.viewmodel.transformation_failed.connect(self._on_transformation_failed)
        
        
        # Initial update
        self._update_templates(self.viewmodel.available_templates)
    
    # All other methods remain the same - just the Signal declaration changed
    def _update_templates(self, templates):
        """Update template combo box."""
        self.template_combo.clear()
        self.template_combo.addItem("Select a bank template...", None)
        
        for template in templates:
            self.template_combo.addItem(f"{template.name} ({template.bank_type})", template)
    
    def _update_loading_state(self, is_loading):
        """Update UI loading state."""
        self.progress_bar.setVisible(is_loading)
        self.transform_btn.setEnabled(not is_loading and self._can_transform())

        if is_loading:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.status_label.setText("Processing...")
    
    def _update_error_message(self, error_message):
        """Update error message display."""
        if error_message:
            self.status_label.setText(f"Error: {error_message}")
            self.status_label.setStyleSheet("QLabel { color: red; }")
        else:
            self.status_label.setStyleSheet("")
    
    def _update_results(self, statement):
        """Update results display."""
        if statement and statement.transactions:
            self._populate_results_table(statement)
            self.results_table.setVisible(True)
            self.use_for_reconciliation_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            
            # Update bank summary with success styling
            self.bank_summary_label.setText(f"Bank: {len(statement.transactions)} transactions loaded")
            self.bank_summary_label.setStyleSheet("padding: 8px; background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; font-weight: bold;")
        else:
            self.results_table.setVisible(False)
            self.use_for_reconciliation_btn.setEnabled(False)
            self.export_btn.setEnabled(False)

            # Reset bank summary
            self.bank_summary_label.setText("Bank: No data")
            self.bank_summary_label.setStyleSheet("padding: 8px; background-color: #f0f0f0; border: 1px solid #ccc;")
        
  
    def _update_status(self, result_info):
        """Update status message."""
        if result_info:
            if result_info['success']:
                message = f"✓ {result_info['message']}"
                self.status_label.setStyleSheet("QLabel { color: green; }")
            else:
                message = f"✗ {result_info['message']}"
                self.status_label.setStyleSheet("QLabel { color: red; }")
            
            self.status_label.setText(message)
            
            # Update results text
            stats = f"""
Rows processed: {result_info['rows_processed']}
Rows transformed: {result_info['rows_transformed']}
            """.strip()
            
            if result_info.get('warnings'):
                stats += f"\nWarnings: {len(result_info['warnings'])}"
            
            self.results_text.setText(stats)
    
    def _populate_results_table(self, statement):
        """Populate results table with transformed transactions."""
        transactions = statement.transactions[:50]  # Show first 50 transactions
        
        self.results_table.setRowCount(len(transactions))
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Date", "Description", "Amount"])
        
        for row, transaction in enumerate(transactions):
            self.results_table.setItem(row, 0, QTableWidgetItem(transaction.date))
            self.results_table.setItem(row, 1, QTableWidgetItem(transaction.description))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"£{transaction.amount:.2f}"))
        
        self.results_table.resizeColumnsToContents()
        
        if len(statement.transactions) > 50:
            self.results_text.setText(
                self.results_text.toPlainText() + 
                f"\nShowing first 50 of {len(statement.transactions)} transactions"
            )
    
    def _on_template_changed(self, _text: str):
        """Handle template selection change."""
        template = self.template_combo.currentData()
        self.viewmodel.selected_template = template
        self.transform_btn.setEnabled(self._can_transform())
        
        # Enable/disable edit and delete buttons based on template selection
        has_template = template is not None
        self.edit_template_btn.setEnabled(has_template)
        self.delete_template_btn.setEnabled(has_template)
    
    def _can_transform(self) -> bool:
        """Check if transformation can be performed."""
        return (self.viewmodel.uploaded_file_path is not None and 
                self.viewmodel.selected_template is not None and
                not self.viewmodel.is_loading)
    
    def _browse_file(self):
        """Open file browser dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Bank Statement",
            "",
            "Supported Files (*.csv *.xlsx *.xls);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            if self.viewmodel.upload_file(file_path):
                self.file_path_label.setText(Path(file_path).name)
                self.transform_btn.setEnabled(self._can_transform())
            else:
                self.file_path_label.setText("File upload failed")
    
    def _transform_statement(self):
        """Trigger statement transformation."""
        self.viewmodel.transform_statement()
        
  
    def _refresh_templates(self):
        """Refresh available templates."""
        self.viewmodel.refresh_templates()
    
    def _create_template(self):
        """Open template creation dialog."""
        try:
            from views.dialogs.template_editor_dialog import TemplateEditorDialog
            
            dialog = TemplateEditorDialog(self)
            if dialog.exec():
                self._refresh_templates()
        except ImportError:
            QMessageBox.information(
                self, 
                "Feature Unavailable", 
                "Template editor dialog is not available yet.\n"
                "Templates can be managed through the configuration files."
            )
    
    def _edit_template(self):
        """Open template editing dialog for the selected template."""
        template = self.template_combo.currentData()
        if not template:
            QMessageBox.warning(
                self, 
                "No Template Selected", 
                "Please select a template to edit."
            )
            return
        
        try:
            from views.dialogs.template_editor_dialog import TemplateEditorDialog
            
            dialog = TemplateEditorDialog(self, template=template)
            if dialog.exec():
                self._refresh_templates()
                # Try to reselect the edited template
                self._select_template_by_name(template.name)
        except ImportError:
            QMessageBox.information(
                self, 
                "Feature Unavailable", 
                "Template editor dialog is not available yet.\n"
                "Templates can be managed through the configuration files."
            )
    
    def _delete_template(self):
        """Delete the selected template after confirmation."""
        template = self.template_combo.currentData()
        if not template:
            QMessageBox.warning(
                self, 
                "No Template Selected", 
                "Please select a template to delete."
            )
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Delete Template", 
            f"Are you sure you want to delete the template '{template.name}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Check if viewmodel has delete method
                if hasattr(self.viewmodel, 'delete_template'):
                    success = self.viewmodel.delete_template(template)
                    if success:
                        QMessageBox.information(
                            self, 
                            "Template Deleted", 
                            f"Template '{template.name}' has been deleted successfully."
                        )
                        self._refresh_templates()
                    else:
                        QMessageBox.critical(
                            self, 
                            "Delete Failed", 
                            f"Failed to delete template '{template.name}'.\n"
                            f"Error: {getattr(self.viewmodel, 'error_message', 'Unknown error')}"
                        )
                else:
                    QMessageBox.information(
                        self, 
                        "Feature Unavailable", 
                        "Template deletion is not yet implemented.\n"
                        "Templates can be managed through the configuration files."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Delete Error", 
                    f"An error occurred while deleting the template:\n{str(e)}"
                )
    
    def _select_template_by_name(self, template_name):
        """Select a template in the combo box by name."""
        for i in range(self.template_combo.count()):
            template = self.template_combo.itemData(i)
            if template and template.name == template_name:
                self.template_combo.setCurrentIndex(i)
                break
    
    def _use_for_reconciliation(self):
        """Signal that this data should be used for reconciliation."""
        if self.viewmodel.transformed_statement:
            self.file_transformed.emit(self.viewmodel.transformed_statement)
    
    def _export_data(self):
        """Export transformed data to file."""
        if not self.viewmodel.transformed_statement:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Transformed Data",
            "transformed_statement.csv",
            "CSV Files (*.csv);;Excel Files (*.xlsx)"
        )
        
        if file_path:
            try:
                df = self.viewmodel.transformed_statement.to_dataframe()
                
                if file_path.endswith('.csv'):
                    df.to_csv(file_path, index=False)
                else:
                    df.to_excel(file_path, index=False)
                
                self.status_label.setText(f"✓ Data exported to {Path(file_path).name}")
                self.status_label.setStyleSheet("QLabel { color: green; }")
            except Exception as e:
                self.status_label.setText(f"✗ Export failed: {str(e)}")
                self.status_label.setStyleSheet("QLabel { color: red; }")

    def _clear_bank_data(self):
        """Clear bank data"""
        if hasattr(self.viewmodel, 'clear_bank_data'):
            self.viewmodel.clear_bank_data()
        
        # Reset UI to initial state
        self.file_path_label.setText("No file selected")
        self.template_combo.setCurrentIndex(0)  # Reset to "Select a bank template..."
        self.bank_summary_label.setText("Bank: No data")
        self.bank_summary_label.setStyleSheet("padding: 8px; background-color: #f0f0f0; border: 1px solid #ccc;")
        
        # Clear results and status
        self.results_table.setVisible(False)
        self.results_table.setRowCount(0)
        if hasattr(self, 'results_text'):
            self.results_text.clear() # Clear the results text
        self.status_label.setText("")  # Clear the status label
        self.status_label.setStyleSheet("")  # Reset styling

        # Reset button states
        self.transform_btn.setEnabled(False)
        self.use_for_reconciliation_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.edit_template_btn.setEnabled(False)
        self.delete_template_btn.setEnabled(False)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        logger.info("Bank data and UI state cleared")

    # ========================================================================
    # NEW SIGNAL HANDLERS - Enhanced functionality
    # ========================================================================
    
    @Slot(object, dict)
    def _on_bank_transformation_completed(self, statement, result_info):
        """Handle bank transformation completion - enhanced signal handler"""
        # Emit your existing signal for compatibility
        self.file_transformed.emit(statement)
        
        # Emit new enhanced signal
        self.bank_data_ready.emit(statement, result_info)
        
        # Note: Status message removed to avoid duplication with MainWindow message
        # The MainWindow will show the comprehensive "Bank Statement Ready" message
        
        logger.info(f"Bank transformation completed: {len(statement.transactions)} transactions")
    
    @Slot(str)
    def _on_transformation_failed(self, error_message):
        """Handle transformation failure"""
        self.status_label.setText(f"✗ Transformation failed: {error_message}")
        self.status_label.setStyleSheet("QLabel { color: red; }")
        
        # Emit error signal
        self.processing_error.emit('bank', error_message)
    