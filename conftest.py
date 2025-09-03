"""Test configuration utilities."""

import sys
import types


def stub_training_modules() -> None:
    """Insert lightweight stubs for heavy training submodules.

    The real implementations pull in optional dependencies like NumPy and
    scikit-learn which aren't required for the lightweight unit tests. By
    providing simple stand-ins we can import ``models.ml.training`` and modules
    depending on it without installing those packages.
    """

    # Core training service stub (used by MLEngine tests)
    trainer_stub = types.ModuleType("models.ml.training.trainer")

    class ModelTrainingConfig:  # pragma: no cover - lightweight placeholder
        pass

    class TrainingDataset:  # pragma: no cover - lightweight placeholder
        pass

    class TrainingService:  # pragma: no cover - lightweight placeholder
        pass

    trainer_stub.ModelTrainingConfig = ModelTrainingConfig
    trainer_stub.TrainingDataset = TrainingDataset
    trainer_stub.TrainingService = TrainingService
    sys.modules.setdefault("models.ml.training.trainer", trainer_stub)

    # Stub modules referenced by the training package's __init__
    modules = {
        "models.ml.training.data_processor": ("FeatureExtractor", "DataQualityAnalyzer", "DatasetBuilder"),
        "models.ml.training.model_factory": ("ModelFactory",),
        "models.ml.training.cross_validator": ("CrossValidator",),
        "models.ml.training.hyperparameter_tuner": ("HyperparameterTuner",),
        "models.ml.training.self_learning": ("SelfLearningManager",),
        "models.ml.training.training_orchestrator": ("TrainingOrchestrator",),
    }

    for name, attrs in modules.items():
        module = types.ModuleType(name)
        for attr in attrs:
            setattr(module, attr, type(attr, (), {}))
        sys.modules.setdefault(name, module)