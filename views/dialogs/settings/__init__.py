# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""Settings dialogs package"""

import logging

logger = logging.getLogger(__name__)

try:
    from .threshold_settings_dialog import ThresholdSettingsDialog
except ImportError:
    logger.warning("Could not import ThresholdSettingsDialog")
    ThresholdSettingsDialog = None

try:
    from .oracle_connection_dialog import OracleConnectionDialog
except ImportError:
    logger.warning("Could not import OracleConnectionDialog")
    OracleConnectionDialog = None

try:
    from .account_settings_dialog import AccountSettingsDialog
except ImportError:
    logger.warning("Could not import AccountSettingsDialog") 
    AccountSettingsDialog = None

__all__ = [
    'ThresholdSettingsDialog',
    'OracleConnectionDialog',
    'AccountSettingsDialog'
]