import pytest
from pathlib import Path

pytest.importorskip("PySide6", reason="PySide6 is required for these tests")
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from views.main_window import MainWindow
from models.data_models import TransactionMatch, Transaction


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def create_sample_files(tmp_path: Path):
    bank_file = tmp_path / "bank.csv"
    bank_file.write_text(
        "Posting Date,Type,Details,Debit,Credit\n"
        "11/04/2025,DD,Payment A,200,\n"
        "12/04/2025,CR,Payment B,,100\n"
    )
    ledger_file = tmp_path / "ledger.csv"
    ledger_file.write_text(
        "Date,Description,Amount,AccountCode\n"
        # Ledger uses the same sign convention: debits positive, credits negative
        "11/04/2025,Payment A,200,1001\n"
        "12/04/2025,Payment B,-100,1001\n"
    )
    return bank_file, ledger_file


@pytest.fixture
def window_with_data(app, tmp_path, monkeypatch):
    bank_file, ledger_file = create_sample_files(tmp_path)
    win = MainWindow()
    win.current_bank_account = "Main Current Account"
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", lambda *a, **k: (str(bank_file), "")
    )
    win.import_bank_statement()
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", lambda *a, **k: (str(ledger_file), "")
    )
    win.import_ledger_data()
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    return win


def test_import_and_reconcile(window_with_data, monkeypatch):
    win = window_with_data
    assert not win.bank_data.empty
    assert not win.ledger_data.empty
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    win.run_reconciliation()
    assert win.reconciliation_results is not None
    assert len(win.reconciliation_results) == 2


def test_training_and_review(window_with_data, monkeypatch):
    win = window_with_data
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    win.run_reconciliation()
    for match in win.reconciliation_results:
        win.matching_viewmodel.confirm_match(match)
    win.train_ai_model()
    win.reconciliation_results[0].confidence_score = 0.1
    captured = {}
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: captured.update(text=a[2]))
    win.review_low_confidence()
    assert "requires review" in captured["text"]