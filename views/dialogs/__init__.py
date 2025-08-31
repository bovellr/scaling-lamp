# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
"""Dialogs package for Bank Reconciliation AI"""

import logging

logger = logging.getLogger(__name__)

# Import main dialog classes to make them available at package level
try:
    from .dialog_manager import DialogManager
except ImportError:
    logger.warning("Could not import DialogManager")
    DialogManager = None

try:
    from .account_config_dialog import AccountConfigDialog
except ImportError:
    logger.warning("Could not import AccountConfigDialog")
    AccountConfigDialog = None

# Template editor dialog
try:
    from .template_editor_dialog import TemplateEditorDialog
except ImportError:
    logger.warning("Could not import TemplateEditorDialog")
    TemplateEditorDialog = None

# Import settings dialogs
try:
    from .settings.threshold_settings_dialog import ThresholdSettingsDialog
    from .settings.oracle_connection_dialog import OracleConnectionDialog
except ImportError as e:
    print(f"Warning: Could not import settings dialogs: {e}")
    ThresholdSettingsDialog = None
    OracleConnectionDialog = None

__all__ = [
    'DialogManager',
    'AccountConfigDialog', 
    'TemplateEditorDialog',
    'ThresholdSettingsDialog',
    'OracleConnectionDialog'
]