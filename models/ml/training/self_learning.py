# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# training/self_learning.py
# ================================

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SelfLearningManager:
    """Manages self-learning and feedback collection."""
    
    def __init__(self, data_dir: str = "data/training/feedback"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.feedback_file = self.data_dir / "feedback_history.json"
        self.performance_file = self.data_dir / "performance_history.json"
        self.uncertain_cases_file = self.data_dir / "uncertain_cases.json"
        
        self.feedback_history = self._load_feedback_history()
        self.performance_history = self._load_performance_history()
    
    def _load_feedback_history(self) -> List[Dict[str, Any]]:
        """Load feedback history from file."""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load feedback history: {e}")
        return []
    
    def _load_performance_history(self) -> List[Dict[str, Any]]:
        """Load performance history from file."""
        if self.performance_file.exists():
            try:
                with open(self.performance_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load performance history: {e}")
        return []
    
    def collect_feedback(self, case_index: int, bank_row: Dict, erp_row: Dict,
                        user_decision: int, confidence: float, 
                        user_comment: str = "") -> bool:
        """Collect human feedback for a specific case."""
        try:
            feedback_entry = {
                'timestamp': datetime.now().isoformat(),
                'case_index': case_index,
                'bank_data': bank_row,
                'erp_data': erp_row,
                'user_decision': user_decision,
                'model_confidence': confidence,
                'user_comment': user_comment,
                'feedback_source': 'manual_review'
            }
            
            self.feedback_history.append(feedback_entry)
            self._save_feedback_history()
            
            logger.info(f"Collected feedback for case {case_index}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to collect feedback: {e}")
            return False
    
    def get_training_data_from_feedback(self) -> List[Dict[str, Any]]:
        """Get feedback data suitable for model retraining."""
        return [fb for fb in self.feedback_history if fb.get('user_decision') is not None]
    
    def calculate_model_improvement(self, old_accuracy: float, 
                                  new_accuracy: float) -> Dict[str, Any]:
        """Calculate and record model improvement metrics."""
        improvement = {
            'timestamp': datetime.now().isoformat(),
            'old_accuracy': old_accuracy,
            'new_accuracy': new_accuracy,
            'improvement': new_accuracy - old_accuracy,
            'improvement_percentage': ((new_accuracy - old_accuracy) / old_accuracy) * 100 if old_accuracy > 0 else 0,
            'feedback_samples_used': len(self.feedback_history)
        }
        
        self.performance_history.append(improvement)
        self._save_performance_history()
        
        return improvement
    
    def _save_feedback_history(self):
        """Save feedback history to file."""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save feedback history: {e}")
    
    def _save_performance_history(self):
        """Save performance history to file."""
        try:
            with open(self.performance_file, 'w') as f:
                json.dump(self.performance_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save performance history: {e}")