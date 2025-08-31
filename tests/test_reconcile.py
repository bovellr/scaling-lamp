import pytest

reconcile_mod = pytest.importorskip(
    "services.reconciliation", reason="reconciliation service not available"
)
TransactionRecord = reconcile_mod.TransactionRecord
reconcile_transactions = reconcile_mod.reconcile_transactions

def test_description_date_boosts_score():
    bank = TransactionRecord(date="2024-05-10", description="Payment", amount=100.0)
    gl_with_desc_date = TransactionRecord(
        date="2024-05-12", description="Payment 09/05/2024", amount=100.0
    )
    gl_without_desc = TransactionRecord(
        date="2024-05-12", description="Payment", amount=100.0
    )

    matches = reconcile_transactions([bank], [gl_with_desc_date, gl_without_desc])

    assert len(matches) == 1
    match = matches[0]
    assert match.gl_transaction == gl_with_desc_date
    assert match.confidence > 0.8


def test_no_match_without_description_date():
    bank = TransactionRecord(date="2024-05-10", description="Payment", amount=100.0)
    gl = TransactionRecord(date="2024-05-12", description="Payment", amount=100.0)

    matches = reconcile_transactions([bank], [gl])
    assert matches == []