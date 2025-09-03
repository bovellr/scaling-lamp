from models.ml.feature_utils import compute_transaction_features


def test_compute_transaction_features_basic():
    features = compute_transaction_features(
        100.0,
        "2024-01-01",
        "Payment",
        110.0,
        "2024-01-05",
        "Payment",
    )
    assert features["amount_diff"] == 10.0
    assert features["date_diff"] == 4
    assert 0 <= features["description_similarity"] <= 100
    assert features["signed_amount_match"] == 1
    assert features["same_day"] == 0