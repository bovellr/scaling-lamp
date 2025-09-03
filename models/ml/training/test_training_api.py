from dataclasses import is_dataclass

from conftest import stub_training_modules

# Provide lightweight stubs so the training package can be imported
stub_training_modules()

from models.ml.training import (
    TrainingDataSource,
    TrainingDataset,
    ModelTrainingConfig,
    TrainingResult,
)


def test_public_api_exposes_model_training_config():
    assert is_dataclass(ModelTrainingConfig)
    config = ModelTrainingConfig(model_type="random_forest")
    assert config.model_type == "random_forest"


def test_public_api_exports_all_data_models():
    # Simply ensure the symbols are available from the package
    for cls in (TrainingDataSource, TrainingDataset, TrainingResult):
        assert hasattr(cls, "__module__")