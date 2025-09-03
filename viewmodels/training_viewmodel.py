# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

# ================================
# PYSIDE6 INTEGRATION ARCHITECTURE
# ================================

# viewmodels/training_viewmodel.py
from typing import List, Dict, Any, Optional, Callable
import logging
from PySide6.QtCore import QObject, Signal, Property, QThread, QTimer
from PySide6.QtWidgets import QApplication

from models.ml.training.training_orchestrator import TrainingOrchestrator 
from models.ml.training.data_models import (
    ModelTrainingConfig,
    TrainingResult,
    TrainingDataset
)
from viewmodels.base_viewmodel import BaseViewModel

logger = logging.getLogger(__name__)

class TrainingWorkerThread(QThread):
    """Background thread for model training to prevent UI freezing."""
    
    training_progress = Signal(int)  # Progress percentage
    training_completed = Signal(object)  # TrainingResult
    training_failed = Signal(str)  # Error message
    
    def __init__(self, orchestrator: TrainingOrchestrator, 
                 dataset_name: str, config: ModelTrainingConfig, 
                 tune_hyperparameters: bool = False):
        super().__init__()
        self.orchestrator = orchestrator
        self.dataset_name = dataset_name
        self.config = config
        self.tune_hyperparameters = tune_hyperparameters
    
    def run(self):
        """Execute training in background thread."""
        try:
            # Emit progress updates
            self.training_progress.emit(10)  # Started
            
            # Perform training
            result = self.orchestrator.train_model_from_feedback(
                self.dataset_name, 
                self.config,
                self.tune_hyperparameters
            )
            
            self.training_progress.emit(100)  # Completed
            self.training_completed.emit(result)
            
        except Exception as e:
            logger.error(f"Training failed in worker thread: {e}")
            self.training_failed.emit(str(e))

class TrainingViewModel(BaseViewModel):
    """ViewModel for training functionality with PySide6 integration."""
    
    # Signals for UI updates
    training_started = Signal()
    training_progress_changed = Signal(int)
    training_completed = Signal(object)  # TrainingResult
    training_failed = Signal(str)
    
    datasets_changed = Signal()
    model_versions_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self.orchestrator = TrainingOrchestrator()
        
        # Properties
        self._available_datasets: List[TrainingDataset] = []
        self._selected_dataset: Optional[TrainingDataset] = None
        self._training_config = ModelTrainingConfig()
        self._model_versions: List[Dict[str, Any]] = []
        self._is_training = False
        self._training_progress = 0
        self._current_training_thread: Optional[TrainingWorkerThread] = None
        
        # Load initial data
        self._load_data()
    
    def _load_data(self):
        """Load initial datasets and model versions."""
        try:
            # Load from orchestrator
            self._available_datasets = list(self.orchestrator.dataset_builder.training_datasets.values()) if hasattr(self.orchestrator.dataset_builder, 'training_datasets') else []
            self._model_versions = self.orchestrator.model_versions
            
            # Emit signals
            self.datasets_changed.emit()
            self.model_versions_changed.emit()
            
        except Exception as e:
            logger.error(f"Failed to load training data: {e}")
            self.set_error(str(e))
    
    # Properties for QML/UI binding
    @Property(list, notify=datasets_changed)
    def available_datasets(self) -> List[Dict[str, Any]]:
        """Available datasets for UI binding."""
        return [
            {
                'dataset_id': ds.dataset_id,
                'name': ds.name,
                'description': ds.description,
                'total_samples': ds.total_samples,
                'positive_samples': ds.positive_samples,
                'created_date': ds.created_date,
                'quality_score': ds.data_quality_metrics.get('quality_score', 0.0)
            }
            for ds in self._available_datasets
        ]
    
    @Property(list, notify=model_versions_changed)
    def model_versions(self) -> List[Dict[str, Any]]:
        """Model versions for UI binding."""
        return self._model_versions
    
    @Property(bool, notify=training_started)
    def is_training(self) -> bool:
        """Whether training is currently in progress."""
        return self._is_training
    
    @Property(int, notify=training_progress_changed)
    def training_progress(self) -> int:
        """Current training progress (0-100)."""
        return self._training_progress
    
    @Property(str)
    def selected_model_type(self) -> str:
        """Currently selected model type."""
        return self._training_config.model_type
    
    @selected_model_type.setter
    def selected_model_type(self, value: str):
        """Set selected model type."""
        if self._training_config.model_type != value:
            self._training_config.model_type = value
            logger.info(f"Model type changed to: {value}")
    
    # Commands (callable from UI)
    def create_dataset_from_feedback(self, dataset_name: str) -> bool:
        """Create training dataset from feedback data."""
        try:
            self.clear_error()
            
            # Get feedback data
            feedback_data = self.orchestrator.self_learning_manager.get_training_data_from_feedback()
            
            if not feedback_data:
                self.set_error("No feedback data available")
                return False
            
            # Create dataset
            dataset, _, _ = self.orchestrator.dataset_builder.build_from_feedback(
                feedback_data, dataset_name
            )
            
            # Update lists
            self._available_datasets.append(dataset)
            self.datasets_changed.emit()
            
            logger.info(f"Created dataset: {dataset_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create dataset: {e}")
            self.set_error(str(e))
            return False
    
    def start_training(self, dataset_name: str, tune_hyperparameters: bool = False) -> bool:
        """Start model training in background thread."""
        if self._is_training:
            self.set_error("Training already in progress")
            return False
        
        try:
            self.clear_error()
            
            # Create and start worker thread
            self._current_training_thread = TrainingWorkerThread(
                self.orchestrator, dataset_name, self._training_config, tune_hyperparameters
            )
            
            # Connect signals
            self._current_training_thread.training_progress.connect(self._on_training_progress)
            self._current_training_thread.training_completed.connect(self._on_training_completed)
            self._current_training_thread.training_failed.connect(self._on_training_failed)
            
            # Update state
            self._is_training = True
            self._training_progress = 0
            
            # Emit signals
            self.training_started.emit()
            self.training_progress_changed.emit(0)
            
            # Start training
            self._current_training_thread.start()
            
            logger.info(f"Started training: {dataset_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start training: {e}")
            self.set_error(str(e))
            return False
    
    def _on_training_progress(self, progress: int):
        """Handle training progress updates."""
        self._training_progress = progress
        self.training_progress_changed.emit(progress)
    
    def _on_training_completed(self, result: TrainingResult):
        """Handle training completion."""
        self._is_training = False
        self._training_progress = 100
        
        # Update model versions
        self._model_versions.append(result.__dict__)
        self.model_versions_changed.emit()
        
        # Emit completion signal
        self.training_completed.emit(result)
        
        logger.info(f"Training completed: {result.test_accuracy:.3f} accuracy")
    
    def _on_training_failed(self, error_message: str):
        """Handle training failure."""
        self._is_training = False
        self._training_progress = 0
        
        self.set_error(error_message)
        self.training_failed.emit(error_message)
        
        logger.error(f"Training failed: {error_message}")
    
    def stop_training(self):
        """Stop current training operation."""
        if self._current_training_thread and self._current_training_thread.isRunning():
            self._current_training_thread.terminate()
            self._current_training_thread.wait()
            
            self._is_training = False
            self._training_progress = 0
            
            logger.info("Training stopped by user")
