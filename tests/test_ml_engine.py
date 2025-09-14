import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root on path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from conftest import stub_training_modules

stub_training_modules()

from models.ml_engine import MLEngine
from models.data_models import (
    BankTransaction,
    ERPTransaction,
    TransactionMatch,
    MatchStatus,
)


@pytest.fixture
def make_bank_transaction():
    """Factory for lightweight BankTransaction objects."""
    def _make(id: str, amount: float, days: int = 0, desc: str = "Payment") -> BankTransaction:
        date = datetime(2023, 1, 1) + timedelta(days=days)
        return BankTransaction(id=id, date=date, description=desc, amount=amount)
    return _make


@pytest.fixture
def make_erp_transaction():
    """Factory for lightweight ERPTransaction objects."""
    def _make(id: str, amount: float, days: int = 0, desc: str = "Payment") -> ERPTransaction:
        date = datetime(2023, 1, 1) + timedelta(days=days)
        return ERPTransaction(id=id, date=date, description=desc, amount=amount)
    return _make

def test_generate_matches_filters_duplicates(make_bank_transaction, make_erp_transaction):
    engine = MLEngine(model_path="dummy.pkl")
    bank = [make_bank_transaction("b1", 100)]
    erp = [make_erp_transaction("e1", 100), make_erp_transaction("e2", 110)]

    matches = engine.generate_matches(bank, erp, confidence_threshold=0.0)

    assert len(matches) == 1
    assert matches[0].erp_transaction.id == "e1"


def _make_match(bank: BankTransaction, erp: ERPTransaction, status: MatchStatus) -> TransactionMatch:
    return TransactionMatch(
        bank_transaction=bank,
        erp_transaction=erp,
        confidence_score=1.0,
        amount_score=1.0,
        date_score=1.0,
        description_score=1.0,
        status=status,
    )


def test_train_model_requires_minimum_samples(make_bank_transaction, make_erp_transaction):
    engine = MLEngine(model_path="dummy.pkl")
    matches = [
        _make_match(
            make_bank_transaction(f"b{i}", 100 + i),
            make_erp_transaction(f"e{i}", 100 + i),
            MatchStatus.MATCHED,
        )
        for i in range(4)
    ]

    with patch.object(engine, "save_model") as mock_save:
        engine.train_model(matches)
        assert engine.model is None
        mock_save.assert_not_called()


def test_train_model_trains_and_saves(make_bank_transaction, make_erp_transaction):
    engine = MLEngine(model_path="dummy.pkl")
    matches = [
        _make_match(
            make_bank_transaction(f"b{i}", 100 + i),
            make_erp_transaction(f"e{i}", 100 + i),
            MatchStatus.MATCHED if i % 2 == 0 else MatchStatus.REJECTED,
        )
        for i in range(5)
    ]

    with patch.object(engine, "save_model") as mock_save:
        engine.train_model(matches)
        assert engine.model is not None
        mock_save.assert_called_once()


def test_save_model_uses_model_path():
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
