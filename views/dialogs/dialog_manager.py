# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
"""Dialog manager"""

from pathlib import Path
import logging

from PySide6.QtCore import Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

from models.database_models import DatabaseConnection
from models.erp_repository import ERPConfigurationRepository

logger = logging.getLogger(__name__)

# Import from the correct paths based on your file structure
try:
    from .settings.threshold_settings_dialog import ThresholdSettingsDialog
except ImportError as e:
    logger.warning(f"Could not import ThresholdSettingsDialog: {e}")
    ThresholdSettingsDialog = None

try:
    from .settings.oracle_connection_dialog import OracleConnectionDialog
except ImportError as e:
    logger.warning(f"Could not import OracleConnectionDialog: {e}")
    OracleConnectionDialog = None

try:
    from .account_config_dialog import AccountConfigDialog
except ImportError as e:
    logger.warning(f"Could not import AccountConfigDialog: {e}")
    AccountConfigDialog = None

class DialogManager:
    """Dialog manager for handling various application dialogs"""

    def __init__(self, parent):
        self.parent = parent

    @Slot()
    def open_threshold_dialog(self):
        """Open threshold settings dialog"""
        if ThresholdSettingsDialog is None:
            QMessageBox.information(
                self.parent, 
                "Feature Unavailable", 
                "Threshold Settings dialog is not available.\n\n"
                "Please check that threshold_settings_dialog.py exists in the settings folder."
            )
            return
            
        try:
            dialog = ThresholdSettingsDialog(self.parent.settings, self.parent)
            if dialog.exec():
                if hasattr(dialog, 'get_thresholds'):
                    high, medium = dialog.get_thresholds()
                    logger.info(f"Updated thresholds: High={high}, Medium={medium}")
                    
                    # Apply thresholds to app logic 
                    self._apply_thresholds(high, medium)
                else:
                    logger.info("Threshold dialog completed successfully")
                    
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Dialog Error",
                f"Failed to open Threshold Settings dialog:\n{str(e)}"
            )
            logger.error(f"Error opening threshold dialog: {e}")

    @Slot()
    def open_oracle_dialog(self):
        """Open Oracle connection dialog"""
        if OracleConnectionDialog is None:
            QMessageBox.information(
                self.parent, 
                "Feature Unavailable", 
                "Oracle Connection dialog is not available.\n\n"
                "Please check that oracle_connection_dialog.py exists in the settings folder."
            )
            return
            
        try:
            dialog = OracleConnectionDialog(self.parent)
            if dialog.exec():
                # Get connection details from the dialog
                if hasattr(dialog, 'get_connection_details'):
                    connection_details = dialog.get_connection_details()
                else:
                    # Fallback method to extract details
                    connection_details = self._extract_oracle_details(dialog)
                
                logger.info(f"Oracle connection configured: {connection_details}")
                
                # Save connection details
                self._save_oracle_connection(connection_details)
                
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Dialog Error", 
                f"Failed to open Oracle Connection dialog:\n{str(e)}"
            )
            logger.error(f"Error opening Oracle dialog: {e}")

    @Slot()
    def open_account_config_dialog(self):
        """Open account configuration dialog"""
        if AccountConfigDialog is None:
            QMessageBox.information(
                self.parent, 
                "Feature Unavailable", 
                "Account Configuration dialog is not available.\n\n"
                "Please check that account_config_dialog.py exists in the dialogs folder."
            )
            return
            
        try:
            # Get current accounts from parent if available
            current_accounts = {}
            if hasattr(self.parent, 'bank_accounts_config'):
                current_accounts = self.parent.bank_accounts_config
            
            dialog = AccountConfigDialog(current_accounts, self.parent)
            if dialog.exec():
                logger.info("Account configuration updated successfully")
                
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Dialog Error", 
                f"Failed to open Account Configuration dialog:\n{str(e)}"
            )
            logger.error(f"Error opening account config dialog: {e}")

    def _extract_oracle_details(self, dialog):
        """Extract Oracle connection details from dialog (fallback method)"""
        try:
            details = {}
            
            # Extract basic fields if they exist
            if hasattr(dialog, 'username') and hasattr(dialog.username, 'text'):
                details['username'] = dialog.username.text()
            if hasattr(dialog, 'host') and hasattr(dialog.host, 'text'):
                details['host'] = dialog.host.text()
            if hasattr(dialog, 'port') and hasattr(dialog.port, 'text'):
                details['port'] = dialog.port.text()
            if hasattr(dialog, 'sid') and hasattr(dialog.sid, 'text'):
                details['sid'] = dialog.sid.text()
            if hasattr(dialog, 'service_name') and hasattr(dialog.service_name, 'text'):
                details['service_name'] = dialog.service_name.text()
            if hasattr(dialog, 'connection_type') and hasattr(dialog.connection_type, 'currentText'):
                details['connection_type'] = dialog.connection_type.currentText()
                
            return details
            
        except Exception as e:
            logger.error(f"Error extracting Oracle connection details: {e}")
            return {}

    def _save_oracle_connection(self, connection_details):
        """Persist Oracle connection details using repository"""
        try:
            repo = ERPConfigurationRepository()

            connection = DatabaseConnection(
                name=connection_details.get('name', 'OracleERP'),
                connection_type='oracle',
                host=connection_details.get('host', ''),
                port=int(connection_details.get('port', 1521)),
                database=connection_details.get('sid') or connection_details.get('service_name') or '',
                username=connection_details.get('username', ''),
                password=connection_details.get('password', ''),
                service_name=connection_details.get('service_name'),
                is_active=True,
            )

            if repo.save_connection(connection):
                logger.info(f"Saved Oracle connection '{connection.name}'")
            else:
                logger.error("Failed to save Oracle connection")
            
        except Exception as e:
            logger.error(f"Error saving Oracle connection: {e}")

    def _apply_thresholds(self, high, medium):
        """Apply threshold settings to the application"""
        try:
            logger.info(f"Applying thresholds - High: {high}, Medium: {medium}")
            
            # Apply to parent application if it has threshold update method
            if hasattr(self.parent, 'update_thresholds'):
                self.parent.update_thresholds(high, medium)
            
            elif hasattr(self.parent, 'settings'):
                self.parent.settings.high_confidence_threshold = high
                self.parent.settings.medium_confidence_threshold = medium
                self.parent.settings.confidence_threshold = high
                self.parent.settings.save()
            
        except Exception as e:
            logger.error(f"Error applying thresholds: {e}")

    def show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(
            self.parent,
            "About Bank Reconciliation AI",
            "Bank Reconciliation AI v1.0\n\n"
            "An intelligent bank reconciliation system using machine learning\n"
            "to automate transaction matching and anomaly detection.\n\n"
            "© 2025 Sumo AI Labs Limited"
        )

    def show_user_manual(self):
        """Open the user manual in the default system viewer."""
        manual_path = Path(__file__).resolve().parents[2] / 'USER_GUIDE.md'
        
        if manual_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(manual_path)))
        else:
            QMessageBox.information(
                self.parent,
                'User Manual',
                'User guide is unavailable.',
            )
