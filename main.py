# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
# !/usr/bin/env python3

# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================
"""
Bank Reconciliation AI - Main Application Entry Point
"""

import logging
from pathlib import Path
import sys

from PySide6.QtWidgets import QApplication, QMessageBox
from services.app_container import setup_application_container

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.constants import ensure_directories
from config.settings import AppSettings
from services.event_bus import EventBus
from services.logging_service import setup_logging
from views.main_window import MainWindow

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""

    try:

        # Ensure required directories exist
        ensure_directories()

        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)

        # Create QApplication
        app = QApplication(sys.argv)

        # Setup dependency injection container FIRST
        setup_application_container()

        app.setApplicationName("Bank Reconciliation AI")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Arvida Software UK")

        # Load settings
        settings = AppSettings()
        
        # Initialize event bus
        event_bus = EventBus()

        # Load application stylesheet
        load_application_stylesheet(app)

        # Create and show main window
        main_window = MainWindow(settings, event_bus)
        main_window.show()
    
        logger.info("Application started successfully")
    
        # Run application
        return app.exec()

    except Exception as e:
        # Show error dialog if GUI initialization fails
        if 'app' in locals():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Application Error")
            msg.setText(f"Failed to start application: {str(e)}")
            msg.exec()
        else:
            print(f"Critical error: {e}")
        return 1


def load_application_stylesheet(app):
    """Load stylesheet once for entire application"""
    try:
        stylesheet_path = Path("resources/styles/main.qss")
        if stylesheet_path.exists():
            with open(stylesheet_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
            logger.info("Application stylesheet loaded successfully")
        else:
            logger.warning(f"Stylesheet not found: {stylesheet_path}")
    except Exception as e:
        logger.error(f"Failed to load stylesheet: {e}")



if __name__ == "__main__":
    sys.exit(main())
