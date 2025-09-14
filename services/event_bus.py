# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""Simple event bus implementation for component communication"""

from PySide6.QtCore import QObject, Signal
from typing import Any
import logging

class EventBus(QObject):
    """Simple event bus for decoupled communication"""
    
    # Define signals using PySide6 Signal syntax
    event_emitted = Signal(str, object)  # event_name, data
    
    # Common application signals
    file_loaded = Signal(str, object)        # file_type, data
    matching_started = Signal()
    matching_completed = Signal(object)      # results
    settings_changed = Signal(str, object)   # setting_name, value
    error_occurred = Signal(str, str)        # context, error_message
    progress_updated = Signal(int)           # progress_percentage
 
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
    
    def publish(self, event_name: str, data: Any = None) -> None:
        """Emit a generic event."""
        # Emit Qt signal
        self.event_emitted.emit(event_name, data)

    def publish_file_loaded(self, file_type: str, data: object):
        """Convenience method for file loaded events"""
        self.file_loaded.emit(file_type, data)
        self.publish("file_loaded", {"type": file_type, "data": data})
    
    def publish_matching_started(self):
        """Convenience method for matching started events"""
        self.matching_started.emit()
        self.publish("matching_started")
    
    def publish_matching_completed(self, results: object):
        """Convenience method for matching completed events"""
        self.matching_completed.emit(results)
        self.publish("matching_completed", results)
    
    def publish_settings_changed(self, setting_name: str, value: object):
        """Convenience method for settings changed events"""
        self.settings_changed.emit(setting_name, value)
        self.publish("settings_changed", {"setting": setting_name, "value": value})
    
    def publish_error(self, context: str, error_message: str):
        """Convenience method for error events"""
        self.error_occurred.emit(context, error_message)
        self.publish("error_occurred", {"context": context, "message": error_message})
    
    def publish_progress(self, percentage: int):
        """Convenience method for progress updates"""
        self.progress_updated.emit(percentage)
        self.publish("progress_updated", percentage)
        