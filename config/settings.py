# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
"""Application settings management"""

try:
    from PySide6.QtCore import QSettings
except ImportError:  # Provide minimal stub for non-GUI environments
    class QSettings(dict):
        def __init__(self, *_, **__):
            self.store = {}

        def value(self, key, default=None):
            return self.store.get(key, default)

        def setValue(self, key, value):
            self.store[key] = value

        def sync(self):
            pass
from typing import Optional, Any
import logging
from .constants import *

class AppSettings:
    """Application settings management using QSettings"""

    def __init__(self):
        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        self.logger = logging.getLogger(__name__)
        self.load_settings()

    def _get_bool(self, key: str, default: bool) -> bool:
        """Retrieve a boolean setting, normalising string values."""
        value = self.settings.value(key, default)
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "y")
        return bool(value)

    def load_settings(self) -> None:
        """Load settings from storage"""
        # Window settings
        self.window_geometry = self.settings.value("window/geometry")
        self.window_state = self.settings.value("window/state")
        
        # Application settings
        # Legacy single threshold (kept for backward compatibility)
        self.confidence_threshold = float(
            self.settings.value("matching/confidence_threshold", DEFAULT_CONFIDENCE_THRESHOLD)
        )

        # Advanced matching thresholds
        self.high_confidence_threshold = float(
            self.settings.value("matching/high_confidence_threshold", self.confidence_threshold)
        )
        self.medium_confidence_threshold = float(
            self.settings.value("matching/medium_confidence_threshold", 0.60)
        )
        self.amount_tolerance = float(
            self.settings.value("matching/amount_tolerance", 0.01)
        )
        self.amount_percentage_tolerance = float(
            self.settings.value("matching/amount_percentage_tolerance", 0.5)
        )
        self.date_tolerance_days = int(
            self.settings.value("matching/date_tolerance_days", 1)
        )
        self.description_similarity_threshold = float(
            self.settings.value("matching/description_similarity_threshold", 0.80)
        )
        self.auto_match_high_confidence = self._get_bool(
            "matching/auto_match_high_confidence", True
        )
        self.flag_low_confidence_for_review = self._get_bool(
            "matching/flag_low_confidence_for_review", True
        )
        self.max_combinations = int(
            self.settings.value("matching/max_combinations", 50000)
        )

        # ML settings
        self.auto_retrain = self._get_bool("ml/auto_retrain", False)
        self.retrain_threshold = int(self.settings.value("ml/retrain_threshold", AUTO_RETRAIN_THRESHOLD))
        
        # File paths
        self.last_bank_dir = self.settings.value("files/last_bank_dir", "")
        self.last_erp_dir = self.settings.value("files/last_erp_dir", "")
        self.last_export_dir = self.settings.value("files/last_export_dir", "")
        
        # UI preferences
        self.theme = self.settings.value("ui/theme", "light")
        self.table_row_height = int(self.settings.value("ui/table_row_height", TABLE_ROW_HEIGHT))
        
    def save(self) -> None:
        """Save current settings"""
        try:
            if hasattr(self, 'window_geometry') and self.window_geometry:
                self.settings.setValue("window/geometry", self.window_geometry)
            if hasattr(self, 'window_state') and self.window_state:
                self.settings.setValue("window/state", self.window_state)
            
            # Legacy single threshold mirrors the high confidence threshold
            self.confidence_threshold = self.high_confidence_threshold
            self.settings.setValue("matching/confidence_threshold", self.confidence_threshold)
            self.settings.setValue("matching/high_confidence_threshold", self.high_confidence_threshold)
            self.settings.setValue("matching/medium_confidence_threshold", self.medium_confidence_threshold)
            self.settings.setValue("matching/amount_tolerance", self.amount_tolerance)
            self.settings.setValue("matching/amount_percentage_tolerance", self.amount_percentage_tolerance)
            self.settings.setValue("matching/date_tolerance_days", self.date_tolerance_days)
            self.settings.setValue("matching/description_similarity_threshold", self.description_similarity_threshold)
            self.settings.setValue("matching/auto_match_high_confidence", self.auto_match_high_confidence)
            self.settings.setValue("matching/flag_low_confidence_for_review", self.flag_low_confidence_for_review)
            self.settings.setValue("matching/max_combinations", self.max_combinations)
            self.settings.setValue("ml/auto_retrain", self.auto_retrain)
            self.settings.setValue("ml/retrain_threshold", self.retrain_threshold)
            
            self.settings.setValue("files/last_bank_dir", self.last_bank_dir)
            self.settings.setValue("files/last_erp_dir", self.last_erp_dir)
            self.settings.setValue("files/last_export_dir", self.last_export_dir)
            
            self.settings.setValue("ui/theme", self.theme)
            self.settings.setValue("ui/table_row_height", self.table_row_height)
            
            self.settings.sync()
            self.logger.debug("Settings saved")
            
        except (TypeError, OSError) as e:
            self.logger.error("Failed to save settings: %s", e)
            raise
