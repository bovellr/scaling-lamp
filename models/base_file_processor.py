# SPDX-License-Identifier: LicenseRef-Proprietary
# Copyright (c) 2025 Arvida Software UK. All rights reserved.

"""Shared utilities for reading files and detecting header rows."""

from pathlib import Path
from typing import List, Optional, Union

import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BaseFileProcessor:
    """Provides common file reading and header detection helpers."""

    def read_file(self, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """Read a file with automatic format detection."""
        file_path = Path(file_path)

        try:
            if file_path.suffix.lower() == ".csv":
                return self._read_csv(file_path, **kwargs)
            if file_path.suffix.lower() in [".xlsx", ".xls"]:
                return self._read_excel(file_path, **kwargs)
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        except Exception as exc:  # pragma: no cover - logging side effect
            logger.error("Failed to read file %s: %s", file_path, exc)
            raise

    def _read_csv(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Read CSV file with encoding detection."""
        encoding = kwargs.pop("encoding", "utf-8")
        kwargs.setdefault("header", None)
        try:
            return pd.read_csv(file_path, encoding=encoding, **kwargs)
        except UnicodeDecodeError:
            for fallback in ["latin-1", "cp1252", "iso-8859-1"]:
                try:
                    return pd.read_csv(file_path, encoding=fallback, **kwargs)
                except UnicodeDecodeError:
                    continue
            raise

    def _read_excel(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Read Excel file using appropriate engine."""
        engine = "openpyxl" if file_path.suffix == ".xlsx" else "xlrd"
        kwargs.setdefault("header", None)
        try:
            return pd.read_excel(file_path, engine=engine, **kwargs)
        except ImportError as exc:  # pragma: no cover - logging side effect
            logger.error(
                "Required Excel engine '%s' is not installed for reading '%s': %s",
                engine,
                file_path,
                exc,
            )
            raise

    def find_header_row(
        self, df: pd.DataFrame, keywords: Optional[List[str]] = None
    ) -> Optional[int]:
        """Find header row either by keywords or by heuristics."""
        if keywords:
            for idx in range(min(10, len(df))):
                row_values = [
                    str(val).lower().strip() if pd.notna(val) else ""
                    for val in df.iloc[idx]
                ]
                matches = sum(
                    1 for keyword in keywords if any(keyword.lower() in val for val in row_values)
                )
                if matches >= 2:
                    return idx
            return None

        best_row: Optional[int] = None
        max_text = 0
        for idx, row in df.iterrows():
            text_count = 0
            non_null = 0
            for val in row:
                if pd.notna(val):
                    non_null += 1
                    if isinstance(val, str) and len(val.strip()) > 2:
                        text_count += 1
            if text_count >= 3 and text_count >= non_null * 0.6:
                if text_count > max_text:
                    max_text = text_count
                    best_row = idx
        return best_row