# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# training/cross_validator.py
# ================================

from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class CrossValidator:
    """Handles cross-validation and model evaluation."""
    
    @staticmethod
    def perform_cross_validation(model, X: np.ndarray, y: np.ndarray, 
                                cv_folds: int = 5) -> Dict[str, float]:
        """Perform stratified k-fold cross-validation."""
        try:
            cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
            cv_scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy')
            
            return {
                'mean_accuracy': float(cv_scores.mean()),
                'std_accuracy': float(cv_scores.std()),
                'min_accuracy': float(cv_scores.min()),
                'max_accuracy': float(cv_scores.max()),
                'scores': cv_scores.tolist()
            }
        except Exception as e:
            logger.error(f"Cross-validation failed: {e}")
            raise
    
    @staticmethod
    def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Evaluate model on test set."""
        try:
            # Predictions
            y_pred = model.predict(X_test)
            y_pred_proba = None
            
            if hasattr(model, 'predict_proba'):
                y_pred_proba = model.predict_proba(X_test)
            
            # Classification report
            class_report = classification_report(y_test, y_pred, output_dict=True)
            
            # Confusion matrix
            conf_matrix = confusion_matrix(y_test, y_pred)
            
            # Feature importance (if available)
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_importance = model.feature_importances_.tolist()
            
            return {
                'accuracy': float(class_report['accuracy']),
                'precision': float(class_report['1']['precision']),
                'recall': float(class_report['1']['recall']),
                'f1_score': float(class_report['1']['f1-score']),
                'classification_report': class_report,
                'confusion_matrix': conf_matrix.tolist(),
                'feature_importance': feature_importance,
                'predictions': y_pred.tolist(),
                'prediction_probabilities': y_pred_proba.tolist() if y_pred_proba is not None else None
            }
        except Exception as e:
            logger.error(f"Model evaluation failed: {e}")
            raise