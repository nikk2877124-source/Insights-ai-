"""Utilities for generating dataset profiling statistics.

This service keeps the profiling logic modular so the application can expand
future iterations without rewriting the existing inspection flow.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class ProfilingService:
    """Generate dataset profiling summaries for basic analytics workflows."""

    def analyze_missing_values(self, df: pd.DataFrame) -> dict[str, Any]:
        """Calculate missing value counts and percentages for every column.

        Args:
            df: The dataset to inspect.

        Returns:
            A JSON-serializable dictionary containing the aggregate missing value
            count and a per-column breakdown.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

        total_rows = len(df)
        missing_counts = df.isna().sum()
        total_missing_values = int(missing_counts.sum())

        columns: dict[str, dict[str, Any]] = {}
        for column_name in df.columns:
            count = int(missing_counts.get(column_name, 0))
            percentage = round((count / total_rows) * 100, 1) if total_rows else 0.0
            columns[str(column_name)] = {
                "count": count,
                "percentage": percentage,
            }

        return {
            "total_missing_values": total_missing_values,
            "columns": columns,
        }

    def analyze_duplicates(self, df: pd.DataFrame) -> dict[str, Any]:
        """Count duplicate rows and calculate their percentage.

        Args:
            df: The dataset to inspect.

        Returns:
            A JSON-serializable dictionary with duplicate totals and percentage.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

        total_rows = len(df)
        duplicate_rows = int(df.duplicated().sum())
        duplicate_percentage = round((duplicate_rows / total_rows) * 100, 1) if total_rows else 0.0

        return {
            "duplicate_rows": duplicate_rows,
            "duplicate_percentage": duplicate_percentage,
        }

    def generate_profile(self, df: pd.DataFrame) -> dict[str, Any]:
        """Build a basic profiling payload for a dataset.

        The profile includes the existing basic information plus sections for
        missing values and duplicates. This keeps the output modular and avoids
        adding more analysis logic to the calling layer.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

        return {
            "basic_info": self._build_basic_info(df),
            "missing_values": self.analyze_missing_values(df),
            "duplicates": self.analyze_duplicates(df),
        }

    def _build_basic_info(self, df: pd.DataFrame) -> dict[str, Any]:
        """Create the basic profiling section for the dataset."""
        return {
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "column_names": [str(column) for column in df.columns.tolist()],
            "data_types": {str(column): str(dtype) for column, dtype in df.dtypes.items()},
            "memory_usage": int(df.memory_usage(index=True, deep=True).sum()),
        }
