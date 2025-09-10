import pytest
from datetime import datetime

pytest.importorskip("PySide6", reason="PySide6 is required for these tests")

from views.main_window import MainWindow
from models.data_models import TransactionData, TransactionMatch, BankTransaction, ERPTransaction


def test_unmatched_handles_duplicates():
    mw = MainWindow.__new__(MainWindow)

    bank_transactions = [
        TransactionData(date="2024-01-01", description="Payment", amount=100.0, transaction_id="b1"),
        TransactionData(date="2024-01-01", description="Payment", amount=100.0, transaction_id="b2"),
    ]
    erp_transactions = [
        TransactionData(date="2024-01-01", description="Payment", amount=100.0, transaction_id="e1"),
        TransactionData(date="2024-01-01", description="Payment", amount=100.0, transaction_id="e2"),
    ]

    match = TransactionMatch(
        bank_transaction=BankTransaction(id="b1", date=datetime(2024, 1, 1), description="Payment", amount=100.0),
        erp_transaction=ERPTransaction(id="e1", date=datetime(2024, 1, 1), description="Payment", amount=100.0),
        confidence_score=1.0,
        amount_score=1.0,
        date_score=1.0,
        description_score=1.0,
    )

    unmatched_bank = mw._calculate_unmatched_bank(bank_transactions, [match])
    unmatched_erp = mw._calculate_unmatched_erp(erp_transactions, [match])

    assert [t.transaction_id for t in unmatched_bank] == ["b2"]
    assert [t.transaction_id for t in unmatched_erp] == ["e2"]