"""Dataset cleaning service.

This module contains reusable, dataframe-focused cleaning transformations.

Design goals:
- Accept a pandas DataFrame as input.
- Never modify the original DataFrame in-place (always operate on a copy).
- Return the cleaned DataFrame plus JSON-serializable metadata describing what
  changed (rows removed, values filled, etc.).
- Validate column existence and handle empty DataFrames safely.

No FastAPI routing, database access, or persistence logic belongs here.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class CleaningService:
    """A collection of independent dataframe cleaning utilities."""

    def remove_duplicates(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Remove fully-duplicate rows.

        Args:
            df: Input dataframe.

        Returns:
            (cleaned_df, metadata)

        Metadata:
            - rows_before: Total input rows
            - rows_after: Rows after duplicate removal
            - duplicates_removed: Count of rows removed as duplicates
        """
        self._validate_dataframe(df)

        rows_before = int(len(df))
        if df.empty:
            # Return a copy to preserve "no in-place mutation" guarantee.
            return df.copy(deep=True), {
                "rows_before": 0,
                "rows_after": 0,
                "duplicates_removed": 0,
            }

        cleaned = df.copy(deep=True)
        cleaned_no_dupes = cleaned.drop_duplicates()

        rows_after = int(len(cleaned_no_dupes))
        duplicates_removed = max(0, rows_before - rows_after)

        return cleaned_no_dupes, {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "duplicates_removed": duplicates_removed,
        }

    def fill_missing_mean(
        self, df: pd.DataFrame, column_name: str
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Fill missing values in a numeric column using the column mean.

        Args:
            df: Input dataframe.
            column_name: Column to operate on.

        Returns:
            (cleaned_df, metadata)

        Raises:
            KeyError: If the column does not exist.
            ValueError: If the column cannot be mean-filled (non-numeric or empty
                after dropping NaNs).

        Metadata:
            - column: Target column
            - missing_before: Number of NaN/NA values before filling
            - missing_filled: Number of values filled (should equal missing_before
              unless mean is undefined)
            - mean_used: The computed mean used to fill (or None if not available)
        """
        self._validate_dataframe(df)
        self._validate_column_exists(df, column_name)

        cleaned = df.copy(deep=True)
        if cleaned.empty:
            return cleaned, {
                "column": column_name,
                "missing_before": 0,
                "missing_filled": 0,
                "mean_used": None,
            }

        series = cleaned[column_name]
        missing_before = int(series.isna().sum())

        if missing_before == 0:
            return cleaned, {
                "column": column_name,
                "missing_before": 0,
                "missing_filled": 0,
                "mean_used": None,
            }

        # Coerce to numeric to support numeric strings; invalid values become NaN.
        numeric_series = pd.to_numeric(series, errors="coerce")
        mean_used = numeric_series.dropna().mean()

        if pd.isna(mean_used):
            raise ValueError(
                f"Cannot compute mean for column '{column_name}' (no numeric non-missing values)."
            )

        cleaned[column_name] = series.fillna(mean_used)

        missing_after = int(cleaned[column_name].isna().sum())
        missing_filled = max(0, missing_before - missing_after)

        return cleaned, {
            "column": column_name,
            "missing_before": missing_before,
            "missing_filled": missing_filled,
            "mean_used": float(mean_used) if not isinstance(mean_used, float) else mean_used,
        }

    def fill_missing_median(
        self, df: pd.DataFrame, column_name: str
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Fill missing values in a numeric column using the column median.

        Args:
            df: Input dataframe.
            column_name: Column to operate on.

        Returns:
            (cleaned_df, metadata)

        Raises:
            KeyError: If the column does not exist.
            ValueError: If the column cannot be median-filled (non-numeric or empty
                after dropping NaNs).

        Metadata:
            - column: Target column
            - missing_before: Number of NaN/NA values before filling
            - missing_filled: Number of values filled
            - median_used: The computed median used to fill
        """
        self._validate_dataframe(df)
        self._validate_column_exists(df, column_name)

        cleaned = df.copy(deep=True)
        if cleaned.empty:
            return cleaned, {
                "column": column_name,
                "missing_before": 0,
                "missing_filled": 0,
                "median_used": None,
            }

        series = cleaned[column_name]
        missing_before = int(series.isna().sum())

        if missing_before == 0:
            return cleaned, {
                "column": column_name,
                "missing_before": 0,
                "missing_filled": 0,
                "median_used": None,
            }

        numeric_series = pd.to_numeric(series, errors="coerce")
        median_used = numeric_series.dropna().median()

        if pd.isna(median_used):
            raise ValueError(
                f"Cannot compute median for column '{column_name}' (no numeric non-missing values)."
            )

        cleaned[column_name] = series.fillna(median_used)

        missing_after = int(cleaned[column_name].isna().sum())
        missing_filled = max(0, missing_before - missing_after)

        return cleaned, {
            "column": column_name,
            "missing_before": missing_before,
            "missing_filled": missing_filled,
            "median_used": float(median_used) if not isinstance(median_used, float) else median_used,
        }

    def fill_missing_mode(
        self, df: pd.DataFrame, column_name: str
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Fill missing values in a column using the mode.

        Mode is computed from non-missing values. If multiple modes exist, pandas
        returns the first one by default.

        Args:
            df: Input dataframe.
            column_name: Column to operate on.

        Returns:
            (cleaned_df, metadata)

        Raises:
            KeyError: If the column does not exist.
            ValueError: If the column cannot be mode-filled (all values missing).

        Metadata:
            - column: Target column
            - missing_before: Number of NaN/NA values before filling
            - missing_filled: Number of values filled
            - mode_used: The selected mode value
            - mode_count: Frequency of the selected mode in non-missing values
        """
        self._validate_dataframe(df)
        self._validate_column_exists(df, column_name)

        cleaned = df.copy(deep=True)
        if cleaned.empty:
            return cleaned, {
                "column": column_name,
                "missing_before": 0,
                "missing_filled": 0,
                "mode_used": None,
                "mode_count": 0,
            }

        series = cleaned[column_name]
        missing_before = int(series.isna().sum())

        if missing_before == 0:
            return cleaned, {
                "column": column_name,
                "missing_before": 0,
                "missing_filled": 0,
                "mode_used": None,
                "mode_count": 0,
            }

        non_missing = series.dropna()
        if non_missing.empty:
            raise ValueError(
                f"Cannot compute mode for column '{column_name}' because all values are missing."
            )

        modes = non_missing.mode(dropna=True)
        if modes.empty:
            raise ValueError(
                f"Cannot compute mode for column '{column_name}' (mode computation returned no values)."
            )

        mode_used = modes.iloc[0]
        mode_count = int((non_missing == mode_used).sum())

        cleaned[column_name] = series.fillna(mode_used)

        missing_after = int(cleaned[column_name].isna().sum())
        missing_filled = max(0, missing_before - missing_after)

        return cleaned, {
            "column": column_name,
            "missing_before": missing_before,
            "missing_filled": missing_filled,
            "mode_used": mode_used if pd.notna(mode_used) else None,
            "mode_count": mode_count,
        }

    def drop_missing_rows(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Drop rows that contain any missing values.

        Args:
            df: Input dataframe.

        Returns:
            (cleaned_df, metadata)

        Metadata:
            - rows_before: Total input rows
            - rows_after: Rows after dropping missing rows
            - rows_dropped: Count of rows removed
            - missing_cells_total_before: Total missing cells before drop
        """
        self._validate_dataframe(df)

        rows_before = int(len(df))
        if df.empty:
            return df.copy(deep=True), {
                "rows_before": 0,
                "rows_after": 0,
                "rows_dropped": 0,
                "missing_cells_total_before": 0,
            }

        missing_cells_total_before = int(df.isna().sum().sum())

        cleaned = df.copy(deep=True)
        cleaned_no_missing = cleaned.dropna(how="any")

        rows_after = int(len(cleaned_no_missing))
        rows_dropped = max(0, rows_before - rows_after)

        return cleaned_no_missing, {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "rows_dropped": rows_dropped,
            "missing_cells_total_before": missing_cells_total_before,
        }

    def trim_whitespace(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Trim leading/trailing whitespace for object-like columns.

        This targets columns with dtype 'object' or 'string' and applies str.strip
        to non-null values.

        Args:
            df: Input dataframe.

        Returns:
            (cleaned_df, metadata)

        Metadata:
            - columns_processed: List of columns included in trimming
            - cells_changed: Estimated count of cells where a change occurred
        """
        self._validate_dataframe(df)

        cleaned = df.copy(deep=True)
        if cleaned.empty:
            return cleaned, {"columns_processed": [], "cells_changed": 0}

        # Identify likely text columns.
        columns_processed: list[str] = []
        cells_changed = 0

        for col in cleaned.columns:
            dtype = cleaned[col].dtype
            if pd.api.types.is_object_dtype(dtype) or pd.api.types.is_string_dtype(dtype):
                columns_processed.append(str(col))

                original = cleaned[col]
                # Only operate on non-null values.
                stripped = original.where(original.isna(), original.astype(str).str.strip())
                # Count changes (avoid NaN comparison pitfalls by masking NaNs).
                changed_mask = ~original.isna() & (original.astype(str) != stripped)
                cells_changed += int(changed_mask.sum())

                cleaned[col] = stripped

        return cleaned, {"columns_processed": columns_processed, "cells_changed": cells_changed}

    def standardize_text(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Standardize text values across text columns.

        Current strategy:
        - Convert to string for non-null values
        - Lowercase
        - Collapse internal whitespace to a single space

        Args:
            df: Input dataframe.

        Returns:
            (cleaned_df, metadata)

        Metadata:
            - columns_processed: Columns included in standardization
            - cells_changed: Estimated count of changed cells
        """
        self._validate_dataframe(df)

        cleaned = df.copy(deep=True)
        if cleaned.empty:
            return cleaned, {"columns_processed": [], "cells_changed": 0}

        columns_processed: list[str] = []
        cells_changed = 0

        for col in cleaned.columns:
            dtype = cleaned[col].dtype
            if pd.api.types.is_object_dtype(dtype) or pd.api.types.is_string_dtype(dtype):
                columns_processed.append(str(col))

                original = cleaned[col]
                non_null_mask = ~original.isna()

                # Convert to string, lowercase, collapse whitespace.
                standardized = original.copy()
                standardized[non_null_mask] = (
                    original[non_null_mask]
                    .astype(str)
                    .str.lower()
                    .str.replace(r"\s+", " ", regex=True)
                )

                changed_mask = non_null_mask & (original.astype(str) != standardized)
                cells_changed += int(changed_mask.sum())

                cleaned[col] = standardized

        return cleaned, {"columns_processed": columns_processed, "cells_changed": cells_changed}

    @staticmethod
    def _validate_dataframe(df: pd.DataFrame) -> None:
        """Validate that df is a pandas DataFrame."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

    @staticmethod
    def _validate_column_exists(df: pd.DataFrame, column_name: str) -> None:
        """Validate that a column exists in a dataframe."""
        if column_name not in df.columns:
            raise KeyError(f"Column '{column_name}' does not exist")

