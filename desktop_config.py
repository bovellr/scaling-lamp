# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
# desktop_config.py - PySide6 Specific Configuration
from config import load_config

CONFIG = load_config()

# Desktop UI Settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
MIN_WINDOW_WIDTH = 1200
MIN_WINDOW_HEIGHT = 800

# Theme
USE_DARK_THEME = False
ACCENT_COLOR = "#4CAF50"

# Performance
MAX_COMBINATIONS = 50000
CHUNK_SIZE = 1000