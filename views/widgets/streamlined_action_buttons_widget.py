# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# STREAMLINED ACTION BUTTONS WIDGETS
# ============================================================================

# views/widgets/streamlined_action_buttons_widget.py
"""
Streamlined action buttons widget with no duplicate import functionality
"""
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar, QLabel
from PySide6.QtCore import Signal, Slot
from typing import Optional

class StreamlinedActionButtonsWidget(QGroupBox):
    """Streamlined action buttons focused only on reconciliation operations"""
    
    # Signals
    train_model_requested = Signal()
    import_training_requested = Signal()
    auto_reconcile_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__("Reconciliation Operations", parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup UI with only reconciliation-specific actions"""
        layout = QVBoxLayout(self)
        
        # Main action buttons
        main_buttons_layout = QHBoxLayout()
        
        self.btn_import_training = QPushButton("Import Training Data")
        self.btn_train_model = QPushButton("Train AI Model")
        self.btn_auto_reconcile = QPushButton("Auto Reconcile")
        
        # Set initial states
        self.btn_auto_reconcile.setEnabled(False)  # Enabled when data is ready
        
        # Style the reconcile button as primary action
        self.btn_auto_reconcile.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
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
        
        # Connect signals
        self.btn_import_training.clicked.connect(self.import_training_requested.emit)
        self.btn_train_model.clicked.connect(self.train_model_requested.emit)
        self.btn_auto_reconcile.clicked.connect(self.auto_reconcile_requested.emit)
        
        main_buttons_layout.addWidget(self.btn_import_training)
        main_buttons_layout.addWidget(self.btn_train_model)
        main_buttons_layout.addStretch()
        main_buttons_layout.addWidget(self.btn_auto_reconcile)
        
        layout.addLayout(main_buttons_layout)
        
        # Progress section
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("")
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
    
    def set_data_ready(self, ready: bool):
        """Enable/disable reconcile button based on data readiness"""
        self.btn_auto_reconcile.setEnabled(ready)
        if ready:
            self.status_label.setText("✓ Ready for reconciliation")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("⚠ Waiting for both bank and ERP data")
            self.status_label.setStyleSheet("color: orange;")
    
    def set_operation_in_progress(self, operation: str, in_progress: bool):
        """Show progress for long-running operations"""
        if in_progress:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.status_label.setText(f"{operation} in progress...")
            self.status_label.setStyleSheet("color: blue;")
            
            # Disable buttons during operation
            self.btn_import_training.setEnabled(False)
            self.btn_train_model.setEnabled(False)
            self.btn_auto_reconcile.setEnabled(False)
        else:
            self.progress_bar.setVisible(False)
            self.status_label.setText(f"{operation} completed")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Re-enable buttons
            self.btn_import_training.setEnabled(True)
            self.btn_train_model.setEnabled(True)
            # Reconcile button state depends on data availability
            # This will be set by the main window based on data service state
