# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# viewmodels/settings_viewmodel.py
"""ViewModel wrapper around application settings."""

from PySide6.QtCore import Signal

from .base_viewmodel import BaseViewModel
from config.settings import AppSettings


class SettingsViewModel(BaseViewModel):
    """Expose :class:`AppSettings` values for the UI."""

    settings_saved = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._settings = AppSettings()

    # Simple example property: theme ------------------------------------
    @property
    def theme(self) -> str:
        return self._settings.theme

    @theme.setter
    def theme(self, value: str) -> None:
        if self._settings.theme != value:
            self._settings.theme = value
            self.notify_property_changed("theme", value)

    def save(self) -> None:
        """Persist the current settings to disk."""
        self._settings.save()
        self.settings_saved.emit()