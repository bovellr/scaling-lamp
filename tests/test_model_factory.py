from unittest.mock import MagicMock
import importlib.util
from pathlib import Path
import sys
import types


def _load_training_module(relative_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, Path(relative_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module


# Stub package hierarchy to avoid executing package __init__ files
sys.modules.setdefault("models", types.ModuleType("models"))
sys.modules.setdefault("models.ml", types.ModuleType("models.ml"))
sys.modules.setdefault("models.ml.training", types.ModuleType("models.ml.training"))

# Load actual modules under the stubs
data_models = _load_training_module("models/ml/training/data_models.py", "models.ml.training.data_models")
model_factory = _load_training_module("models/ml/training/model_factory.py", "models.ml.training.model_factory")

ModelTrainingConfig = data_models.ModelTrainingConfig
ModelFactory = model_factory.ModelFactory


def test_create_model_delegates_to_config():
    config = ModelTrainingConfig()
    config.create_model = MagicMock(return_value="model")

    result = ModelFactory.create_model(config)

    config.create_model.assert_called_once_with()
    assert result == "model"


def test_create_scaler_delegates_to_config():
    config = ModelTrainingConfig()
    config.create_scaler = MagicMock(return_value="scaler")

    result = ModelFactory.create_scaler(config)

    config.create_scaler.assert_called_once_with()
    assert result == "scaler"
