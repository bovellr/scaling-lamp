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
import re
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
    """Load stylesheet once for entire application.

    Supports basic ``@import`` statements within the QSS file by inlining
    the referenced component stylesheets. In addition to processing any
    imports found in ``main.qss``, the button, combobox and table component
    styles are always concatenated with the base stylesheet.
    """
    try:
        stylesheet_path = Path(__file__).parent / "resources" / "styles" / "main.qss"
        if not stylesheet_path.exists():
            logger.warning(f"Stylesheet not found: {stylesheet_path}")
            return

        # Read base stylesheet and replace any @import directives with the
        # contents of the referenced file.
        base_content = stylesheet_path.read_text(encoding="utf-8").splitlines()
        import_pattern = re.compile(
            r"@import\s+url\([\"']?([^\"')]+)[\"']?\);?"
        )
        final_styles = []
        imported_files = set()

        for line in base_content:
            match = import_pattern.search(line.strip())
            if match:
                import_file = stylesheet_path.parent / match.group(1)
                if import_file.exists():
                    final_styles.append(import_file.read_text(encoding="utf-8"))
                    imported_files.add(import_file.resolve())
                else:
                    logger.warning(f"Imported stylesheet not found: {import_file}")
            else:
                final_styles.append(line)

        # Ensure specific component styles are included even if they were not
        # explicitly imported.
        components = [
            "components/buttons.qss",
            "components/comboboxes.qss",
            "components/tables.qss",
        ]
        for component in components:
            comp_path = stylesheet_path.parent / component
            resolved = comp_path.resolve()
            if comp_path.exists() and resolved not in imported_files:
                final_styles.append(comp_path.read_text(encoding="utf-8"))
                imported_files.add(resolved)
            elif not comp_path.exists():
                logger.warning(f"Stylesheet not found: {comp_path}")

        app.setStyleSheet("\n".join(final_styles))
        logger.info("Application stylesheet loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load stylesheet: {e}")



if __name__ == "__main__":
    sys.exit(main())
