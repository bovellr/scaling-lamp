# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""
Legacy configuration module for backward compatibility.
This module provides the old config.py functionality within the config package.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class AppConfig:
    """Application configuration values."""
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODEL_DIR: Path = BASE_DIR / "models"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    TEST_DATA_DIR: Path = BASE_DIR / "test_data"
    DATABASE_DIR: Path = BASE_DIR / "database"

    DATABASE_PATH: Path = DATABASE_DIR / "reconciliation.db"
    BACKUP_RETENTION_DAYS: int = 30
    AUTO_BACKUP_ENABLED: bool = True

    BANK_FILE: Path = TEST_DATA_DIR / "sample_bank.csv"
    ERP_FILE: Path = TEST_DATA_DIR / "sample_erp.csv"
    TRAINING_FILE: Path = TEST_DATA_DIR / "sample_training.csv"
    MODEL_PATH: Path = MODEL_DIR / "reconciliation_model.pkl"
    MATCHED_REPORT_PATH: Path = OUTPUT_DIR / "matched_transactions.csv"
    UNMATCHED_REPORT_PATH: Path = OUTPUT_DIR / "unmatched_transactions.csv"
    REPORT_FILE: Path = OUTPUT_DIR / "reconciliation_report.xlsx"

    MATCH_CONFIDENCE_THRESHOLD: float = 0.7
    MODEL_VERSION: str = "v1.0.0"

    # Set to True for datasets where credits are positive and debits are negative
    ERP_POSITIVE_CREDITS: bool = False


_config: Optional[AppConfig] = None


def load_config() -> AppConfig:
    """Return a singleton application configuration."""
    global _config
    if _config is None:
        cfg = AppConfig()
        for directory in [cfg.DATA_DIR, cfg.MODEL_DIR, cfg.OUTPUT_DIR, cfg.DATABASE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
        _config = cfg
    return _config
