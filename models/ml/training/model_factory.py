# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# training/model_factory.py
# ================================

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from typing import Optional
from models.ml.training.data_models import ModelTrainingConfig


logger = logging.getLogger(__name__)

class ModelFactory:
    """Factory for creating different ML models."""
    
    @staticmethod
    def create_model(config: ModelTrainingConfig):
        """Create model instance based on configuration."""
        model_type = config.model_type.lower()
        params = config.hyperparameters
        
        if model_type == "random_forest":
            default_params = {
                'n_estimators': 100,
                'max_depth': 10,
                'class_weight': 'balanced',
                'min_samples_split': 5,
                'random_state': 42
            }
            default_params.update(params)
            return RandomForestClassifier(**default_params)
        
        elif model_type == "xgboost":
            try:
                import xgboost as xgb
                default_params = {
                    'n_estimators': 200,
                    'max_depth': 6,
                    'learning_rate': 0.1,
                    'subsample': 0.8,
                    'random_state': 42
                }
                default_params.update(params)
                return xgb.XGBClassifier(**default_params)
            except ImportError:
                logger.warning("XGBoost not available, falling back to RandomForest")
                return ModelFactory.create_model(
                    ModelTrainingConfig(model_type="random_forest", hyperparameters=params)
                )
        
        elif model_type == "lightgbm":
            try:
                import lightgbm as lgb
                default_params = {
                    'objective': 'binary',
                    'metric': 'binary_logloss',
                    'boosting_type': 'gbdt',
                    'learning_rate': 0.05,
                    'num_leaves': 31,
                    'class_weight': 'balanced',
                    'verbosity': -1,
                    'random_state': 42
                }
                default_params.update(params)
                return lgb.LGBMClassifier(**default_params)
            except ImportError:
                logger.warning("LightGBM not available, falling back to RandomForest")
                return ModelFactory.create_model(
                    ModelTrainingConfig(model_type="random_forest", hyperparameters=params)
                )
        
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    @staticmethod
    def create_scaler(config: ModelTrainingConfig) -> Optional[StandardScaler]:
        """Create feature scaler if needed."""
        if config.use_feature_scaling:
            return StandardScaler()
        return None