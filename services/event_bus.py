# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""Simple event bus implementation for component communication"""

from PySide6.QtCore import QObject, Signal
from typing import Any, Dict, List
import logging
import weakref

class EventBus(QObject):
    """Simple event bus for decoupled communication with memory leak prevention"""
    
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
        self._subscribers: Dict[str, List[callable]] = {}
        self._weak_refs: List[weakref.ref] = []
        
    
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
    
    def subscribe(self, event_name: str, callback: callable) -> None:
        """Subscribe to an event with weak reference to prevent memory leaks"""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        
        # Use weak reference to prevent memory leaks
        weak_callback = weakref.ref(callback)
        self._subscribers[event_name].append(weak_callback)
        self._weak_refs.append(weak_callback)
    
    def unsubscribe(self, event_name: str, callback: callable) -> None:
        """Unsubscribe from an event"""
        if event_name in self._subscribers:
            # Find and remove the weak reference
            for weak_callback in self._subscribers[event_name][:]:
                if weak_callback() == callback:
                    self._subscribers[event_name].remove(weak_callback)
                    if weak_callback in self._weak_refs:
                        self._weak_refs.remove(weak_callback)
                    break
    
    def cleanup_weak_refs(self) -> None:
        """Clean up dead weak references"""
        for event_name in list(self._subscribers.keys()):
            self._subscribers[event_name] = [
                ref for ref in self._subscribers[event_name] 
                if ref() is not None
            ]
            if not self._subscribers[event_name]:
                del self._subscribers[event_name]
        
        self._weak_refs = [ref for ref in self._weak_refs if ref() is not None]
        