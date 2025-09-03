# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# MODULAR TRAINING ARCHITECTURE
# ================================

# models/training/data_models.py
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class TrainingDataSource:
    """Represents a source of training data."""
    source_id: str
    source_type: str  # 'file_upload', 'bank_api', 'erp_database', 'manual_feedback'
    bank_type: str    # 'lloyds', 'natwest', 'generic', etc.
    data_format: str  # 'csv', 'api_json', 'database_query'
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    sample_count: int = 0
    quality_score: float = 0.0
    is_validated: bool = False

@dataclass 
class TrainingDataset:
    """Enhanced training dataset with metadata."""
    dataset_id: str
    name: str
    description: str
    sources: List[TrainingDataSource] = field(default_factory=list)
    total_samples: int = 0
    positive_samples: int = 0
    negative_samples: int = 0
    feature_columns: List[str] = field(default_factory=list)
    data_quality_metrics: Dict[str, float] = field(default_factory=dict)
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1

@dataclass
class ModelTrainingConfig:
    """Configuration for model training."""
    model_type: str = "random_forest"
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    cross_validation_folds: int = 5
    test_size: float = 0.2
    use_feature_scaling: bool = True
    feature_selection: bool = True
    class_balancing: str = "auto"
    # Hyperparameter tuning options
    use_random_search: bool = False
    random_search_iters: int = 20
    search_hyperparameters: Optional[Dict[str, Any]] = None
    scoring_metric: str = "f1"

@dataclass
class TrainingResult:
    """Results from model training."""
    version_id: str
    dataset_id: str
    model_type: str
    train_accuracy: float
    test_accuracy: float
    cv_mean_accuracy: float
    cv_std_accuracy: float
    feature_importance: Optional[Dict[str, float]]
    classification_report: Dict[str, Any]
    confusion_matrix: List[List[int]]
    created_date: str
