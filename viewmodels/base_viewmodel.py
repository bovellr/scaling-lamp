# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# viewmodels/base_viewmodel.py
"""
Base ViewModel with common functionality for MVVM pattern.
"""

from abc import ABC
from typing import Any, Callable, Dict, List
import logging
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

class BaseViewModel(QObject):
    """Base class for all ViewModels providing common functionality."""

    # Generic signal emitted whenever a property changes.  The name of the
    # property and its new value are provided so that QML or other Qt widgets
    # can react without needing a dedicated signal for every property.
    property_changed = Signal(str, object)
    
    def __init__(self):
        super().__init__()
        self._property_changed_callbacks: Dict[str, List[Callable[[Any], None]]] = {}
        self._is_loading = False
        self._error_message = ""
    
    # ------------------------------------------------------------------
    # Property change helpers
    # ------------------------------------------------------------------
    def bind_property_changed(self, property_name: str, callback: Callable[[Any], None]) -> None:
        """Bind *callback* to changes of ``property_name``.

        This is mainly used in tests or plain-Python components that do not rely
        on Qt's signal system.  Callbacks are invoked with the new value of the
        property when :meth:`notify_property_changed` is called.
        """
        self._property_changed_callbacks.setdefault(property_name, []).append(callback)

    def notify_property_changed(self, property_name: str, new_value: Any = None) -> None:
        """Notify registered callbacks and emit the generic Qt signal."""
        for callback in self._property_changed_callbacks.get(property_name, []):
            try:
                callback(new_value)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Error in property changed callback: %s", exc)

        # Emit Qt signal for any interested views
        self.property_changed.emit(property_name, new_value)
    

    # ------------------------------------------------------------------
    # Common properties
    # ------------------------------------------------------------------
    @property
    def is_loading(self) -> bool:
        """Whether the view model is performing a long‑running operation."""
        return self._is_loading
    
    @is_loading.setter
    def is_loading(self, value: bool) -> None:
        if self._is_loading != value:
            self._is_loading = value
            self.notify_property_changed("is_loading", value)
    
    @property
    def error_message(self) -> str:
        """Error message to display to the user."""
        return self._error_message
    
    @error_message.setter
    def error_message(self, value: str) -> None:
        if self._error_message != value:
            self._error_message = value
            self.notify_property_changed("error_message", value)
    
    # ------------------------------------------------------------------
    # Error helpers
    # ------------------------------------------------------------------
    def clear_error(self) -> None:
        """Clear any existing error message."""
        self.error_message = ""

    def set_error(self, message: str) -> None:
        """Set and log an error message.

        Parameters
        ----------
        message:
            Human readable description of the error.
        """
        logger.error(message)
        self.error_message = message