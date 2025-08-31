# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# training/__init__.py
# ================================

"""
Training package for the Bank Reconciliation AI.

This package provides a modular approach to machine learning model training
with support for multiple data sources, hyperparameter tuning, cross-validation,
and self-learning capabilities.
"""

from .data_models import (
    TrainingDataSource, 
    TrainingDataset, 
    ModelTrainingConfig, 
    TrainingResult
)
from .data_processor import (
    FeatureExtractor, 
    DataQualityAnalyzer, 
    DatasetBuilder
)
from .model_factory import ModelFactory
from .cross_validator import CrossValidator
from .hyperparameter_tuner import HyperparameterTuner
from .self_learning import SelfLearningManager
from .training_orchestrator import TrainingOrchestrator

__all__ = [
    'TrainingDataSource',
    'TrainingDataset', 
    'ModelTrainingConfig',
    'TrainingResult',
    'FeatureExtractor',
    'DataQualityAnalyzer',
    'DatasetBuilder',
    'ModelFactory',
    'CrossValidator',
    'HyperparameterTuner', 
    'SelfLearningManager',
    'TrainingOrchestrator'
]