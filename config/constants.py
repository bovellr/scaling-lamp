# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
"""Application constants and enums"""

from enum import Enum
from pathlib import Path

# Application info
APP_NAME = "Bank Reconciliation AI"
APP_VERSION = "1.0.0"
ORGANIZATION_NAME = "Arvida Software UK"

# File constraints
MAX_FILE_SIZE_MB = 100
SUPPORTED_EXTENSIONS = ['.csv', '.xlsx', '.xls']

# ML constants
DEFAULT_CONFIDENCE_THRESHOLD = 0.7
MIN_TRAINING_SAMPLES = 5
AUTO_RETRAIN_THRESHOLD = 10

# UI constants
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
TABLE_ROW_HEIGHT = 25

# File paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
MODEL_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
RESOURCES_DIR = PROJECT_ROOT / "resources"

def ensure_directories() -> None:
    """Create required application directories if they do not exist."""
    for path in (DATA_DIR, OUTPUT_DIR, MODEL_DIR, LOGS_DIR, RESOURCES_DIR):
        path.mkdir(parents=True, exist_ok=True)

# Legacy config compatibility
BANK_FILE = str(DATA_DIR / "bank_statement.csv")
ERP_FILE = str(DATA_DIR / "erp_transactions.csv")
TRAINING_FILE = str(DATA_DIR / "training_labels.csv")
MODEL_PATH = str(MODEL_DIR / "model.pkl")
REPORT_FILE = str(OUTPUT_DIR / "reconciliation_report.xlsx")
MATCHED_REPORT_PATH = str(OUTPUT_DIR / "matched_transactions.csv")
UNMATCHED_REPORT_PATH = str(OUTPUT_DIR / "unmatched_transactions.csv")


# Additional configuration constants
MODEL_VERSION = "v1.0.0"
MATCH_CONFIDENCE_THRESHOLD = DEFAULT_CONFIDENCE_THRESHOLD


class FileType(Enum):
    """Supported file types"""
    CSV = "csv"
    EXCEL = "excel"

class Theme(Enum):
    """UI theme options"""
    LIGHT = "light"
    DARK = "dark"

class MatchStatus(Enum):
    """Transaction match status"""
    MATCHED = "matched"
    UNMATCHED = "unmatched"
    PENDING = "pending"
    REVIEWED = "reviewed"

class BankType(Enum):
    LLOYDS = "lloyds"
    RBS_NATWEST = "natwest"
    BARCLAYS = "barclays"
    HSBC = "hsbc"

