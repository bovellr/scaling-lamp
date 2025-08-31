import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import types

import pytest

# Ensure project root on path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Stub heavy training module to avoid optional dependencies during import
trainer_stub = types.ModuleType("models.ml.training.trainer")
class ModelTrainingConfig:  # pragma: no cover - simple placeholder
    pass
class TrainingDataset:  # pragma: no cover - simple placeholder
    pass
class TrainingService:  # pragma: no cover - simple placeholder
    pass
trainer_stub.ModelTrainingConfig = ModelTrainingConfig
trainer_stub.TrainingDataset = TrainingDataset
trainer_stub.TrainingService = TrainingService
sys.modules.setdefault("models.ml.training.trainer", trainer_stub)

from models.ml_engine import MLEngine
from models.data_models import Transaction, TransactionMatch, MatchStatus


@pytest.fixture
def make_transaction():
    """Factory for lightweight Transaction objects."""
    def _make(id: str, amount: float, days: int = 0, desc: str = "Payment") -> Transaction:
        date = datetime(2023, 1, 1) + timedelta(days=days)
        return Transaction(id=id, date=date, description=desc, amount=amount)
    return _make


def test_generate_matches_filters_duplicates(make_transaction):
    engine = MLEngine(model_path="dummy.pkl")
    bank = [make_transaction("b1", 100)]
    erp = [make_transaction("e1", 100), make_transaction("e2", 110)]

    matches = engine.generate_matches(bank, erp, confidence_threshold=0.0)

    assert len(matches) == 1
    assert matches[0].erp_transaction.id == "e1"


def _make_match(bank: Transaction, erp: Transaction, status: MatchStatus) -> TransactionMatch:
    return TransactionMatch(
        bank_transaction=bank,
        erp_transaction=erp,
        confidence_score=1.0,
        amount_score=1.0,
        date_score=1.0,
        description_score=1.0,
        status=status,
    )


def test_train_model_requires_minimum_samples(make_transaction):
    engine = MLEngine(model_path="dummy.pkl")
    matches = [
        _make_match(make_transaction(f"b{i}", 100 + i), make_transaction(f"e{i}", 100 + i), MatchStatus.MATCHED)
        for i in range(4)
    ]

    with patch.object(engine, "save_model") as mock_save:
        engine.train_model(matches)
        assert engine.model is None
        mock_save.assert_not_called()


def test_train_model_trains_and_saves(make_transaction):
    engine = MLEngine(model_path="dummy.pkl")
    matches = [
        _make_match(
            make_transaction(f"b{i}", 100 + i),
            make_transaction(f"e{i}", 100 + i),
            MatchStatus.MATCHED if i % 2 == 0 else MatchStatus.REJECTED,
        )
        for i in range(5)
    ]

    with patch.object(engine, "save_model") as mock_save:
        engine.train_model(matches)
        assert engine.model is not None
        mock_save.assert_called_once()


def test_save_model_uses_model_path(make_transaction):
    engine = MLEngine(model_path="some/model.pkl")
    engine.model = MagicMock()

    with patch("models.ml_engine.joblib.dump") as mock_dump, patch("pathlib.Path.mkdir") as mock_mkdir:
        engine.save_model()
        mock_mkdir.assert_called_once()
        mock_dump.assert_called_once()
        assert mock_dump.call_args[0][1] == engine.model_path


def test_load_model_reads_from_model_path():
    with patch("pathlib.Path.exists", return_value=False):
        engine = MLEngine(model_path="some/model.pkl")

    with patch("pathlib.Path.exists", return_value=True), patch("models.ml_engine.joblib.load", return_value="model") as mock_load:
        engine.load_model()
        mock_load.assert_called_once_with(engine.model_path)
        assert engine.model == "model"
