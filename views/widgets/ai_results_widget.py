# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""AI results widget"""

from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


class AiResultsWidget(QGroupBox):
    """Widget displaying AI matching results and actions."""

    def __init__(self, parent=None):
        super().__init__("AI Matching Results", parent)
        layout = QVBoxLayout(self)

        confidence_layout = QHBoxLayout()
        self.lbl_high = QLabel("High Confidence (>85%): 0", alignment=Qt.AlignCenter)
        self.lbl_med = QLabel("Medium Confidence (60-85%): 0", alignment=Qt.AlignCenter)
        self.lbl_low = QLabel("Low Confidence (<60%): 0", alignment=Qt.AlignCenter)
        self.lbl_high.setStyleSheet("background-color: #d4edda; padding: 10px; border-radius: 5px; font-weight: bold;")
        self.lbl_med.setStyleSheet("background-color: #fff3cd; padding: 10px; border-radius: 5px; font-weight: bold;")
        self.lbl_low.setStyleSheet("background-color: #f8d7da; padding: 10px; border-radius: 5px; font-weight: bold;")
        confidence_layout.addWidget(self.lbl_high)
        confidence_layout.addWidget(self.lbl_med)
        confidence_layout.addWidget(self.lbl_low)
        layout.addLayout(confidence_layout)

        metrics_layout = QHBoxLayout()
        self.lbl_accuracy = QLabel("Model Accuracy: Not Available")
        self.lbl_precision = QLabel("Precision: Not Available")
        metrics_layout.addWidget(self.lbl_accuracy)
        metrics_layout.addWidget(self.lbl_precision)
        metrics_layout.addStretch()
        layout.addLayout(metrics_layout)

        action_layout = QHBoxLayout()
        self.btn_review_low = QPushButton("Review Low Confidence Matches")
        self.btn_export_model = QPushButton("Export AI Model")
        action_layout.addStretch()
        action_layout.addWidget(self.btn_review_low)
        action_layout.addWidget(self.btn_export_model)
        layout.addLayout(action_layout)