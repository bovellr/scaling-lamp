# Commercial License
# Copyright (c) 2024 Arvida Software UK
# All rights reserved.
# This software is the confidential and proprietary information of Arvida Software UK.
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.

# config.py - Shared Configuration
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"
OUTPUT_DIR = BASE_DIR / "output"
TEST_DATA_DIR = BASE_DIR / "test_data"
DATABASE_DIR = BASE_DIR / "database"  # 🆕 Database directory

# Ensure directories exist
for directory in [DATA_DIR, MODEL_DIR, OUTPUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database configuration 🆕
DATABASE_PATH = DATABASE_DIR / "reconciliation.db"
BACKUP_RETENTION_DAYS = 30
AUTO_BACKUP_ENABLED = True

# File paths
BANK_FILE = TEST_DATA_DIR / "sample_bank.csv"
ERP_FILE = TEST_DATA_DIR / "sample_erp.csv"
TRAINING_FILE = TEST_DATA_DIR / "sample_training.csv"
MODEL_PATH = MODEL_DIR / "reconciliation_model.pkl"
MATCHED_REPORT_PATH = OUTPUT_DIR / "matched_transactions.csv"
UNMATCHED_REPORT_PATH = OUTPUT_DIR / "unmatched_transactions.csv"
REPORT_FILE = OUTPUT_DIR / "reconciliation_report.xlsx"

# Model settings
MATCH_CONFIDENCE_THRESHOLD = 0.7
MODEL_VERSION = "v1.0.0"