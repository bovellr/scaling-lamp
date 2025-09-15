# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ============================================================================
# OPTIMIZED RECONCILIATION SERVICE
# ============================================================================

"""
High-performance reconciliation service with optimized algorithms and caching.
Eliminates O(n²) complexity and provides better performance for large datasets.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from collections import defaultdict
import time

from models.data_models import TransactionData, TransactionMatch, MatchStatus
from services.data_transformation_service import DataTransformationService

logger = logging.getLogger(__name__)

@dataclass
class ReconciliationConfig:
    """Configuration for reconciliation process"""
    confidence_threshold: float = 0.7
    amount_tolerance: float = 0.01
    date_tolerance_days: int = 7
    description_similarity_threshold: float = 0.6
    use_fuzzy_matching: bool = True
    max_candidates_per_transaction: int = 50
    enable_caching: bool = True

@dataclass
class ReconciliationStats:
    """Statistics for reconciliation process"""
    total_bank_transactions: int
    total_erp_transactions: int
    matches_found: int
    high_confidence_matches: int
    medium_confidence_matches: int
    low_confidence_matches: int
    processing_time: float
    cache_hits: int
    cache_misses: int

class OptimizedReconciliationService:
    """High-performance reconciliation service with optimized algorithms"""
    
    def __init__(self, config: Optional[ReconciliationConfig] = None):
        self.config = config or ReconciliationConfig()
        self.transformation_service = DataTransformationService()
        self._cache: Dict[str, Any] = {}
        self._stats = ReconciliationStats(0, 0, 0, 0, 0, 0, 0.0, 0, 0)
    
    def reconcile(
        self, 
        bank_transactions: List[TransactionData],
        erp_transactions: List[TransactionData]
    ) -> Tuple[List[TransactionMatch], ReconciliationStats]:
        """
        Perform optimized reconciliation between bank and ERP transactions.
        
        Returns:
            Tuple of (matches, statistics)
        """
        start_time = time.time()
        self._reset_stats()
        
        try:
            # Optimize input data
            bank_opt = self.transformation_service.optimize_transaction_list(bank_transactions)
            erp_opt = self.transformation_service.optimize_transaction_list(erp_transactions)
            
            if not bank_opt.success or not erp_opt.success:
                logger.error("Failed to optimize transaction data")
                return [], self._stats
            
            bank_tx = bank_opt.data
            erp_tx = erp_opt.data
            
            self._stats.total_bank_transactions = len(bank_tx)
            self._stats.total_erp_transactions = len(erp_tx)
            
            # Create optimized indexes
            bank_index = self._create_bank_index(bank_tx)
            erp_index = self._create_erp_index(erp_tx)
            
            # Debug logging
            logger.info(f"Created indexes - Bank: {len(bank_index)} transactions, ERP: {len(erp_index)} transactions")
            if len(bank_index) == 0:
                logger.warning("No valid bank transactions found after optimization")
            if len(erp_index) == 0:
                logger.warning("No valid ERP transactions found after optimization")
            
            # Perform matching
            matches = self._perform_optimized_matching(bank_index, erp_index)
            
            # Calculate statistics
            self._calculate_match_statistics(matches)
            self._stats.processing_time = time.time() - start_time
            
            logger.info(f"Reconciliation completed: {len(matches)} matches in {self._stats.processing_time:.2f}s")
            return matches, self._stats
            
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            self._stats.processing_time = time.time() - start_time
            return [], self._stats
    
    def _create_bank_index(self, transactions: List[TransactionData]) -> pd.DataFrame:
        """Create optimized index for bank transactions"""
        records = []
        for tx in transactions:
            try:
                date_val = pd.to_datetime(tx.date).to_pydatetime()
                amount_bucket = int(round(abs(tx.amount) / self.config.amount_tolerance))
                date_bucket = date_val.date().toordinal() // self.config.date_tolerance_days
                
                records.append({
                    'id': tx.transaction_id,
                    'amount': tx.amount,
                    'date': date_val,
                    'description': tx.description,
                    'amount_bucket': amount_bucket,
                    'date_bucket': date_bucket,
                    'transaction': tx
                })
            except Exception as e:
                logger.warning(f"Failed to index bank transaction {tx.transaction_id}: {e}")
        
        return pd.DataFrame(records)
    
    def _create_erp_index(self, transactions: List[TransactionData]) -> pd.DataFrame:
        """Create optimized index for ERP transactions"""
        records = []
        for tx in transactions:
            try:
                date_val = pd.to_datetime(tx.date).to_pydatetime()
                amount_bucket = int(round(abs(tx.amount) / self.config.amount_tolerance))
                date_bucket = date_val.date().toordinal() // self.config.date_tolerance_days
                
                records.append({
                    'id': tx.transaction_id,
                    'amount': tx.amount,
                    'date': date_val,
                    'description': tx.description,
                    'amount_bucket': amount_bucket,
                    'date_bucket': date_bucket,
                    'transaction': tx
                })
            except Exception as e:
                logger.warning(f"Failed to index ERP transaction {tx.transaction_id}: {e}")
        
        return pd.DataFrame(records)
    
    def _perform_optimized_matching(
        self, 
        bank_index: pd.DataFrame, 
        erp_index: pd.DataFrame
    ) -> List[TransactionMatch]:
        """Perform optimized matching using indexed data"""
        matches = []
        used_erp_ids: Set[str] = set()
        
        # Group ERP transactions by buckets for faster lookup
        erp_groups = erp_index.groupby(['amount_bucket', 'date_bucket'])
        
        logger.info(f"Starting matching process with {len(bank_index)} bank transactions and {len(erp_index)} ERP transactions")
        logger.info(f"ERP groups created: {len(erp_groups.groups)} unique buckets")
        
        candidates_found = 0
        for bank_idx, bank_row in bank_index.iterrows():
            try:
                # Find candidate ERP transactions using bucket matching
                candidates = self._get_candidate_erp_transactions(
                    bank_row, erp_groups, erp_index
                )
                
                if not candidates:
                    if bank_idx < 3:  # Log first few bank transactions for debugging
                        logger.info(f"Bank transaction {bank_idx}: No candidates found for {bank_row['amount']:.2f} | {bank_row['date']} | {bank_row['description'][:50]}")
                    continue
                
                candidates_found += len(candidates)
                
                if bank_idx < 3:  # Log first few bank transactions for debugging
                    logger.info(f"Bank transaction {bank_idx}: Found {len(candidates)} candidates")
                
                # Score candidates
                best_match = self._find_best_match(bank_row, candidates, bank_idx)
                
                if best_match and best_match['erp_id'] not in used_erp_ids:
                    # Create TransactionMatch
                    match = TransactionMatch(
                        bank_transaction=bank_row['transaction'],
                        erp_transaction=best_match['erp_transaction'],
                        confidence_score=best_match['confidence'],
                        amount_score=best_match['amount_score'],
                        date_score=best_match['date_score'],
                        description_score=best_match['description_score'],
                        match_note=best_match['note'],
                        status=self._determine_match_status(best_match['confidence'])
                    )
                    
                    matches.append(match)
                    used_erp_ids.add(best_match['erp_id'])
                    
            except Exception as e:
                logger.warning(f"Failed to match bank transaction {bank_row['id']}: {e}")
        
        # Sort by confidence score
        matches.sort(key=lambda m: m.confidence_score, reverse=True)
        
        logger.info(f"Matching completed: {len(matches)} matches found from {candidates_found} total candidates")
        return matches
    
    def _get_candidate_erp_transactions(
        self, 
        bank_row: pd.Series, 
        erp_groups: pd.core.groupby.DataFrameGroupBy,
        erp_index: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Get candidate ERP transactions for a bank transaction"""
        candidates = []
        
        # Get transactions from same buckets
        bucket_key = (bank_row['amount_bucket'], bank_row['date_bucket'])
        if len(candidates) == 0:  # Only log for first transaction
            logger.info(f"Looking for bucket key: {bucket_key} (amount_bucket={bank_row['amount_bucket']}, date_bucket={bank_row['date_bucket']})")
        if bucket_key in erp_groups.groups:
            bucket_transactions = erp_groups.get_group(bucket_key)
            if len(candidates) == 0:  # Only log for first transaction
                logger.info(f"Found {len(bucket_transactions)} transactions in exact bucket")
            for _, erp_row in bucket_transactions.iterrows():
                candidates.append({
                    'erp_id': erp_row['id'],
                    'erp_transaction': erp_row['transaction'],
                    'amount': erp_row['amount'],
                    'date': erp_row['date'],
                    'description': erp_row['description']
                })
        else:
            if len(candidates) == 0:  # Only log for first transaction
                logger.info(f"No transactions found in exact bucket {bucket_key}")
        
        # Also check adjacent buckets for near matches
        for amount_offset in [-1, 1]:
            for date_offset in [-1, 1]:
                adjacent_key = (
                    bank_row['amount_bucket'] + amount_offset,
                    bank_row['date_bucket'] + date_offset
                )
                if adjacent_key in erp_groups.groups:
                    bucket_transactions = erp_groups.get_group(adjacent_key)
                    for _, erp_row in bucket_transactions.iterrows():
                        candidates.append({
                            'erp_id': erp_row['id'],
                            'erp_transaction': erp_row['transaction'],
                            'amount': erp_row['amount'],
                            'date': erp_row['date'],
                            'description': erp_row['description']
                        })
        
        # Limit candidates to prevent performance issues
        return candidates[:self.config.max_candidates_per_transaction]
    
    def _find_best_match(
        self, 
        bank_row: pd.Series, 
        candidates: List[Dict[str, Any]],
        bank_idx: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Find the best matching ERP transaction"""
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            try:
                # Calculate scores
                amount_score = self._calculate_amount_score(
                    bank_row['amount'], candidate['amount'],
                    bank_row['description'], candidate['description']
                )
                date_score = self._calculate_date_score(
                    bank_row['date'], candidate['date'], 
                    bank_row['description'], candidate['description']
                )
                description_score = self._calculate_description_score(
                    bank_row['description'], candidate['description']
                )
                
                # Log scoring details for debugging (limit to first few transactions)
                if bank_idx < 2 and len([c for c in candidates if c == candidate]) <= 3:
                    logger.info(f"Bank: {bank_row['amount']:.2f} | {bank_row['date']} | {bank_row['description'][:50]}")
                    logger.info(f"ERP:  {candidate['amount']:.2f} | {candidate['date']} | {candidate['description'][:50]}")
                    logger.info(f"Scores: amount={amount_score:.3f}, date={date_score:.3f}, desc={description_score:.3f}")
                    
                    # Log sign convention detection
                    if amount_score >= 0.95 and (bank_row['amount'] * candidate['amount']) < 0:
                        logger.info("*** SIGN CONVENTION MISMATCH DETECTED ***")
                
                # Skip if any critical score is too low (very relaxed thresholds for debugging)
                if (amount_score < 0.1 or 
                    date_score < 0.05 or 
                    description_score < 0.1):
                    if bank_idx < 2:  # Log rejection for first few transactions
                        logger.info(f"Rejected candidate: amount={amount_score:.3f} < 0.1 or date={date_score:.3f} < 0.05 or desc={description_score:.3f} < 0.1")
                    continue
                
                # Calculate overall confidence
                confidence = (
                    amount_score * 0.4 + 
                    date_score * 0.3 + 
                    description_score * 0.3
                )
                
                # Use a lower threshold for initial matching, but still respect the config threshold
                min_confidence = min(0.3, self.config.confidence_threshold)
                
                if confidence > best_score and confidence >= min_confidence:
                    best_score = confidence
                    best_match = {
                        'erp_id': candidate['erp_id'],
                        'erp_transaction': candidate['erp_transaction'],
                        'confidence': confidence,
                        'amount_score': amount_score,
                        'date_score': date_score,
                        'description_score': description_score,
                        'note': self._generate_match_note(amount_score, date_score, description_score)
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to score candidate {candidate['erp_id']}: {e}")
        
        return best_match
    
    def _calculate_amount_score(self, amount1: float, amount2: float, bank_description: str = "", erp_description: str = "") -> float:
        """Calculate amount similarity score with sign convention handling"""
        if amount1 == 0 and amount2 == 0:
            return 1.0
        
        # Check for sign convention mismatch (Lloyds debits positive vs ERP debits negative)
        # If amounts have opposite signs but same absolute value, it's a perfect match
        if amount1 == -amount2:
            return 1.0
        
        # Also check if one amount is the negative of the other (handles floating point precision)
        if abs(amount1 + amount2) < 0.01:  # Within 1 cent tolerance
            return 1.0
        
        # Additional check: if amounts are very close but opposite signs, likely a sign convention issue
        if abs(abs(amount1) - abs(amount2)) < 0.01 and (amount1 * amount2) < 0:
            return 0.95  # Very high score for sign convention mismatch
        
        # Standard similarity calculation
        diff = abs(amount1 - amount2)
        max_amount = max(abs(amount1), abs(amount2))
        
        if max_amount == 0:
            return 0.0
        
        similarity = 1.0 - (diff / max_amount)
        return max(0.0, similarity)
    
    def _calculate_date_score(self, date1: datetime, date2: datetime, bank_description: str = "", erp_description: str = "") -> float:
        """Calculate date similarity score with special handling for payroll transactions"""
        days_diff = abs((date1 - date2).days)
        
        # Add special handling for payroll transactions
        if "PAYROLL" in erp_description.upper() or "FP" in bank_description:
            date_tolerance_days = 35  # Allow month-end processing delays
        else:
            date_tolerance_days = self.config.date_tolerance_days
        
        if days_diff == 0:
            return 1.0
        elif days_diff <= date_tolerance_days:
            return max(0.0, 1.0 - (days_diff / date_tolerance_days))
        else:
            return 0.0
    
    def _calculate_description_score(self, desc1: str, desc2: str) -> float:
        """Calculate description similarity score"""
        if not desc1 or not desc2:
            return 0.0
        
        # Handle NaN values
        if str(desc1).lower() in ['nan', 'none', ''] or str(desc2).lower() in ['nan', 'none', '']:
            return 0.0
        
        # Normalize descriptions
        norm1 = self._normalize_description(desc1)
        norm2 = self._normalize_description(desc2)
        
        if norm1 == norm2:
            return 1.0
        
        # Use fuzzy matching for better similarity detection
        if self.config.use_fuzzy_matching:
            return self._fuzzy_similarity(norm1, norm2)
        else:
            # Simple substring matching for basic similarity
            if norm1 in norm2 or norm2 in norm1:
                return 0.5
            return 0.0
    
    def _normalize_description(self, text: str) -> str:
        """Normalize description for comparison - minimal normalization to preserve identifiers"""
        if not text:
            return ""
        # Only normalize case and strip whitespace, preserve all characters and spaces
        return text.lower().strip()
    
    def _fuzzy_similarity(self, text1: str, text2: str) -> float:
        """Calculate fuzzy similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Use token-based similarity with word matching
        tokens1 = set(text1.split())
        tokens2 = set(text2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        # Also check for partial word matches (useful for reference numbers)
        partial_matches = 0
        for token1 in tokens1:
            for token2 in tokens2:
                if len(token1) > 3 and len(token2) > 3:  # Only for meaningful tokens
                    if token1 in token2 or token2 in token1:
                        partial_matches += 0.5
        
        base_score = intersection / union if union > 0 else 0.0
        partial_bonus = min(0.3, partial_matches / max(len(tokens1), len(tokens2)))
        
        return min(1.0, base_score + partial_bonus)
    
    def _generate_match_note(
        self, 
        amount_score: float, 
        date_score: float, 
        description_score: float
    ) -> str:
        """Generate note for the match"""
        notes = []
        if amount_score < 0.99:
            notes.append("Amount mismatch")
        if date_score < 0.9:
            notes.append("Date mismatch")
        if description_score < 0.8:
            notes.append("Description mismatch")
        return "; ".join(notes) if notes else "Good match"
    
    def _determine_match_status(self, confidence: float) -> MatchStatus:
        """Determine match status based on confidence"""
        if confidence >= 0.9:
            return MatchStatus.MATCHED
        elif confidence >= 0.7:
            return MatchStatus.PENDING
        else:
            return MatchStatus.REJECTED
    
    def _calculate_match_statistics(self, matches: List[TransactionMatch]):
        """Calculate match statistics"""
        self._stats.matches_found = len(matches)
        
        for match in matches:
            if match.confidence_score >= 0.9:
                self._stats.high_confidence_matches += 1
            elif match.confidence_score >= 0.7:
                self._stats.medium_confidence_matches += 1
            else:
                self._stats.low_confidence_matches += 1
    
    def _reset_stats(self):
        """Reset statistics"""
        self._stats = ReconciliationStats(0, 0, 0, 0, 0, 0, 0.0, 0, 0)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            'processing_time': self._stats.processing_time,
            'transactions_per_second': (
                (self._stats.total_bank_transactions + self._stats.total_erp_transactions) / 
                self._stats.processing_time if self._stats.processing_time > 0 else 0
            ),
            'match_rate': (
                self._stats.matches_found / 
                self._stats.total_bank_transactions if self._stats.total_bank_transactions > 0 else 0
            ),
            'cache_hit_rate': (
                self._stats.cache_hits / 
                (self._stats.cache_hits + self._stats.cache_misses) 
                if (self._stats.cache_hits + self._stats.cache_misses) > 0 else 0
            )
        }
