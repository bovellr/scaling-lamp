# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""Action buttons widget""" 

from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton


class ActionButtonsWidget(QGroupBox):
    """Widget containing data import and processing buttons."""

    def __init__(self, parent=None):
        super().__init__("Data Import & Processing", parent)
        layout = QVBoxLayout(self)

        row1 = QHBoxLayout()
        self.btn_import_bank = QPushButton("Import Bank Statement")
        self.btn_import_gl = QPushButton("Import GL Balances")
        self.btn_auto_match = QPushButton("Auto Reconcile")
        self.btn_auto_match.setEnabled(False)
        row1.addWidget(self.btn_import_bank)
        row1.addWidget(self.btn_import_gl)
        row1.addWidget(self.btn_auto_match)

        row2 = QHBoxLayout()
        self.btn_train_model = QPushButton("Train AI Model")
        self.btn_import_training = QPushButton("Import Training Data")
        row2.addWidget(self.btn_train_model)
        row2.addWidget(self.btn_import_training)
        row2.addStretch()

        layout.addLayout(row1)
        layout.addLayout(row2)