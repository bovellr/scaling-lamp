# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# training/training_orchestrator.py
# ================================

from typing import Optional, Dict, Any, List, Tuple
import logging
from pathlib import Path
import joblib
import json
import numpy as np
from datetime import datetime

# Import from the training package __init__.py
from . import (
    TrainingDataset, 
    ModelTrainingConfig, 
    DatasetBuilder,
    ModelFactory,
    CrossValidator,
    HyperparameterTuner,
    SelfLearningManager,
    TrainingResult
)
logger = logging.getLogger(__name__)

class TrainingOrchestrator:
    """Main orchestrator that coordinates all training components."""
    
    def __init__(self, model_dir: str = "models/ml/training"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.dataset_builder = DatasetBuilder()
        self.model_factory = ModelFactory()
        self.cross_validator = CrossValidator()
        self.hyperparameter_tuner = HyperparameterTuner()
        self.self_learning_manager = SelfLearningManager()
        
        self.model_versions: List[Dict[str, Any]] = []
        self._load_model_versions()
    
    def _load_model_versions(self):
        """Load existing model versions."""
        versions_file = self.model_dir / "model_versions.json"
        if versions_file.exists():
            try:
                import json
                with open(versions_file, 'r') as f:
                    self.model_versions = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load model versions: {e}")
    
    def train_model_from_feedback(self, dataset_name: str, 
                                 config: ModelTrainingConfig,
                                 tune_hyperparameters: bool = False) -> TrainingResult:
        """Complete training pipeline from feedback data."""
        try:
            # 1. Get feedback data
            feedback_data = self.self_learning_manager.get_training_data_from_feedback()
            if not feedback_data:
                raise ValueError("No feedback data available for training")
            
            # 2. Build dataset
            dataset, features, labels = self.dataset_builder.build_from_feedback(
                feedback_data, dataset_name
            )
            
            # 3. Prepare data
            X = np.array(features, dtype=np.float64)
            y = np.array(labels, dtype=np.int32)
            
            # 4. Create model and scaler
            model = self.model_factory.create_model(config)
            scaler = self.model_factory.create_scaler(config)
            
            # 5. Scale features if needed
            if scaler:
                X = scaler.fit_transform(X)
            
            # 6. Split data
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=config.test_size, random_state=42, stratify=y
            )
            
            # 7. Hyperparameter tuning (optional)
            if tune_hyperparameters:
                model, tuning_results = self.hyperparameter_tuner.tune_hyperparameters(
                    model, X_train, y_train
                )
            
            # 8. Train model
            model.fit(X_train, y_train)
            
            # 9. Cross-validation
            cv_results = self.cross_validator.perform_cross_validation(
                model, X, y, config.cross_validation_folds
            )
            
            # 10. Evaluate on test set
            eval_results = self.cross_validator.evaluate_model(model, X_test, y_test)
            
            # 11. Create training result
            result = TrainingResult(
                version_id=f"v{len(self.model_versions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                dataset_id=dataset.dataset_id,
                model_type=config.model_type,
                train_accuracy=float(model.score(X_train, y_train)),
                test_accuracy=eval_results['accuracy'],
                cv_mean_accuracy=cv_results['mean_accuracy'],
                cv_std_accuracy=cv_results['std_accuracy'],
                feature_importance=dict(zip(dataset.feature_columns, eval_results['feature_importance'])) if eval_results['feature_importance'] else None,
                classification_report=eval_results['classification_report'],
                confusion_matrix=eval_results['confusion_matrix'],
                created_date=datetime.now().isoformat()
            )
            
            # 12. Save model
            self._save_trained_model(result, model, scaler, dataset, config)
            
            # 13. Record improvement
            if self.model_versions:
                last_accuracy = self.model_versions[-1].get('test_accuracy', 0)
                self.self_learning_manager.calculate_model_improvement(
                    last_accuracy, result.test_accuracy
                )
            
            # 14. Update version history
            self.model_versions.append(result.__dict__)
            self._save_model_versions()
            
            logger.info(f"Training completed: {result.test_accuracy:.3f} accuracy")
            return result
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise
    
    def _save_trained_model(self, result: TrainingResult, model: Any, 
                           scaler: Optional[Any], dataset: TrainingDataset,
                           config: ModelTrainingConfig):
        """Save trained model and metadata."""
        model_path = self.model_dir / f"{result.version_id}.pkl"
        
        model_data = {
            'model': model,
            'scaler': scaler,
            'config': config,
            'dataset_info': dataset,
            'training_result': result,
            'feature_columns': dataset.feature_columns
        }
        
        joblib.dump(model_data, model_path)
        logger.info(f"Model saved to {model_path}")
    
    def _save_model_versions(self):
        """Save model version history."""
        versions_file = self.model_dir / "model_versions.json"
        
        try:
            with open(versions_file, 'w') as f:
                json.dump(self.model_versions, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save model versions: {e}")
    
    def get_best_model(self) -> Optional[Dict[str, Any]]:
        """Get the best performing model."""
        if not self.model_versions:
            return None
        
        return max(self.model_versions, key=lambda v: v['test_accuracy'])
    
    def load_production_model(self, version_id: Optional[str] = None):
        """Load model for production use."""
        if version_id:
            model_path = self.model_dir / f"{version_id}.pkl"
        else:
            best_model = self.get_best_model()
            if not best_model:
                raise ValueError("No trained models available")
            model_path = self.model_dir / f"{best_model['version_id']}.pkl"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        return joblib.load(model_path)