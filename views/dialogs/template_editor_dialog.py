# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# views/dialogs/template_editor_dialog.py
"""Dialog for creating or editing bank statement parsing templates."""

from __future__ import annotations

from typing import Optional
import json

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)

from models.data_models import BankTemplate
from models.database import TemplateRepository


class TemplateEditorDialog(QDialog):
    """Simple editor for :class:`BankTemplate` objects."""

    def __init__(self, parent=None, template: Optional[BankTemplate] = None):
        super().__init__(parent)
        self._repo = TemplateRepository()
        self.template = template

        self.setWindowTitle("Edit Template" if template else "New Template")
        self.resize(500, 500)
        self._setup_ui()
        if template:
            self._populate_fields()

    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.bank_type_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.headers_edit = QLineEdit()
        self.date_patterns_edit = QLineEdit()
        self.skip_keywords_edit = QLineEdit()
        self.column_mapping_edit = QTextEdit()

        form.addRow("Template Name:", self.name_edit)
        form.addRow("Bank Type:", self.bank_type_edit)
        form.addRow("Description:", self.description_edit)
        form.addRow("Header Keywords (comma-separated):", self.headers_edit)
        form.addRow("Date Patterns (comma-separated regex):", self.date_patterns_edit)
        form.addRow("Skip Keywords (comma-separated):", self.skip_keywords_edit)
        form.addRow("Column Mapping (JSON):", self.column_mapping_edit)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self._save)
        self.cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

    # ------------------------------------------------------------------
    def _populate_fields(self) -> None:
        t = self.template
        self.name_edit.setText(t.name)
        self.bank_type_edit.setText(t.bank_type)
        self.description_edit.setPlainText(t.description)
        self.headers_edit.setText(", ".join(t.header_keywords))
        self.date_patterns_edit.setText(", ".join(t.date_patterns))
        self.skip_keywords_edit.setText(", ".join(t.skip_keywords))
        self.column_mapping_edit.setPlainText(json.dumps(t.column_mapping, indent=2))

    # ------------------------------------------------------------------
    def _save(self) -> None:
        try:
            name = self.name_edit.text().strip()
            bank_type = self.bank_type_edit.text().strip()
            if not name or not bank_type:
                QMessageBox.warning(self, "Validation", "Name and bank type are required.")
                return

            header_keywords = [s.strip() for s in self.headers_edit.text().split(",") if s.strip()]
            date_patterns = [s.strip() for s in self.date_patterns_edit.text().split(",") if s.strip()]
            skip_keywords = [s.strip() for s in self.skip_keywords_edit.text().split(",") if s.strip()]

            column_mapping: dict = {}
            mapping_text = self.column_mapping_edit.toPlainText().strip()
            if mapping_text:
                try:
                    column_mapping = json.loads(mapping_text)
                except json.JSONDecodeError as e:
                    QMessageBox.critical(
                        self,
                        "Validation",
                        f"Invalid JSON for column mapping: {e}",
                    )
                    return

            template = BankTemplate(
                name=name,
                bank_type=bank_type,
                header_keywords=header_keywords,
                date_patterns=date_patterns,
                skip_keywords=skip_keywords,
                column_mapping=column_mapping,
                description=self.description_edit.toPlainText().strip(),
            )

            if self._repo.save_template(template):
                QMessageBox.information(self, "Template Saved", "Template saved successfully.")
                self.accept()
            else:
                QMessageBox.critical(self, "Save Failed", "Unable to save template.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save template: {e}")