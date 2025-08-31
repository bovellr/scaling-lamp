# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
"""Summary card widget"""

from PySide6.QtWidgets import QGroupBox, QHBoxLayout

from .summary_card import SummaryCard


class SummaryCardsWidget(QGroupBox):
    """Widget displaying account summary cards."""

    def __init__(self, parent=None):
        super().__init__("Account Summary", parent)
        layout = QHBoxLayout(self)

        self.cards = []
        for title, value, color in [
            ("GL Balance", "£0.00", "#3498db"),
            ("Bank Balance", "£0.00", "#2ecc71"),
            ("Matched Amount", "£0.00", "#27ae60"),
            ("Outstanding", "£0.00", "#e74c3c"),
        ]:
            card = SummaryCard(title, value)
            card.setStyleSheet(f"""
                SummaryCard {{
                    border: 2px solid {color};
                    border-radius: 8px;
                    background-color: white;
                    margin: 5px;
                }}
            """)
            layout.addWidget(card)
            self.cards.append(card)