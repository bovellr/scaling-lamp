import pandas as pd
import pytest
from unittest.mock import MagicMock

from models.file_processor import FileProcessor
from models.data_models import BankTemplate


def make_file_processor():
    """Helper to create FileProcessor with mocked templates manager."""
    templates_manager = MagicMock()
    return FileProcessor(templates_manager)


def test_read_file_csv(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("a,b,c\n1,2,3\n")

    fp = make_file_processor()
    df = fp.read_file(csv_path)

    assert df.shape == (2, 3)
    assert list(df.iloc[0]) == ["a", "b", "c"]
    assert df.iloc[1, 2] == "3"


def test_read_file_excel(tmp_path):
    df_original = pd.DataFrame([["x", "y"], ["1", "2"]])
    xlsx_path = tmp_path / "sample.xlsx"
    df_original.to_excel(xlsx_path, index=False, header=False)

    fp = make_file_processor()
    df = fp.read_file(xlsx_path)

    assert df.shape == (2, 2)
    assert df.iloc[1, 1] == "2"


def test_read_file_unsupported(tmp_path):
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text("data")

    fp = make_file_processor()
    with pytest.raises(ValueError):
        fp.read_file(txt_path)


def test_transform_statement_header_failure():
    df = pd.DataFrame([["foo", "bar"], ["1", "2"]])
    template = BankTemplate(
        name="TestBank",
        bank_type="custom",
        header_keywords=["date", "amount"],
        date_patterns=[r"\d{2}/\d{2}/\d{4}"],
        skip_keywords=[],
        column_mapping={},
    )

    fp = make_file_processor()
    statement, info = fp.transform_statement(df, template)

    assert not info["success"]
    assert "Could not find header row" in info["message"]
    assert statement.transactions == []


def test_parse_amount_malformed():
    fp = make_file_processor()
    assert fp._parse_amount("notanumber") == 0.0
    assert fp._parse_amount("") == 0.0


def test_find_header_row_with_keywords():
    df = pd.DataFrame([
        ["foo", "bar"],
        ["Date", "Amount"],
        ["1/1/2024", "100"],
    ])
    fp = make_file_processor()
    assert fp.find_header_row(df, ["date", "amount"]) == 1
