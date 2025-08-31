# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""Filters widget"""

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QComboBox, QDateEdit, QSlider
from PySide6.QtCore import Qt


class FiltersWidget(QGroupBox):
    """Widget containing transaction filters and options."""

    def __init__(self, parent=None):
        super().__init__("Filters & Options", parent)
        layout = QHBoxLayout(self)

        layout.addWidget(QLabel("Transaction Type:"))
        self.combo_transaction_type = QComboBox()
        self.combo_transaction_type.addItems([
            "All Transactions", "Debits", "Credits", "Unmatched"
        ])
        layout.addWidget(self.combo_transaction_type)

        layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        layout.addWidget(self.date_from)

        layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        layout.addWidget(self.date_to)

        layout.addWidget(QLabel("Min Confidence:"))
        self.slider_confidence = QSlider(Qt.Horizontal)
        self.slider_confidence.setRange(0, 100)
        self.slider_confidence.setValue(60)
        layout.addWidget(self.slider_confidence)

        self.label_confidence_value = QLabel("60%")
        self.slider_confidence.valueChanged.connect(
            lambda v: self.label_confidence_value.setText(f"{v}%")
        )
        layout.addWidget(self.label_confidence_value)

        layout.addStretch()