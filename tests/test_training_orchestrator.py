import sys
import types
import numpy as np
from unittest.mock import MagicMock, patch

# Stub minimal sklearn modules required for import
sklearn = types.ModuleType("sklearn")
model_selection = types.ModuleType("sklearn.model_selection")
metrics = types.ModuleType("sklearn.metrics")
preprocessing = types.ModuleType("sklearn.preprocessing")
ensemble = types.ModuleType("sklearn.ensemble")

class RandomForestClassifier:
    pass

ensemble.RandomForestClassifier = RandomForestClassifier


def train_test_split(X, y, test_size=0.25, random_state=None, stratify=None):
    split = int(len(X) * (1 - test_size))
    return X[:split], X[split:], y[:split], y[split:]


def cross_val_score(model, X, y, cv=None, scoring=None):
    return np.array([1.0])


class StratifiedKFold:
    def __init__(self, n_splits=5, shuffle=True, random_state=None):
        pass


class GridSearchCV:
    pass


class RandomizedSearchCV:
    pass


def classification_report(y_true, y_pred, output_dict=True):
    return {"accuracy": 1.0, "1": {"precision": 1.0, "recall": 1.0, "f1-score": 1.0}}


def confusion_matrix(y_true, y_pred):
    return np.array([[1]])


class StandardScaler:
    def fit_transform(self, X):
        return X


model_selection.train_test_split = train_test_split
model_selection.cross_val_score = cross_val_score
model_selection.StratifiedKFold = StratifiedKFold
model_selection.GridSearchCV = GridSearchCV
model_selection.RandomizedSearchCV = RandomizedSearchCV
metrics.classification_report = classification_report
metrics.confusion_matrix = confusion_matrix
preprocessing.StandardScaler = StandardScaler
sklearn.model_selection = model_selection
sklearn.metrics = metrics
sklearn.preprocessing = preprocessing
sklearn.ensemble = ensemble
sys.modules.setdefault("sklearn", sklearn)
sys.modules.setdefault("sklearn.model_selection", model_selection)
sys.modules.setdefault("sklearn.metrics", metrics)
sys.modules.setdefault("sklearn.preprocessing", preprocessing)
sys.modules.setdefault("sklearn.ensemble", ensemble)
sys.modules.setdefault("joblib", types.ModuleType("joblib"))

from models.ml.training.training_orchestrator import TrainingOrchestrator
from models.ml.training.data_models import TrainingDataset


def test_train_model_from_feedback_uses_config_create_model():
    orchestrator = TrainingOrchestrator()

    orchestrator.self_learning_manager = MagicMock()
    orchestrator.self_learning_manager.get_training_data_from_feedback.return_value = ["data"]
    orchestrator.dataset_builder = MagicMock()
    dataset = TrainingDataset(dataset_id="d1", name="ds", description="", feature_columns=["f1"], total_samples=5)
    orchestrator.dataset_builder.build_from_feedback.return_value = (dataset, [[1],[2],[3],[4],[5]], [0,1,0,1,0])

    orchestrator.cross_validator = MagicMock()
    orchestrator.cross_validator.perform_cross_validation.return_value = {"mean_accuracy":0.9, "std_accuracy":0.1}
    orchestrator.cross_validator.evaluate_model.return_value = {
        "accuracy":0.8,
        "feature_importance":[0.5],
        "classification_report":{"accuracy":0.8, "1":{"precision":0.8, "recall":0.8, "f1-score":0.8}},
        "confusion_matrix":[[1]]
    }

    orchestrator._save_trained_model = MagicMock()
    orchestrator._save_model_versions = MagicMock()

    config = MagicMock()
    model = MagicMock()
    model.fit.return_value = None
    model.score.return_value = 0.9
    config.create_model.return_value = model
    config.use_feature_scaling = False
    config.test_size = 0.2
    config.cross_validation_folds = 5
    config.model_type = "mock"

    with patch("models.ml.training.training_orchestrator.StandardScaler") as scaler_cls:
        orchestrator.train_model_from_feedback("ds", config)
        config.create_model.assert_called_once()
        scaler_cls.assert_not_calle