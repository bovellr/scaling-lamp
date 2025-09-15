# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# ML ENGINE
# ============================================================================

# models/ml_engine.py
try:  # Optional dependency
    from sklearn.ensemble import RandomForestClassifier  # type: ignore
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # pragma: no cover - optional
    RandomForestClassifier = None
    TfidfVectorizer = None
    cosine_similarity = None
try:  # Optional dependency
    from rapidfuzz import fuzz  # type: ignore
except Exception:  # pragma: no cover - optional
    from difflib import SequenceMatcher

    class _Fuzz:
        @staticmethod
        def token_sort_ratio(a: str, b: str) -> int:
            return int(SequenceMatcher(None, a, b).ratio() * 100)

    fuzz = _Fuzz()

try:  # Optional dependency
    import joblib  # type: ignore
except Exception:  # pragma: no cover - optional
    class joblib:  # type: ignore
        @staticmethod
        def dump(model, path):
            return None

        @staticmethod
        def load(path):
            return None
from typing import List, Tuple, Optional, Dict
import logging
import math
from pathlib import Path
from datetime import datetime
import pandas as pd
from .data_models import (
    Transaction,
    TransactionMatch,
    MatchStatus,
    BankTransaction,
    ERPTransaction,
)
from .ml.training.data_models import ModelTrainingConfig, TrainingDataset
from .ml.training.trainer import TrainingService
from .ml.feature_utils import compute_transaction_features


class MLEngine:
    """Machine Learning engine for transaction matching"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.training_service = None
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english') if TfidfVectorizer else None
        self.model_path = Path(model_path) if model_path else Path("models/ml/training/trained_model.pkl")
        
        # Load existing model if available
        self.load_model()
    
        # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _to_datetime(self, value) -> datetime:
        """Convert value to datetime with robust error handling"""
        if value is None:
            raise ValueError("Date value is None")

        if isinstance(value, datetime):
            return value

        try:
            return datetime.fromisoformat(str(value))
        except (ValueError, TypeError):
            try:
                return pd.to_datetime(value).to_pydatetime()
            except Exception:
                raise ValueError(f"Cannot convert {value} to datetime")

    def _validate_transaction(
        self,
        tx: Transaction,
        source: str,
        amount_tolerance: float,
        date_tolerance: int,
    ) -> Optional[Tuple[datetime, int, int]]:
        """Validate transaction fields and compute bucket values."""
        try:
            if source == 'ERP':
                date_val = getattr(tx, 'description_date', None) or tx.date
            else:
                date_val = tx.date
            if date_val is None or pd.isna(date_val):
                raise ValueError("no valid date")

            if tx.amount is None or pd.isna(tx.amount) or math.isnan(tx.amount):
                raise ValueError("invalid amount")

            dt = self._to_datetime(date_val)
            amount_bucket = int(round(abs(tx.amount) / amount_tolerance))
            date_bucket = dt.date().toordinal() // date_tolerance
            return dt, amount_bucket, date_bucket
        except Exception as e:
            self.logger.warning(
                f"Skipping {source} transaction {getattr(tx, 'id', 'unknown')} - {e}"
            )
            return None

    def _index_erp_transactions(
        self,
        erp_transactions: List[Transaction],
        amount_tolerance: float,
        date_tolerance: int,
    ) -> pd.DataFrame:
        """Create an index of ERP transactions using pandas for fast lookup."""
        records = []
        for tx in erp_transactions:
            validated = self._validate_transaction(tx, 'ERP', amount_tolerance, date_tolerance)
            if not validated:
                continue
            _, amount_bucket, date_bucket = validated
            records.append({
                'amount_bucket': amount_bucket,
                'date_bucket': date_bucket,
                'tx': tx,
            })

        if not records:
            return pd.DataFrame(columns=['amount_bucket', 'date_bucket', 'tx'])

        return pd.DataFrame.from_records(records)

    def _get_candidate_transactions(
        self,
        erp_df: pd.DataFrame,
        amount_bucket: int,
        date_bucket: int,
    ) -> List[Transaction]:
        """Retrieve candidate ERP transactions for a given bank bucket."""
        if erp_df.empty:
            return []

        mask = (
            erp_df['amount_bucket'].between(amount_bucket - 1, amount_bucket + 1)
            & erp_df['date_bucket'].between(date_bucket - 1, date_bucket + 1)
        )
        return erp_df.loc[mask, 'tx'].tolist()

    def generate_matches(
        self,
        bank_transactions: List[BankTransaction],
        erp_transactions: List[ERPTransaction],
        confidence_threshold: float = 0.5,
    ) -> List[TransactionMatch]:
        """Generate potential matches between bank and ERP transactions with optimized performance"""
        matches = []
        
        self.logger.info(
            f"Generating matches for {len(bank_transactions)} bank and {len(erp_transactions)} ERP transactions"
        )

        amount_tolerance = 1.0
        date_tolerance = 7

        # Build optimized index of ERP transactions
        erp_df = self._index_erp_transactions(erp_transactions, amount_tolerance, date_tolerance)
        
        # Pre-validate all bank transactions to avoid repeated validation
        validated_bank_transactions = []
        for bank_tx in bank_transactions:
            validated = self._validate_transaction(bank_tx, 'bank', amount_tolerance, date_tolerance)
            if validated:
                validated_bank_transactions.append((bank_tx, validated))

        # Use vectorized operations where possible
        for bank_tx, (bank_dt, bank_amount_bucket, bank_date_bucket) in validated_bank_transactions:
            candidate_erps = self._get_candidate_transactions(
                erp_df, bank_amount_bucket, bank_date_bucket
            )

            # Limit candidates to prevent performance issues
            if len(candidate_erps) > 100:
                candidate_erps = candidate_erps[:100]

            for erp_tx in candidate_erps:
                try:
                    erp_date_val = getattr(erp_tx, 'description_date', None) or erp_tx.date
                    erp_dt = self._to_datetime(erp_date_val)
                    
                    # Early exit conditions for performance
                    amount_diff = abs(abs(bank_tx.amount) - abs(erp_tx.amount))
                    if amount_diff > amount_tolerance:
                        continue
                    
                    date_diff = abs((bank_dt - erp_dt).days)
                    if date_diff > date_tolerance:
                        continue

                    # Calculate match features
                    features = self._extract_features(bank_tx, erp_tx)
                    
                    # Predict match probability
                    confidence = self._predict_match_probability(features)

                    # Only create match if confidence is above minimum threshold
                    if confidence < 0.3:  # Skip very low confidence matches
                        continue

                    note = self._generate_match_note(features, confidence, confidence_threshold)

                    match = TransactionMatch(
                        bank_transaction=bank_tx,
                        erp_transaction=erp_tx,
                        confidence_score=confidence,
                        match_note=note,
                        amount_score=features['amount_score'],
                        date_score=features['date_score'],
                        description_score=features['description_score'],
                        status=MatchStatus.MATCHED if confidence >= confidence_threshold 
                                else MatchStatus.PENDING if confidence > 0.5
                                    else MatchStatus.REJECTED
                        )
                    
                    matches.append(match)
                except Exception as e:
                    self.logger.warning(f"Error processing match for {bank_tx.id} and {erp_tx.id}: {e}")
                    continue
       
        # Sort by confidence score (highest first)
        matches.sort(key=lambda m: m.confidence_score, reverse=True)
        
        # Remove duplicate matches (keep highest confidence)
        unique_matches = self._remove_duplicate_matches(matches)
        
        self.logger.info(f"Generated {len(unique_matches)} potential matches")
        return unique_matches
    
    def _extract_features(self, bank_tx: Transaction, erp_tx: Transaction) -> Dict[str, float]:
        """Extract matching features for two transactions"""
        
        erp_date = getattr(erp_tx, 'description_date', None) or erp_tx.date

        base_features = compute_transaction_features(
            bank_tx.amount,
            bank_tx.date,
            bank_tx.description,
            erp_tx.amount,
            erp_date,
            erp_tx.description,
        )
        
        amount_diff = base_features['amount_diff']
        date_diff = base_features['date_diff']
        description_similarity = base_features['description_similarity']
        same_sign_score = float(base_features['signed_amount_match'])

        max_amount = max(abs(bank_tx.amount), abs(erp_tx.amount))
        amount_score = 1.0 - (amount_diff / max_amount) if max_amount > 0 else 1.0        
        date_score = max(0, 1.0 - (date_diff / 30.0))  # 30 days = 0 score
        
        # Description similarity
        description_score = description_similarity / 100.0
        
        return {
            'amount_score': amount_score,
            'date_score': date_score,
            'description_score': description_score,
            'same_sign_score': same_sign_score,
            'amount_diff': amount_diff,
            'date_diff': date_diff
        }
    
    def _predict_match_probability(self, features: Dict[str, float]) -> float:
        """Predict match probability using ML model or heuristic"""
        if self.model is not None:
            # Use trained model
            feature_vector = [
                features['amount_score'],
                features['date_score'],
                features['description_score'],
                features['same_sign_score'],
                features['amount_diff'],
                features['date_diff']
            ]
            try:
                probability = self.model.predict_proba([feature_vector])[0][1]
                return float(probability)
            except Exception as e:
                self.logger.warning(f"Model prediction failed: {e}, using heuristic")
        
        # Fallback heuristic
        weights = {
            'amount_score': 0.4,
            'date_score': 0.3,
            'description_score': 0.2,
            'same_sign_score': 0.1
        }
        
        score = sum(features[key] * weight for key, weight in weights.items())
        return min(1.0, max(0.0, score))
    
    def _remove_duplicate_matches(self, matches: List[TransactionMatch]) -> List[TransactionMatch]:
        """Remove duplicate matches, keeping the highest confidence ones"""
        used_bank_ids = set()
        used_erp_ids = set()
        unique_matches = []
        
        for match in matches:
            bank_id = match.bank_transaction.id
            erp_id = match.erp_transaction.id
            
            if bank_id not in used_bank_ids and erp_id not in used_erp_ids:
                unique_matches.append(match)
                used_bank_ids.add(bank_id)
                used_erp_ids.add(erp_id)
        
        return unique_matches
    
    def _generate_match_note(self, features: Dict[str, float], confidence: float, confidence_threshold: float) -> str:
        """Generate a note for the match"""
        notes = []
        if features['amount_score'] < 0.99:
            notes.append("Amount mismatch")
        if features['date_score'] < 0.9:
                notes.append("Date mismatch")
        if features['description_score'] < 0.6:
            notes.append("Low description similarity")
        if confidence < confidence_threshold:
            notes.append("Manual review recommended")
        return "; ".join(notes)
    

    def set_training_service(self, training_service):
        """Inject training service for enhanced functionality"""
        self.training_service = training_service

    def train_from_dataset(self, dataset_id: str, config: ModelTrainingConfig) -> Dict:
        """Train using enhanced training service"""
        if not self.training_service:
            raise ValueError("Training service not configured")
        
        return self.training_service.train_from_dataset(dataset_id, config)

    def get_training_datasets(self) -> List[TrainingDataset]:
        """Get available training datasets"""
        if not self.training_service:
            return []
        return list(self.training_service.training_datasets.values())

    def train_model(self, training_matches: List[TransactionMatch]) -> None:
        """Train the ML model with user-confirmed matches"""
        if not training_matches:
            self.logger.warning("No training data provided")
            return
        
        # Prepare training data
        X = []
        y = []
        
        for match in training_matches:
            if match.status in [MatchStatus.MATCHED, MatchStatus.REJECTED]:
                features = self._extract_features(match.bank_transaction, match.erp_transaction)
                feature_vector = [
                    features['amount_score'],
                    features['date_score'],
                    features['description_score'],
                    features['same_sign_score'],
                    features['amount_diff'],
                    features['date_diff']
                ]
                X.append(feature_vector)
                y.append(1 if match.status == MatchStatus.MATCHED else 0)
        
        if len(X) < 5:  # Need minimum samples
            self.logger.warning("Insufficient training data for model training")
            return
        
        # Train model
        if RandomForestClassifier is None:
            class SimpleClassifier:
                def fit(self, X, y):
                    pass

                def predict_proba(self, X):
                    return [[0.5, 0.5] for _ in X]

            self.model = SimpleClassifier()
        else:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X, y)
        
        # Save model
        self.save_model()
        
        self.logger.info(f"Model trained with {len(X)} samples")
    
    def save_model(self) -> None:
        """Save the trained model to file"""
        if self.model is not None and joblib is not None:
            try:
                self.model_path.parent.mkdir(parents=True, exist_ok=True)
                joblib.dump(self.model, self.model_path)
                self.logger.info(f"Model saved to {self.model_path}")
            except Exception as e:
                self.logger.error(f"Failed to save model: {e}")
    
    def load_model(self) -> None:
        """Load trained model from file"""
        if self.model_path.exists() and joblib is not None:
            try:
                self.model = joblib.load(self.model_path)
                self.logger.info(f"Model loaded from {self.model_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load model: {e}")
                self.model = None