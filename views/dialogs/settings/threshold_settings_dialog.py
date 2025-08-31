# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# views/dialogs/settings/threshold_settings_dialog.py
"""Threshold settings dialog"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLabel, 
                               QDoubleSpinBox, QPushButton, QHBoxLayout,
                               QGroupBox, QSlider, QSpinBox, QCheckBox,
                               QTextEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from config.settings import AppSettings


class ThresholdSettingsDialog(QDialog):
    """Dialog for configuring matching thresholds and AI parameters"""
    
    # Signal emitted when settings are applied
    settings_applied = Signal(dict)
    
    def __init__(self, app_settings: AppSettings, parent=None):
        super().__init__(parent)
        self.app_settings = app_settings
        self.setWindowTitle("Threshold Settings")
        self.setMinimumSize(500, 600)
        self.setModal(True)
        
        self.setup_ui()
        self.connect_signals()
        self.load_current_settings()
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Configure AI Matching Thresholds")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Confidence thresholds group
        confidence_group = QGroupBox("Confidence Thresholds")
        confidence_layout = QFormLayout(confidence_group)
        
        # High confidence threshold
        self.high_confidence = QDoubleSpinBox()
        self.high_confidence.setRange(0.70, 1.0)
        self.high_confidence.setSingleStep(0.01)
        self.high_confidence.setValue(0.85)
        self.high_confidence.setDecimals(2)
        self.high_confidence.setSuffix(" (85%+)")
        confidence_layout.addRow("High Confidence:", self.high_confidence)
        
        # Medium confidence threshold  
        self.medium_confidence = QDoubleSpinBox()
        self.medium_confidence.setRange(0.50, 0.85)
        self.medium_confidence.setSingleStep(0.01)
        self.medium_confidence.setValue(0.60)
        self.medium_confidence.setDecimals(2)
        self.medium_confidence.setSuffix(" (60-85%)")
        confidence_layout.addRow("Medium Confidence:", self.medium_confidence)
        
        # Low confidence is automatically everything below medium
        self.low_confidence_label = QLabel("< 60% (Requires Review)")
        self.low_confidence_label.setStyleSheet("color: #666; font-style: italic;")
        confidence_layout.addRow("Low Confidence:", self.low_confidence_label)
        
        layout.addWidget(confidence_group)
        
        # Matching tolerances group
        tolerance_group = QGroupBox("Matching Tolerances")
        tolerance_layout = QFormLayout(tolerance_group)
        
        # Amount tolerance
        self.amount_tolerance = QDoubleSpinBox()
        self.amount_tolerance.setRange(0.0, 100.0)
        self.amount_tolerance.setSingleStep(0.01)
        self.amount_tolerance.setValue(0.01)
        self.amount_tolerance.setDecimals(2)
        self.amount_tolerance.setPrefix("£")
        tolerance_layout.addRow("Amount Tolerance:", self.amount_tolerance)
        
        # Amount percentage tolerance
        self.amount_percentage = QDoubleSpinBox()
        self.amount_percentage.setRange(0.0, 10.0)
        self.amount_percentage.setSingleStep(0.1)
        self.amount_percentage.setValue(0.5)
        self.amount_percentage.setDecimals(1)
        self.amount_percentage.setSuffix("%")
        tolerance_layout.addRow("Amount % Tolerance:", self.amount_percentage)
        
        # Date tolerance
        self.date_tolerance = QSpinBox()
        self.date_tolerance.setRange(0, 30)
        self.date_tolerance.setValue(1)
        self.date_tolerance.setSuffix(" days")
        tolerance_layout.addRow("Date Tolerance:", self.date_tolerance)
        
        # Description similarity threshold
        self.description_similarity = QSlider(Qt.Horizontal)
        self.description_similarity.setRange(50, 100)
        self.description_similarity.setValue(70)
        self.description_similarity.setTickPosition(QSlider.TicksBelow)
        self.description_similarity.setTickInterval(10)
        
        self.description_label = QLabel("70%")
        self.description_similarity.valueChanged.connect(
            lambda v: self.description_label.setText(f"{v}%")
        )
        
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(self.description_similarity)
        desc_layout.addWidget(self.description_label)
        
        tolerance_layout.addRow("Description Similarity:", desc_layout)
        
        layout.addWidget(tolerance_group)
        
        # Advanced settings group
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        # Auto-match high confidence
        self.auto_match_high = QCheckBox("Automatically accept high confidence matches")
        self.auto_match_high.setChecked(True)
        advanced_layout.addRow("Auto-matching:", self.auto_match_high)
        
        # Review required for low confidence
        self.review_low = QCheckBox("Flag low confidence matches for manual review")
        self.review_low.setChecked(True)
        advanced_layout.addRow("Manual Review:", self.review_low)
        
        # Maximum combinations to process
        self.max_combinations = QSpinBox()
        self.max_combinations.setRange(1000, 1000000)
        self.max_combinations.setValue(50000)
        self.max_combinations.setSuffix(" combinations")
        advanced_layout.addRow("Max Combinations:", self.max_combinations)
        
        layout.addWidget(advanced_group)
        
        # Preview/explanation text
        preview_group = QGroupBox("Current Settings Summary")
        preview_layout = QVBoxLayout(preview_group)
        
        self.settings_preview = QTextEdit()
        self.settings_preview.setMaximumHeight(120)
        self.settings_preview.setReadOnly(True)
        preview_layout.addWidget(self.settings_preview)
        
        layout.addWidget(preview_group)
        
        # Update preview initially
        self.update_preview()
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        button_layout.addWidget(self.btn_reset)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_apply)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
    
    def connect_signals(self):
        """Connect UI signals"""
        self.btn_apply.clicked.connect(self.apply_settings)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_reset.clicked.connect(self.reset_to_defaults)
        
        # Update preview when values change
        self.high_confidence.valueChanged.connect(self.update_preview)
        self.medium_confidence.valueChanged.connect(self.update_preview)
        self.amount_tolerance.valueChanged.connect(self.update_preview)
        self.date_tolerance.valueChanged.connect(self.update_preview)
        self.description_similarity.valueChanged.connect(self.update_preview)
    
    def load_current_settings(self):
        """Load current threshold settings from AppSettings"""
        self.high_confidence.setValue(self.app_settings.high_confidence_threshold)
        self.medium_confidence.setValue(self.app_settings.medium_confidence_threshold)
        self.amount_tolerance.setValue(self.app_settings.amount_tolerance)
        self.amount_percentage.setValue(self.app_settings.amount_percentage_tolerance)
        self.date_tolerance.setValue(self.app_settings.date_tolerance_days)
        self.description_similarity.setValue(int(self.app_settings.description_similarity_threshold * 100))
        self.auto_match_high.setChecked(self.app_settings.auto_match_high_confidence)
        self.review_low.setChecked(self.app_settings.flag_low_confidence_for_review)
        self.max_combinations.setValue(self.app_settings.max_combinations)

        self.update_preview()
    
    def reset_to_defaults(self):
        """Reset all settings to default values"""
        self.high_confidence.setValue(0.85)
        self.medium_confidence.setValue(0.60)
        self.amount_tolerance.setValue(0.01)
        self.amount_percentage.setValue(0.5)
        self.date_tolerance.setValue(1)
        self.description_similarity.setValue(70)
        self.auto_match_high.setChecked(True)
        self.review_low.setChecked(True)
        self.max_combinations.setValue(50000)
    
    def apply_settings(self):
        """Apply the current settings"""
        settings = self.get_current_settings()
        
        # Update application settings
        self.app_settings.high_confidence_threshold = settings['high_confidence_threshold']
        self.app_settings.medium_confidence_threshold = settings['medium_confidence_threshold']
        self.app_settings.amount_tolerance = settings['amount_tolerance']
        self.app_settings.amount_percentage_tolerance = settings['amount_percentage_tolerance']
        self.app_settings.date_tolerance_days = settings['date_tolerance_days']
        self.app_settings.description_similarity_threshold = settings['description_similarity_threshold']
        self.app_settings.auto_match_high_confidence = settings['auto_match_high_confidence']
        self.app_settings.flag_low_confidence_for_review = settings['flag_low_confidence_for_review']
        self.app_settings.max_combinations = settings['max_combinations']
        # Mirror high threshold to legacy field
        self.app_settings.confidence_threshold = settings['high_confidence_threshold']
        self.app_settings.save()
        
        # Emit signal with new settings
        self.settings_applied.emit(settings)
        
        # Accept dialog
        self.accept()
    
    def get_current_settings(self):
        """Get current settings as dictionary"""
        return {
            'high_confidence_threshold': self.high_confidence.value(),
            'medium_confidence_threshold': self.medium_confidence.value(),
            'amount_tolerance': self.amount_tolerance.value(),
            'amount_percentage_tolerance': self.amount_percentage.value(),
            'date_tolerance_days': self.date_tolerance.value(),
            'description_similarity_threshold': self.description_similarity.value() / 100.0,
            'auto_match_high_confidence': self.auto_match_high.isChecked(),
            'flag_low_confidence_for_review': self.review_low.isChecked(),
            'max_combinations': self.max_combinations.value()
        }
    
    def get_thresholds(self):
        """Get high and medium thresholds (for backward compatibility)"""
        return self.high_confidence.value(), self.medium_confidence.value()
    
    def update_preview(self):
        """Update the settings preview text"""
        settings = self.get_current_settings()
        
        preview_text = f"""Current Threshold Configuration:

• High Confidence: {settings['high_confidence_threshold']:.2f} ({settings['high_confidence_threshold']*100:.0f}%)
• Medium Confidence: {settings['medium_confidence_threshold']:.2f} ({settings['medium_confidence_threshold']*100:.0f}%)
• Low Confidence: < {settings['medium_confidence_threshold']:.2f} (Requires Review)

Matching Tolerances:
• Amount: ±£{settings['amount_tolerance']:.2f} or ±{settings['amount_percentage_tolerance']:.1f}%
• Date: ±{settings['date_tolerance_days']} days
• Description: {settings['description_similarity_threshold']*100:.0f}% similarity minimum

Behavior:
• Auto-match high confidence: {'Yes' if settings['auto_match_high_confidence'] else 'No'}
• Review low confidence: {'Yes' if settings['flag_low_confidence_for_review'] else 'No'}
• Max combinations: {settings['max_combinations']:,}"""
        
        self.settings_preview.setText(preview_text)