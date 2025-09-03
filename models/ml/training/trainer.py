# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# ENHANCED TRAINING MODEL INTEGRATION
# ================================

"""
The training model becomes MORE important in the enhanced version because:

1. DIVERSE DATA SOURCES: Bank files, ERP databases, API feeds need unified training
2. TEMPLATE VARIATIONS: Different bank formats require adaptive models
3. SELF-LEARNING SCALE: More data sources = more learning opportunities
4. ENTERPRISE DEPLOYMENT: Production systems need robust, retrained models
5. MULTI-TENANT SUPPORT: Different organizations need custom-trained models
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

import numpy as np
import logging
import joblib
import json
from pathlib import Path
from models.ml.feature_utils import compute_transaction_features

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.preprocessing import StandardScaler

from models.data_models import BankStatement, TransactionData, MatchResult
from models.database import AuditRepository
from viewmodels.base_viewmodel import BaseViewModel
from .data_models import (
    TrainingDataSource,
    TrainingDataset,
    ModelTrainingConfig,
)

logger = logging.getLogger(__name__)


# ================================
# ENHANCED TRAINING SERVICE
# ================================

class TrainingService:
    """Enhanced training service supporting multiple data sources and advanced ML."""
    
    def __init__(self, model_dir: str = "models/ml/training", data_dir: str = "data/training/labeled"):
        self.model_dir = Path(model_dir)
        self.data_dir = Path(data_dir)
        self.audit_repository = AuditRepository()
        
        # Create directories
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Training history
        self.training_datasets: Dict[str, TrainingDataset] = {}
        self.model_versions: List[Dict[str, Any]] = []
        
        # Load existing datasets
        self._load_training_datasets()
    
    def _load_training_datasets(self):
        """Load existing training datasets."""
        datasets_file = self.data_dir / "training_datasets.json"
        if datasets_file.exists():
            try:
                import json
                with open(datasets_file, 'r') as f:
                    data = json.load(f)
                
                for dataset_dict in data.get('datasets', []):
                    # Convert sources back to TrainingDataSource objects
                    sources = [TrainingDataSource(**src) for src in dataset_dict.get('sources', [])]
                    dataset_dict['sources'] = sources
                    
                    dataset = TrainingDataset(**dataset_dict)
                    self.training_datasets[dataset.dataset_id] = dataset
                    
                logger.info(f"Loaded {len(self.training_datasets)} training datasets")
            except Exception as e:
                logger.error(f"Failed to load training datasets: {e}")
    
    def create_dataset_from_feedback(self, feedback_data: List[Dict[str, Any]], 
                                   dataset_name: str) -> TrainingDataset:
        """Create training dataset from self-learning feedback."""
        logger.info(f"Creating dataset from {len(feedback_data)} feedback entries")
        
        # Convert feedback to training features
        features_list = []
        labels_list = []
        
        for feedback in feedback_data:
            try:
                # Extract transaction data
                bank_data = feedback['bank_data']
                erp_data = feedback['erp_data']
                
                # Generate features (same as your existing logic)
                features = self._extract_features_from_feedback(bank_data, erp_data)
                label = feedback['user_decision']  # 1 for match, 0 for no match
                
                features_list.append(features)
                labels_list.append(label)
                
            except Exception as e:
                logger.warning(f"Error processing feedback entry: {e}")
                continue
        
        if not features_list:
            raise ValueError("No valid features extracted from feedback data")
        
        # Create dataset
        dataset = TrainingDataset(
            dataset_id=f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=dataset_name,
            description=f"Dataset created from {len(features_list)} feedback entries",
            total_samples=len(features_list),
            positive_samples=sum(labels_list),
            negative_samples=len(labels_list) - sum(labels_list),
            feature_columns=['amount_difference', 'date_difference', 'description_similarity', 
                           'signed_amount_match', 'same_day']
        )
        
        # Add source information
        source = TrainingDataSource(
            source_id=f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            source_type='manual_feedback',
            bank_type='mixed',
            data_format='feedback_json',
            sample_count=len(features_list),
            quality_score=self._calculate_data_quality(features_list, labels_list),
            is_validated=True  # Feedback is pre-validated by users
        )
        dataset.sources.append(source)
        
        # Save dataset
        self._save_dataset(dataset, features_list, labels_list)
        self.training_datasets[dataset.dataset_id] = dataset
        
        return dataset
    
    def create_dataset_from_bank_api(self, bank_transactions: List[TransactionData],
                                   erp_transactions: List[TransactionData],
                                   manual_matches: List[Tuple[int, int, bool]],
                                   dataset_name: str,
                                   bank_type: str) -> TrainingDataset:
        """Create training dataset from bank API and ERP data with manual matches."""
        logger.info(f"Creating dataset from {len(manual_matches)} manual matches")
        
        features_list = []
        labels_list = []
        
        for bank_idx, erp_idx, is_match in manual_matches:
            try:
                bank_txn = bank_transactions[bank_idx]
                erp_txn = erp_transactions[erp_idx]
                
                # Generate features
                features = self._generate_transaction_features(bank_txn, erp_txn)
                
                features_list.append(features)
                labels_list.append(1 if is_match else 0)
                
            except Exception as e:
                logger.warning(f"Error processing manual match: {e}")
                continue
        
        # Create dataset
        dataset = TrainingDataset(
            dataset_id=f"api_{bank_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=dataset_name,
            description=f"Dataset from {bank_type} API with {len(features_list)} manual matches",
            total_samples=len(features_list),
            positive_samples=sum(labels_list),
            negative_samples=len(labels_list) - sum(labels_list),
            feature_columns=['amount_difference', 'date_difference', 'description_similarity', 
                           'signed_amount_match', 'same_day']
        )
        
        # Add source
        source = TrainingDataSource(
            source_id=f"api_{bank_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            source_type='bank_api',
            bank_type=bank_type,
            data_format='api_json',
            sample_count=len(features_list),
            quality_score=self._calculate_data_quality(features_list, labels_list),
            is_validated=True
        )
        dataset.sources.append(source)
        
        # Save dataset
        self._save_dataset(dataset, features_list, labels_list)
        self.training_datasets[dataset.dataset_id] = dataset
        
        return dataset
    
    def merge_datasets(self, dataset_ids: List[str], merged_name: str) -> TrainingDataset:
        """Merge multiple training datasets into one."""
        if not dataset_ids:
            raise ValueError("No datasets provided for merging")
        
        all_features = []
        all_labels = []
        all_sources = []
        total_samples = 0
        
        for dataset_id in dataset_ids:
            if dataset_id not in self.training_datasets:
                logger.warning(f"Dataset {dataset_id} not found, skipping")
                continue
            
            dataset = self.training_datasets[dataset_id]
            
            # Load dataset features and labels
            features, labels = self._load_dataset_data(dataset_id)
            
            all_features.extend(features)
            all_labels.extend(labels)
            all_sources.extend(dataset.sources)
            total_samples += dataset.total_samples
        
        if not all_features:
            raise ValueError("No valid datasets found for merging")
        
        # Create merged dataset
        merged_dataset = TrainingDataset(
            dataset_id=f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=merged_name,
            description=f"Merged dataset from {len(dataset_ids)} sources",
            sources=all_sources,
            total_samples=len(all_features),
            positive_samples=sum(all_labels),
            negative_samples=len(all_labels) - sum(all_labels),
            feature_columns=['amount_difference', 'date_difference', 'description_similarity', 
                           'signed_amount_match', 'same_day']
        )
        
        # Calculate quality metrics
        merged_dataset.data_quality_metrics = {
            'balance_ratio': min(sum(all_labels), len(all_labels) - sum(all_labels)) / len(all_labels),
            'feature_completeness': self._calculate_feature_completeness(all_features),
            'source_diversity': len(set(src.source_type for src in all_sources))
        }
        
        # Save merged dataset
        self._save_dataset(merged_dataset, all_features, all_labels)
        self.training_datasets[merged_dataset.dataset_id] = merged_dataset
        
        return merged_dataset
    
    def train_enhanced_model(self, dataset_id: str, config: ModelTrainingConfig) -> Dict[str, Any]:
        """Train enhanced model with advanced ML techniques."""
        logger.info(f"Training enhanced model with dataset {dataset_id}")
        
        if dataset_id not in self.training_datasets:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        dataset = self.training_datasets[dataset_id]
        
        # Load training data
        X, y = self._load_dataset_data(dataset_id)
        X = np.array(X, dtype=np.float64)
        y = np.array(y, dtype=np.int32)
        
        logger.info(f"Training with {len(X)} samples, {sum(y)} positive matches")
        
        # Feature preprocessing
        if config.use_feature_scaling:
            scaler = StandardScaler()
            X = scaler.fit_transform(X)
        else:
            scaler = None
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=config.test_size, 
            random_state=42, 
            stratify=y
        )
        
        # Create model based on config
        model = self._create_model(config)
        
        from sklearn.model_selection import RandomizedSearchCV
        
        # Optional hyperparameter search
        if config.use_random_search and config.search_hyperparameters:
            logger.info("Running RandomizedSearchCV for hyperparameter tuning...")

            search = RandomizedSearchCV(
                estimator=model,
                param_distributions=config.search_hyperparameters,
                n_iter=config.random_search_iters,
                cv=config.cross_validation_folds,
                scoring=config.scoring_metric,
                verbose=1,
                n_jobs=-1,
                random_state=42
            )

            # Train model
            search.fit(X_train, y_train)
            model = search.best_estimator_
            
            # Update config with best params for logging and saving
            config.hyperparameters = search.best_params_
            logger.info(f"Best hyperparameters found: {search.best_params_}")

        else:
            model.fit(X_train, y_train)

        # Evaluate model
        train_accuracy = model.score(X_train, y_train)
        test_accuracy = model.score(X_test, y_test)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X, y, cv=config.cross_validation_folds)
        
        # Detailed predictions for analysis
        y_pred = model.predict(X_test)
        classification_rep = classification_report(y_test, y_pred, output_dict=True)
        confusion_mat = confusion_matrix(y_test, y_pred)
        
        # Feature importance (if available)
        feature_importance = None
        if hasattr(model, 'feature_importances_'):
            feature_importance = {
                feature: importance 
                for feature, importance in zip(dataset.feature_columns, model.feature_importances_)
            }
        
        # Create model version record
        model_version = {
            'version_id': f"v{len(self.model_versions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'dataset_id': dataset_id,
            'model_type': config.model_type,
            'hyperparameters': config.hyperparameters,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'cv_mean_accuracy': cv_scores.mean(),
            'cv_std_accuracy': cv_scores.std(),
            'classification_report': classification_rep,
            'confusion_matrix': confusion_mat.tolist(),
            'feature_importance': feature_importance,
            'created_date': datetime.now().isoformat(),
            'is_production': False
        }
        
        # Save model
        model_path = self.model_dir / f"{model_version['version_id']}.pkl"
        model_data = {
            'model': model,
            'scaler': scaler,
            'config': config,
            'dataset_info': dataset,
            'version_info': model_version,
            'feature_columns': dataset.feature_columns
        }
        
        joblib.dump(model_data, model_path)
        
        # Record version
        self.model_versions.append(model_version)
        self._save_model_versions()
        
        # Log to audit
        self.audit_repository.log_user_action(
            'model_training_completed',
            f"Model {model_version['version_id']} trained with {test_accuracy:.3f} accuracy"
        )
        
        logger.info(f"Model training complete: {test_accuracy:.3f} test accuracy")
        return model_version
    
    def _create_model(self, config: ModelTrainingConfig):
        """Create ML model based on configuration."""
        if config.model_type == "random_forest":
            return RandomForestClassifier(**config.hyperparameters)
        elif config.model_type == "xgboost":
            try:
                import xgboost as xgb
                return xgb.XGBClassifier(**config.hyperparameters)
            except ImportError:
                logger.warning("XGBoost not available, falling back to RandomForest")
                return RandomForestClassifier(**config.hyperparameters)
        else:
            raise ValueError(f"Unsupported model type: {config.model_type}")
    
    def _extract_features_from_feedback(self, bank_data: Dict, erp_data: Dict) -> List[float]:
        """Extract features from feedback data."""
        features = compute_transaction_features(
            bank_data['Amount'],
            bank_data['Date'],
            bank_data['Description'],
            erp_data['Amount'],
            erp_data['Date'],
            erp_data['Description'],
        )
        return [
            features['amount_diff'],
            features['date_diff'],
            features['description_similarity'],
            features['signed_amount_match'],
            features['same_day'],
        ]
    
    def _generate_transaction_features(self, bank_txn: TransactionData, 
                                     erp_txn: TransactionData) -> List[float]:
        """Generate features from transaction objects."""
        features = compute_transaction_features(
            bank_txn.amount,
            bank_txn.date,
            bank_txn.description,
            erp_txn.amount,
            erp_txn.date,
            erp_txn.description,
        )
        return [
            features['amount_diff'],
            features['date_diff'],
            features['description_similarity'],
            features['signed_amount_match'],
            features['same_day'],
        ]
    
    def _calculate_data_quality(self, features_list: List[List[float]], 
                               labels_list: List[int]) -> float:
        """Calculate data quality score."""
        if not features_list:
            return 0.0
        
        # Balance score (closer to 50/50 is better)
        positive_ratio = sum(labels_list) / len(labels_list)
        balance_score = 1 - abs(0.5 - positive_ratio) * 2
        
        # Feature completeness (no NaN/infinite values)
        features_array = np.array(features_list)
        completeness_score = 1 - (np.isnan(features_array).sum() + np.isinf(features_array).sum()) / features_array.size
        
        # Diversity score (feature variance)
        diversity_score = np.mean([np.std(features_array[:, i]) for i in range(features_array.shape[1])])
        diversity_score = min(1.0, diversity_score / 100)  # Normalize
        
        # Overall quality score
        quality_score = (balance_score * 0.4 + completeness_score * 0.4 + diversity_score * 0.2)
        
        return min(1.0, max(0.0, quality_score))
    
    def _calculate_feature_completeness(self, features_list: List[List[float]]) -> float:
        """Calculate feature completeness ratio."""
        if not features_list:
            return 0.0
        
        features_array = np.array(features_list)
        total_values = features_array.size
        missing_values = np.isnan(features_array).sum() + np.isinf(features_array).sum()
        
        return 1 - (missing_values / total_values)
    
    def _save_dataset(self, dataset: TrainingDataset, features: List[List[float]], 
                     labels: List[int]):
        """Save dataset to disk."""
        # Save metadata
        datasets_file = self.data_dir / "training_datasets.json"
        
        if datasets_file.exists():
            with open(datasets_file, 'r') as f:
                data = json.load(f)
        else:
            data = {'datasets': []}
        
        # Convert dataset to dict for JSON serialization
        dataset_dict = {
            'dataset_id': dataset.dataset_id,
            'name': dataset.name,
            'description': dataset.description,
            'sources': [
                {
                    'source_id': src.source_id,
                    'source_type': src.source_type,
                    'bank_type': src.bank_type,
                    'data_format': src.data_format,
                    'created_date': src.created_date,
                    'sample_count': src.sample_count,
                    'quality_score': src.quality_score,
                    'is_validated': src.is_validated
                } for src in dataset.sources
            ],
            'total_samples': dataset.total_samples,
            'positive_samples': dataset.positive_samples,
            'negative_samples': dataset.negative_samples,
            'feature_columns': dataset.feature_columns,
            'data_quality_metrics': dataset.data_quality_metrics,
            'created_date': dataset.created_date,
            'last_updated': dataset.last_updated,
            'version': dataset.version
        }
        
        # Update or add dataset
        existing_idx = None
        for i, existing in enumerate(data['datasets']):
            if existing['dataset_id'] == dataset.dataset_id:
                existing_idx = i
                break
        
        if existing_idx is not None:
            data['datasets'][existing_idx] = dataset_dict
        else:
            data['datasets'].append(dataset_dict)
        
        # Save metadata
        with open(datasets_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save actual training data
        data_file = self.data_dir / f"{dataset.dataset_id}.pkl"
        training_data = {
            'features': features,
            'labels': labels,
            'dataset_info': dataset_dict
        }
        joblib.dump(training_data, data_file)
    
    def _load_dataset_data(self, dataset_id: str) -> Tuple[List[List[float]], List[int]]:
        """Load dataset features and labels."""
        data_file = self.data_dir / f"{dataset_id}.pkl"
        
        if not data_file.exists():
            raise FileNotFoundError(f"Dataset file not found: {data_file}")
        
        training_data = joblib.load(data_file)
        return training_data['features'], training_data['labels']
    
    def _save_model_versions(self):
        """Save model version history."""
        versions_file = self.model_dir / "model_versions.json"
        
        with open(versions_file, 'w') as f:
            json.dump(self.model_versions, f, indent=2, default=str)
    
    def get_best_model(self) -> Optional[Dict[str, Any]]:
        """Get the best performing model version."""
        if not self.model_versions:
            return None
        
        # Sort by test accuracy
        best_version = max(self.model_versions, key=lambda v: v['test_accuracy'])
        return best_version
    
    def load_production_model(self, version_id: Optional[str] = None):
        """Load model for production use."""
        if version_id:
            # Load specific version
            model_path = self.model_dir / f"{version_id}.pkl"
        else:
            # Load best model
            best_model = self.get_best_model()
            if not best_model:
                raise ValueError("No trained models available")
            model_path = self.model_dir / f"{best_model['version_id']}.pkl"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        return joblib.load(model_path)

# ================================
# TRAINING VIEWMODEL
# ================================

class TrainingViewModel(BaseViewModel):
    """ViewModel for enhanced training functionality."""
    
    def __init__(self):
        super().__init__()
        self.training_service = TrainingService()
        
        self._available_datasets: List[TrainingDataset] = []
        self._selected_dataset: Optional[TrainingDataset] = None
        self._training_config = ModelTrainingConfig()
        self._model_versions: List[Dict[str, Any]] = []
        self._is_training = False
        self._training_progress = 0
        
        self._load_available_datasets()
    
    def _load_available_datasets(self):
        """Load available training datasets."""
        self._available_datasets = list(self.training_service.training_datasets.values())
        self._model_versions = self.training_service.model_versions
        
        self.notify_property_changed('available_datasets', self._available_datasets)
        self.notify_property_changed('model_versions', self._model_versions)
    
    @property
    def available_datasets(self) -> List[TrainingDataset]:
        return self._available_datasets
    
    @property
    def selected_dataset(self) -> Optional[TrainingDataset]:
        return self._selected_dataset
    
    @selected_dataset.setter
    def selected_dataset(self, dataset: Optional[TrainingDataset]):
        if self._selected_dataset != dataset:
            self._selected_dataset = dataset
            self.notify_property_changed('selected_dataset', dataset)
    
    @property
    def training_config(self) -> ModelTrainingConfig:
        return self._training_config
    
    @property
    def model_versions(self) -> List[Dict[str, Any]]:
        return self._model_versions
    
    @property
    def is_training(self) -> bool:
        return self._is_training
    
    @property
    def training_progress(self) -> int:
        return self._training_progress
    
    def create_dataset_from_feedback_command(self, feedback_data: List[Dict], 
                                           dataset_name: str) -> bool:
        """Create training dataset from self-learning feedback."""
        try:
            self.clear_error()
            
            dataset = self.training_service.create_dataset_from_feedback(
                feedback_data, dataset_name
            )
            
            self._load_available_datasets()
            
            logger.info(f"Created dataset {dataset.dataset_id} with {dataset.total_samples} samples")
            return True
            
        except Exception as e:
            self.error_message = f"Failed to create dataset: {str(e)}"
            return False
    
    def train_model_command(self) -> bool:
        """Train model with selected dataset and configuration."""
        if not self._selected_dataset:
            self.error_message = "No dataset selected"
            return False
        
        try:
            self._is_training = True
            self._training_progress = 0
            self.clear_error()
            
            self.notify_property_changed('is_training', True)
            self.notify_property_changed('training_progress', 0)
            
            # Train model
            model_version = self.training_service.train_enhanced_model(
                self._selected_dataset.dataset_id,
                self._training_config
            )
            
            self._training_progress = 100
            self.notify_property_changed('training_progress', 100)
            
            # Refresh model versions
            self._load_available_datasets()
            
            return True
            
        except Exception as e:
            self.error_message = f"Training failed: {str(e)}"
            return False
        finally:
            self._is_training = False
            self.notify_property_changed('is_training', False)
    
    def merge_datasets_command(self, dataset_ids: List[str], merged_name: str) -> bool:
        """Merge multiple datasets."""
        try:
            self.clear_error()
            
            merged_dataset = self.training_service.merge_datasets(dataset_ids, merged_name)
            self._load_available_datasets()
            
            return True
            
        except Exception as e:
            self.error_message = f"Failed to merge datasets: {str(e)}"
            return False

# ================================
# WHY TRAINING IS MORE CRITICAL NOW
# ================================

"""
TRAINING MODEL IMPORTANCE IN ENHANCED VERSION:

1. ✅ DIVERSE DATA SOURCES
   - File uploads (CSV, Excel)
   - Bank APIs (live transaction feeds)
   - ERP databases (multiple query results)
   - Manual feedback (self-learning)
   → Need unified model handling all sources

2. ✅ TEMPLATE VARIATIONS
   - Different bank statement formats
   - Various ERP system outputs
   - Multiple API response structures
   → Model must adapt to format differences

3. ✅ SCALE & PERFORMANCE
   - Enterprise deployments
   - High-volume transactions
   - Real-time processing requirements
   → Need production-grade, optimized models

4. ✅ MULTI-TENANT SUPPORT
   - Different organizations
   - Custom business rules
   - Industry-specific matching patterns
   → Custom models per tenant/use case

5. ✅ CONTINUOUS IMPROVEMENT
   - Self-learning from user feedback
   - Performance monitoring
   - Model retraining schedules
   → Advanced training pipeline essential

BEFORE (Simple): File → ML Model → Results
AFTER (Enhanced): Multiple Sources → Advanced Training → Custom Models → Production Deployment
"""

if __name__ == "__main__":
    logger.info("🤖 Enhanced Training Model Integration")
    logger.info("=" * 50)