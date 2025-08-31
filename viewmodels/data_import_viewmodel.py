# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# viewmodels/data_import_viewmodel.py
"""Aggregate ViewModel for importing bank and ERP data.

The application allows users to import bank statements from files and to pull
ERP transactions from configured databases.  This view model simply exposes the
existing upload and ERP database view models under a single roof so the main
window can work with a single abstraction for the "Data Import" tab.
"""

from PySide6.QtCore import Signal

from .base_viewmodel import BaseViewModel
from .upload_viewmodel import UploadViewModel
from .erp_database_viewmodel import ERPDatabaseViewModel


class DataImportViewModel(BaseViewModel):
    """Coordinates the different data import mechanisms."""

    data_imported = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.upload_vm = UploadViewModel()
        self.erp_vm = ERPDatabaseViewModel()

    def import_bank_file(self, path: str, template_type: str) -> bool:
        """Convenience wrapper around :class:`UploadViewModel`.

        Parameters
        ----------
        path:
            File path to the bank statement.
        template_type:
            Identifier of the bank template to use.
        """
        template = self.upload_vm.get_template_by_type(template_type)
        if template is None:
            self.set_error("Template not found")
            return False
        self.upload_vm.selected_template = template
        if self.upload_vm.upload_file(path) and self.upload_vm.transform_statement():
            self.data_imported.emit()
            return True
        return False