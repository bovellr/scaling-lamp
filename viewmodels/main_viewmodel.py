# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# viewmodels/main_viewmodel.py
# ================================

from PySide6.QtCore import Signal, Property

from .base_viewmodel import BaseViewModel
from .training_viewmodel import TrainingViewModel
from .reconciliation_viewmodel import ReconciliationViewModel
from .data_import_viewmodel import DataImportViewModel
from .reporting_viewmodel import ReportingViewModel
from .settings_viewmodel import SettingsViewModel

class MainViewModel(BaseViewModel):
    """Main application ViewModel coordinating all sub-ViewModels."""
    
    # Signals  for high level UI bindings
    current_tab_changed = Signal(str)
    status_message_changed = Signal(str)
    
    def __init__(self) -> None:
        super().__init__()
        
        # Sub-ViewModels
        self.training_vm = TrainingViewModel()
        self.reconciliation_vm = ReconciliationViewModel()
        self.data_import_vm = DataImportViewModel()
        self.reporting_vm = ReportingViewModel()
        self.settings_vm = SettingsViewModel()
        
        # Properties
        self._current_tab = "data_import"
        self._status_message = "Ready"
        
        # Connect child view models to update the status bar
        self._connect_sub_viewmodels()
    
    def _connect_sub_viewmodels(self):
        """Connect signals from sub-ViewModels."""
        # Training events
        self.training_vm.training_started.connect(
            lambda: self._set_status_message("Training started...")
        )
        self.training_vm.training_completed.connect(
            lambda result: self._set_status_message(
                f"Training completed: {result.test_accuracy:.3f} accuracy")
        )
        self.training_vm.training_failed.connect(
            lambda error: self._set_status_message(f"Training failed: {error}")
        )
        
        # Reconciliation events
        self.reconciliation_vm.reconciliation_started.connect(
            lambda: self._set_status_message("Reconciliation in progress...")
        )
        self.reconciliation_vm.reconciliation_completed.connect(
            lambda matches: self._set_status_message(
                f"Reconciliation completed: {len(matches)} matches found")
        )

        self.reconciliation_vm.reconciliation_failed.connect(
            lambda err: self._set_status_message(f"Reconciliation failed: {err}")
        )

        # Data import events
        self.data_import_vm.data_imported.connect(
            lambda: self._set_status_message("Data imported successfully")
        )

        # Reporting events
        self.reporting_vm.report_generated.connect(
            lambda _: self._set_status_message("Report generated")
        )

        # Settings events
        self.settings_vm.settings_saved.connect(
            lambda: self._set_status_message("Settings saved")
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @Property(str, notify=current_tab_changed)
    def current_tab(self) -> str:
        """Currently active tab."""
        return self._current_tab
    
    @current_tab.setter
    def current_tab(self, value: str):
        """Set current tab."""
        if self._current_tab != value:
            self._current_tab = value
            self.current_tab_changed.emit(value)
    
    @Property(str, notify=status_message_changed)
    def status_message(self) -> str:
        """Current status message."""
        return self._status_message
    
    def _set_status_message(self, message: str) -> None:
        """Update and emit the status message."""
        if self._status_message != message:
            self._status_message = message
            self.status_message_changed.emit(message)