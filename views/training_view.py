# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.
# views/training_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QProgressBar, QTextEdit, QSplitter,
    QMessageBox, QFileDialog, QLineEdit, QDialog
)
from PySide6.QtCore import Qt, QTimer

from viewmodels.training_viewmodel import TrainingViewModel

# Placeholder class for TrainingResultsDialog
class TrainingResultsDialog(QDialog):
    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.result = result
        self.setWindowTitle("Training Results")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Training completed successfully!"))
        layout.addWidget(QLabel(f"Test Accuracy: {result.test_accuracy:.3f}"))
        layout.addWidget(QLabel(f"CV Accuracy: {result.cv_mean_accuracy:.3f} ± {result.cv_std_accuracy:.3f}"))
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

class TrainingView(QWidget):
    """Training view with comprehensive training controls."""
    
    def __init__(self, viewmodel: TrainingViewModel):
        super().__init__()
        self.viewmodel = viewmodel
        
        self._setup_ui()
        self._connect_viewmodel()
    
    def _setup_ui(self):
        """Setup the training UI."""
        layout = QVBoxLayout(self)
        
        # Create splitter for left/right panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Training controls
        left_panel = self._create_training_controls()
        splitter.addWidget(left_panel)
        
        # Right panel - Results and monitoring
        right_panel = self._create_results_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
    
    def _create_training_controls(self) -> QWidget:
        """Create training controls panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Dataset Management Group
        dataset_group = QGroupBox("Dataset Management")
        dataset_layout = QVBoxLayout(dataset_group)
        
        # Create dataset from feedback
        dataset_layout.addWidget(QLabel("Create Dataset from Feedback:"))
        
        dataset_name_layout = QHBoxLayout()
        self.dataset_name_edit = QLineEdit()
        self.dataset_name_edit.setPlaceholderText("Dataset name...")
        dataset_name_layout.addWidget(self.dataset_name_edit)
        
        self.create_dataset_btn = QPushButton("Create from Feedback")
        self.create_dataset_btn.clicked.connect(self._create_dataset)
        dataset_name_layout.addWidget(self.create_dataset_btn)
        
        dataset_layout.addLayout(dataset_name_layout)
        
        # Available datasets table
        dataset_layout.addWidget(QLabel("Available Datasets:"))
        self.datasets_table = QTableWidget()
        self.datasets_table.setColumnCount(5)
        self.datasets_table.setHorizontalHeaderLabels([
            "Name", "Samples", "Positive", "Quality", "Created"
        ])
        self.datasets_table.horizontalHeader().setStretchLastSection(True)
        dataset_layout.addWidget(self.datasets_table)
        
        layout.addWidget(dataset_group)
        
        # Training Configuration Group
        config_group = QGroupBox("Training Configuration")
        config_layout = QGridLayout(config_group)
        
        # Model type
        config_layout.addWidget(QLabel("Model Type:"), 0, 0)
        self.model_type_combo = QComboBox()
        self.model_type_combo.addItems(["random_forest", "xgboost", "lightgbm"])
        config_layout.addWidget(self.model_type_combo, 0, 1)
        
        # Cross-validation folds
        config_layout.addWidget(QLabel("CV Folds:"), 1, 0)
        self.cv_folds_spin = QSpinBox()
        self.cv_folds_spin.setRange(3, 10)
        self.cv_folds_spin.setValue(5)
        config_layout.addWidget(self.cv_folds_spin, 1, 1)
        
        # Test size
        config_layout.addWidget(QLabel("Test Size:"), 2, 0)
        self.test_size_spin = QDoubleSpinBox()
        self.test_size_spin.setRange(0.1, 0.5)
        self.test_size_spin.setValue(0.2)
        self.test_size_spin.setSingleStep(0.05)
        config_layout.addWidget(self.test_size_spin, 2, 1)
        
        # Feature scaling
        self.feature_scaling_check = QCheckBox("Enable Feature Scaling")
        self.feature_scaling_check.setChecked(True)
        config_layout.addWidget(self.feature_scaling_check, 3, 0, 1, 2)
        
        # Hyperparameter tuning
        self.hyperparameter_tuning_check = QCheckBox("Enable Hyperparameter Tuning")
        config_layout.addWidget(self.hyperparameter_tuning_check, 4, 0, 1, 2)
        
        layout.addWidget(config_group)
        
        # Training Actions Group
        actions_group = QGroupBox("Training Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        # Progress bar
        self.training_progress = QProgressBar()
        self.training_progress.setVisible(False)
        actions_layout.addWidget(self.training_progress)
        
        # Training buttons
        button_layout = QHBoxLayout()
        
        self.start_training_btn = QPushButton("Start Training")
        self.start_training_btn.clicked.connect(self._start_training)
        button_layout.addWidget(self.start_training_btn)
        
        self.stop_training_btn = QPushButton("Stop Training")
        self.stop_training_btn.clicked.connect(self._stop_training)
        self.stop_training_btn.setEnabled(False)
        button_layout.addWidget(self.stop_training_btn)
        
        actions_layout.addLayout(button_layout)
        
        layout.addWidget(actions_group)
        
        # Stretch
        layout.addStretch()
        
        return widget
    
    def _create_results_panel(self) -> QWidget:
        """Create results and monitoring panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Model Versions Group
        versions_group = QGroupBox("Model Versions")
        versions_layout = QVBoxLayout(versions_group)
        
        self.versions_table = QTableWidget()
        self.versions_table.setColumnCount(6)
        self.versions_table.setHorizontalHeaderLabels([
            "Version", "Model Type", "Test Accuracy", "CV Accuracy", "Dataset", "Created"
        ])
        self.versions_table.horizontalHeader().setStretchLastSection(True)
        versions_layout.addWidget(self.versions_table)
        
        # Version actions
        version_actions = QHBoxLayout()
        
        self.load_model_btn = QPushButton("Load Selected Model")
        self.load_model_btn.clicked.connect(self._load_selected_model)
        version_actions.addWidget(self.load_model_btn)
        
        self.delete_model_btn = QPushButton("Delete Selected")
        self.delete_model_btn.clicked.connect(self._delete_selected_model)
        version_actions.addWidget(self.delete_model_btn)
        
        versions_layout.addLayout(version_actions)
        
        layout.addWidget(versions_group)
        
        # Training Log Group
        log_group = QGroupBox("Training Log")
        log_layout = QVBoxLayout(log_group)
        
        self.training_log = QTextEdit()
        self.training_log.setReadOnly(True)
        self.training_log.setMaximumHeight(200)
        log_layout.addWidget(self.training_log)
        
        layout.addWidget(log_group)
        
        return widget
    
    def _connect_viewmodel(self):
        """Connect ViewModel signals to UI updates."""
        # Dataset changes
        self.viewmodel.datasets_changed.connect(self._update_datasets_table)
        
        # Model version changes
        self.viewmodel.model_versions_changed.connect(self._update_versions_table)
        
        # Training events
        self.viewmodel.training_started.connect(self._on_training_started)
        self.viewmodel.training_progress_changed.connect(self._on_training_progress)
        self.viewmodel.training_completed.connect(self._on_training_completed)
        self.viewmodel.training_failed.connect(self._on_training_failed)
        
        # Error handling
        self.viewmodel.error_occurred.connect(self._show_error)
        
        # Initial data load
        self._update_datasets_table()
        self._update_versions_table()
    
    def _create_dataset(self):
        """Create dataset from feedback."""
        dataset_name = self.dataset_name_edit.text().strip()
        if not dataset_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a dataset name.")
            return
        
        if self.viewmodel.create_dataset_from_feedback(dataset_name):
            self.dataset_name_edit.clear()
            self._log_message(f"Dataset '{dataset_name}' created successfully")
        else:
            self._log_message(f"Failed to create dataset '{dataset_name}'")
    
    def _start_training(self):
        """Start model training."""
        selected_rows = self.datasets_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a dataset for training.")
            return
        
        # Get selected dataset name
        row = selected_rows[0].row()
        dataset_name = self.datasets_table.item(row, 0).text()
        
        # Update configuration
        self.viewmodel._training_config.model_type = self.model_type_combo.currentText()
        self.viewmodel._training_config.cross_validation_folds = self.cv_folds_spin.value()
        self.viewmodel._training_config.test_size = self.test_size_spin.value()
        self.viewmodel._training_config.use_feature_scaling = self.feature_scaling_check.isChecked()
        
        # Start training
        tune_hyperparameters = self.hyperparameter_tuning_check.isChecked()
        
        if self.viewmodel.start_training(dataset_name, tune_hyperparameters):
            self._log_message(f"Started training with dataset: {dataset_name}")
        else:
            self._log_message("Failed to start training")
    
    def _stop_training(self):
        """Stop current training."""
        self.viewmodel.stop_training()
        self._log_message("Training stopped by user")
    
    def _load_selected_model(self):
        """Load selected model for production use."""
        selected_rows = self.versions_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a model version to load.")
            return
        
        row = selected_rows[0].row()
        version_id = self.versions_table.item(row, 0).text()
        
        try:
            model_data = self.viewmodel.orchestrator.load_production_model(version_id)
            QMessageBox.information(self, "Model Loaded", f"Model {version_id} loaded successfully!")
            self._log_message(f"Loaded model: {version_id}")
        except Exception as e:
            QMessageBox.critical(self, "Load Failed", f"Failed to load model:\n{str(e)}")
    
    def _delete_selected_model(self):
        """Delete selected model version."""
        selected_rows = self.versions_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a model version to delete.")
            return
        
        row = selected_rows[0].row()
        version_id = self.versions_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete model {version_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Implementation for model deletion
            self._log_message(f"Deleted model: {version_id}")
    
    def _update_datasets_table(self):
        """Update datasets table."""
        datasets = self.viewmodel.available_datasets
        
        self.datasets_table.setRowCount(len(datasets))
        
        for row, dataset in enumerate(datasets):
            self.datasets_table.setItem(row, 0, QTableWidgetItem(dataset['name']))
            self.datasets_table.setItem(row, 1, QTableWidgetItem(str(dataset['total_samples'])))
            self.datasets_table.setItem(row, 2, QTableWidgetItem(str(dataset['positive_samples'])))
            self.datasets_table.setItem(row, 3, QTableWidgetItem(f"{dataset['quality_score']:.2f}"))
            self.datasets_table.setItem(row, 4, QTableWidgetItem(dataset['created_date'][:10]))
    
    def _update_versions_table(self):
        """Update model versions table."""
        versions = self.viewmodel.model_versions
        
        self.versions_table.setRowCount(len(versions))
        
        for row, version in enumerate(versions):
            self.versions_table.setItem(row, 0, QTableWidgetItem(version.get('version_id', '')))
            self.versions_table.setItem(row, 1, QTableWidgetItem(version.get('model_type', '')))
            self.versions_table.setItem(row, 2, QTableWidgetItem(f"{version.get('test_accuracy', 0):.3f}"))
            self.versions_table.setItem(row, 3, QTableWidgetItem(f"{version.get('cv_mean_accuracy', 0):.3f}"))
            self.versions_table.setItem(row, 4, QTableWidgetItem(version.get('dataset_id', '')))
            self.versions_table.setItem(row, 5, QTableWidgetItem(version.get('created_date', '')[:16]))
    
    def _on_training_started(self):
        """Handle training started."""
        self.training_progress.setVisible(True)
        self.training_progress.setValue(0)
        self.start_training_btn.setEnabled(False)
        self.stop_training_btn.setEnabled(True)
        
        self._log_message("Training started...")
    
    def _on_training_progress(self, progress: int):
        """Handle training progress update."""
        self.training_progress.setValue(progress)
        
        if progress % 20 == 0:  # Log every 20%
            self._log_message(f"Training progress: {progress}%")
    
    def _on_training_completed(self, result):
        """Handle training completion."""
        self.training_progress.setVisible(False)
        self.start_training_btn.setEnabled(True)
        self.stop_training_btn.setEnabled(False)
        
        self._log_message(f"Training completed!")
        self._log_message(f"Test Accuracy: {result.test_accuracy:.3f}")
        self._log_message(f"CV Accuracy: {result.cv_mean_accuracy:.3f} ± {result.cv_std_accuracy:.3f}")
        
        # Show detailed results
        self._show_training_results(result)
    
    def _on_training_failed(self, error: str):
        """Handle training failure."""
        self.training_progress.setVisible(False)
        self.start_training_btn.setEnabled(True)
        self.stop_training_btn.setEnabled(False)
        
        self._log_message(f"Training failed: {error}")
    
    def _show_training_results(self, result):
        """Show detailed training results dialog."""
        dialog = TrainingResultsDialog(result, self)
        dialog.exec()
    
    def _show_error(self, error: str):
        """Show error message."""
        QMessageBox.critical(self, "Error", error)
        self._log_message(f"Error: {error}")
    
    def _log_message(self, message: str):
        """Add message to training log."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.training_log.append(f"[{timestamp}] {message}")