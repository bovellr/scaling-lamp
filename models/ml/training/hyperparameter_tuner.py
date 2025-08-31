# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from typing import Dict, Any, Optional
import logging
import numpy as np
from typing import Tuple

# Try to import LightGBM, but don't fail if not available
try:
    import lightgbm as lgb
except ImportError:
    lgb = None

logger = logging.getLogger(__name__)

class HyperparameterTuner:
    """Handles hyperparameter optimization."""
    
    @staticmethod
    def get_default_param_grids() -> Dict[str, Dict[str, list]]:
        """Get default parameter grids for different models."""
        return {
            'random_forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'class_weight': ['balanced', None]
            },
            'xgboost': {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 6, 9],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0]
            },
            'lightgbm': {
                'n_estimators': [100, 200, 300],
                'num_leaves': [31, 50, 100],
                'learning_rate': [0.01, 0.05, 0.1],
                'feature_fraction': [0.8, 0.9, 1.0],
                'bagging_fraction': [0.8, 0.9, 1.0]
            }
        }
    
    @staticmethod
    def tune_hyperparameters(model, X: np.ndarray, y: np.ndarray,
                           param_grid: Optional[Dict[str, list]] = None,
                           search_type: str = 'grid',
                           use_lightgbm_cv: bool = False,
                           cv_folds: int = 5,
                           n_iter: int = 20) -> Tuple[Any, Dict[str, Any]]:
        """Perform hyperparameter tuning."""
        try:
            model_name = model.__class__.__name__.lower()
            
            # Use default param grid if none provided
            if param_grid is None:
                default_grids = HyperparameterTuner.get_default_param_grids()
                for key, grid in default_grids.items():
                    if key in model_name:
                        param_grid = grid
                        break
                
                if param_grid is None:
                    logger.warning(f"No default param grid for {model_name}")
                    return model, {}
            
            # Choose search strategy
            if search_type == 'random':
                search = RandomizedSearchCV(
                    model, param_grid, 
                    n_iter=n_iter,
                    cv=cv_folds,
                    scoring='accuracy',
                    n_jobs=-1,
                    random_state=42
                )
            elif search_type == 'lightgbm' and use_lightgbm_cv:
                search = lgb.LGBMClassifier(
                    model, param_grid,
                    cv=cv_folds,
                    scoring='binary_logloss',
                    n_jobs=-1,
                    random_state=42
                )
            else:  # grid search
                search = GridSearchCV(
                    model, param_grid,
                    cv=cv_folds,
                    scoring='accuracy',
                    n_jobs=-1
                )
            
            # Perform search
            logger.info(f"Starting {search_type} search with {len(param_grid)} parameters")
            search.fit(X, y)
            
            # Return best model and results
            tuning_results = {
                'best_params': search.best_params_,
                'best_score': search.best_score_,
                'cv_results': search.cv_results_
            }
            
            logger.info(f"Best parameters: {search.best_params_}")
            logger.info(f"Best cross-validation score: {search.best_score_:.4f}")
            
            return search.best_estimator_, tuning_results
            
        except Exception as e:
            logger.error(f"Hyperparameter tuning failed: {e}")
            raise