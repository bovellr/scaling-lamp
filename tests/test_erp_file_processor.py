import pandas as pd

from models.erp_file_processor import ERPFileProcessor


def test_excel_metadata_includes_sheet_and_header_and_returns_df(tmp_path):
    df = pd.DataFrame({
        "Date": ["2024-01-01"],
        "Description": ["Test"],
        "Amount": [100],
        "Reference": ["ABC"],
    })
    file_path = tmp_path / "input.xlsx"
    df.to_excel(file_path, index=False)

    processor = ERPFileProcessor()
    result = processor.analyze_and_process_file(str(file_path))

    assert result["success"] is True
    analysis = result["analysis"]
    metadata = analysis["metadata"]
    assert metadata["sheet_name"] == analysis["sheet_name"]
    assert metadata["header_row"] == analysis["header_row"]

    processed_df = result["data"]
    assert isinstance(processed_df, pd.DataFrame)
    assert processed_df.iloc[0]["Amount"] == 100