# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""Simple event bus implementation for component communication"""

from PySide6.QtCore import QObject, Signal
from typing import Dict, List, Callable, Any
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
        self._subscribers: Dict[str, List[Callable]] = {}
        self._error_handlers: List[Callable[[str, Exception], None]] = []

    def subscribe(self, event_name: str, callback: Callable) -> None:
        """Subscribe to an event
        
        Args:
            event_name: The name of the event to subscribe to
            callback: The function to call when the event is emitted

        Returns:
            None
        """
        
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)
            self.logger.debug(f"Subscribed to event: {event_name}")
    
    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """
        Unsubscribe from an event
        
        Args:
            event_name: Name of the event to unsubscribe from
            callback: Function to remove from callbacks
        """
        if event_name in self._subscribers:
            try:
                self._subscribers[event_name].remove(callback)
                self.logger.debug(f"Unsubscribed from event: {event_name}")
            except ValueError:
                self.logger.warning(f"Callback not found for event: {event_name}")
    
    
    def publish(self, event_name: str, data: Any = None) -> None:
        """
        Publish an event to all subscribers
        Args:
            event_name: Name of the event to emit
            data: Data to pass to callbacks
        """

        # Emit Qt signal
        self.event_emitted.emit(event_name, data)

        # Call direct subscribers
        if event_name in self._subscribers:
            for callback in self._subscribers[event_name][:]:
                try:
                    if data is not None:
                        callback(data)
                    else:
                        callback()
                except Exception as e:
                    self.logger.error(f"Error in callback for event {event_name}: {e}")
                    
                    # Call error handlers
                    for error_handler in self._error_handlers:
                        try:
                            error_handler(event_name, e)
                        except Exception as handler_error:
                            self.logger.error(f"Error in error handler: {handler_error}")
                    
                    # Re-raise the original exception
                    raise

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
    
    def add_error_handler(self, handler: Callable[[str, Exception], None]) -> None:
        """Add an error handler for callback exceptions"""
        self._error_handlers.append(handler)
    
    def clear_subscribers(self, event_name: str = None) -> None:
        """Clear subscribers for a specific event or all events"""
        if event_name:
            if event_name in self._subscribers:
                self._subscribers[event_name].clear()
                self.logger.info(f"Cleared subscribers for event: {event_name}")
        else:
            self._subscribers.clear()
            self.logger.info("Cleared all subscribers")    
    