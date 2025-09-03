# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# training/data_processor.py
# ================================

import numpy as np
from typing import List, Tuple, Dict, Any

import logging
from datetime import datetime
from models.ml.training.data_models import TrainingDataset
from models.ml.feature_utils import compute_transaction_features

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """Handles feature extraction from different data sources."""
    
    @staticmethod
    def extract_features_from_feedback(bank_data: Dict, erp_data: Dict) -> List[float]:
        """Extract features from feedback data."""
        try:
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
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            raise
    
    @staticmethod
    def extract_features_from_transactions(bank_txn, erp_txn) -> List[float]:
        """Extract features from transaction objects."""
        try:
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
        except Exception as e:
            logger.error(f"Transaction feature extraction failed: {e}")
            raise

class DataQualityAnalyzer:
    """Analyzes and validates training data quality."""
    
    @staticmethod
    def calculate_data_quality(features_list: List[List[float]], 
                              labels_list: List[int]) -> float:
        """Calculate overall data quality score."""
        if not features_list:
            return 0.0
        
        # Balance score (closer to 50/50 is better)
        positive_ratio = sum(labels_list) / len(labels_list)
        balance_score = 1 - abs(0.5 - positive_ratio) * 2
        
        # Feature completeness (no NaN/infinite values)
        features_array = np.array(features_list)
        missing_values = np.isnan(features_array).sum() + np.isinf(features_array).sum()
        completeness_score = 1 - (missing_values / features_array.size)
        
        # Feature diversity (variance across features)
        diversity_scores = []
        for i in range(features_array.shape[1]):
            col_std = np.std(features_array[:, i])
            diversity_scores.append(min(1.0, col_std / 100))
        diversity_score = np.mean(diversity_scores)
        
        # Overall quality score
        quality_score = (balance_score * 0.4 + 
                        completeness_score * 0.4 + 
                        diversity_score * 0.2)
        
        return min(1.0, max(0.0, quality_score))
    
    @staticmethod
    def validate_features(features: List[List[float]]) -> Dict[str, Any]:
        """Validate feature matrix and return quality metrics."""
        if not features:
            return {"valid": False, "error": "Empty features"}
        
        features_array = np.array(features)
        
        # Check for invalid values
        has_nan = np.isnan(features_array).any()
        has_inf = np.isinf(features_array).any()
        
        # Check feature ranges
        feature_ranges = []
        for i in range(features_array.shape[1]):
            col = features_array[:, i]
            feature_ranges.append({
                "min": float(np.min(col)),
                "max": float(np.max(col)),
                "mean": float(np.mean(col)),
                "std": float(np.std(col))
            })
        
        return {
            "valid": not (has_nan or has_inf),
            "has_nan": has_nan,
            "has_inf": has_inf,
            "shape": features_array.shape,
            "feature_ranges": feature_ranges
        }

class DatasetBuilder:
    """Builds training datasets from various sources."""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.quality_analyzer = DataQualityAnalyzer()
    
    def build_from_feedback(self, feedback_data: List[Dict], 
                           dataset_name: str) -> Tuple[TrainingDataset, List[List[float]], List[int]]:
        """Build dataset from self-learning feedback."""
        features_list = []
        labels_list = []
        
        for feedback in feedback_data:
            try:
                features = self.feature_extractor.extract_features_from_feedback(
                    feedback['bank_data'], feedback['erp_data']
                )
                label = feedback['user_decision']
                
                features_list.append(features)
                labels_list.append(label)
                
            except Exception as e:
                logger.warning(f"Error processing feedback: {e}")
                continue
        
        if not features_list:
            raise ValueError("No valid features extracted from feedback")
        
        # Create dataset metadata
        dataset = TrainingDataset(
            dataset_id=f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=dataset_name,
            description=f"Dataset from {len(features_list)} feedback entries",
            total_samples=len(features_list),
            positive_samples=sum(labels_list),
            negative_samples=len(labels_list) - sum(labels_list),
            feature_columns=['amount_difference', 'date_difference', 
                           'description_similarity', 'signed_amount_match', 'same_day']
        )
        
        # Add quality metrics
        dataset.data_quality_metrics = {
            'quality_score': self.quality_analyzer.calculate_data_quality(features_list, labels_list),
            'validation': self.quality_analyzer.validate_features(features_list)
        }
        
        return dataset, features_list, labels_list