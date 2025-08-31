# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
"""Summary card widget"""

from typing import Optional
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel

class SummaryCard(QFrame):
    """
    A reusable summary card widget for displaying financial metrics
    like balances or matched/outstanding values.
    """

    def __init__(self, title: str, value: str, currency_symbol: Optional[str] = None):
        super().__init__()

        # Persist underlying value and currency for later updates
        if currency_symbol is None:
            currency_symbol, value = self._split_currency(value)
        self._value = value
        self._currency_symbol = currency_symbol or ""

        # Frame style
        self.setFrameShape(QFrame.Box)
        self.setObjectName(title.lower().replace(" ", "_"))
        self.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                padding: 10px;
                border-radius: 10px;
            }
            QLabel#title {
                font-size: 10pt;
                color: #333;
            }
            QLabel#value {
                font-size: 14pt;
                font-weight: bold;
            }
        """)

        # Vertical layout inside the card
        layout = QVBoxLayout(self)

        # Title label
        self.label_title = QLabel(title)
        self.label_title.setObjectName("title")

        # Value label
        self.label_value = QLabel(self._format_value())
        self.label_value.setObjectName("value")

        layout.addWidget(self.label_title)
        layout.addWidget(self.label_value)
        layout.addStretch()

    def _split_currency(self, value: str) -> tuple[str, str]:
        """Separate a currency symbol from the value string if present."""
        if value and not value[0].isdigit() and value[0] not in "-":
            return value[0], value[1:]
        return "", value

    def _format_value(self) -> str:
        """Return the formatted value with currency symbol."""
        return f"{self._currency_symbol}{self._value}"

    # Public API -------------------------------------------------
    def update_value(self, value: str) -> None:
        """Update the numeric/textual value displayed on the card."""
        self._value = value
        self.label_value.setText(self._format_value())

    def update_currency(self, currency_symbol: str) -> None:
        """Update the currency symbol displayed on the card."""
        self._currency_symbol = currency_symbol
        self.label_value.setText(self._format_value())


