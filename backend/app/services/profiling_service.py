"""Utilities for generating dataset profiling statistics.

This service keeps the profiling logic modular so the application can expand
future iterations without rewriting the existing inspection flow.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)


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
        self._validate_dataframe(df)

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
        self._validate_dataframe(df)

        total_rows = len(df)
        duplicate_rows = int(df.duplicated().sum())
        duplicate_percentage = round((duplicate_rows / total_rows) * 100, 1) if total_rows else 0.0

        return {
            "duplicate_rows": duplicate_rows,
            "duplicate_percentage": duplicate_percentage,
        }

    def analyze_data_types(self, df: pd.DataFrame) -> dict[str, Any]:
        """Classify columns by their inferred data type.

        The method returns the numeric, categorical, boolean, datetime and object
        columns separately and also provides the raw pandas dtype for each
        column.
        """
        self._validate_dataframe(df)

        numeric_columns: list[str] = []
        categorical_columns: list[str] = []
        boolean_columns: list[str] = []
        datetime_columns: list[str] = []
        object_columns: list[str] = []
        column_types: dict[str, str] = {}

        for column_name in df.columns:
            column = df[column_name]
            column_name_str = str(column_name)
            dtype = column.dtype
            column_types[column_name_str] = str(dtype)

            if is_bool_dtype(dtype):
                boolean_columns.append(column_name_str)
            elif is_datetime64_any_dtype(dtype):
                datetime_columns.append(column_name_str)
            elif is_numeric_dtype(dtype):
                numeric_columns.append(column_name_str)
            elif is_object_dtype(dtype) or is_categorical_dtype(dtype):
                object_columns.append(column_name_str)
                categorical_columns.append(column_name_str)
            else:
                categorical_columns.append(column_name_str)

        return {
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "datetime_columns": datetime_columns,
            "boolean_columns": boolean_columns,
            "object_columns": object_columns,
            "column_types": column_types,
        }

    def analyze_statistics(self, df: pd.DataFrame) -> dict[str, Any]:
        """Calculate descriptive statistics for numeric columns only.

        Missing values are ignored during the computation. Empty or all-missing
        numeric columns return zero counts with null statistics to keep the output
        JSON-safe.
        """
        self._validate_dataframe(df)

        numeric_columns = self._get_numeric_columns(df)
        statistics: dict[str, dict[str, Any]] = {}

        for column_name in numeric_columns:
            numeric_series = pd.to_numeric(df[column_name], errors="coerce")
            clean_series = numeric_series.dropna()

            if clean_series.empty:
                statistics[str(column_name)] = {
                    "count": 0,
                    "mean": None,
                    "median": None,
                    "min": None,
                    "max": None,
                    "std": None,
                    "variance": None,
                    "q1": None,
                    "q3": None,
                    "iqr": None,
                }
                continue

            statistics[str(column_name)] = {
                "count": int(clean_series.count()),
                "mean": self._serialize_value(clean_series.mean()),
                "median": self._serialize_value(clean_series.median()),
                "min": self._serialize_value(clean_series.min()),
                "max": self._serialize_value(clean_series.max()),
                "std": self._serialize_value(clean_series.std()),
                "variance": self._serialize_value(clean_series.var()),
                "q1": self._serialize_value(clean_series.quantile(0.25)),
                "q3": self._serialize_value(clean_series.quantile(0.75)),
                "iqr": self._serialize_value(clean_series.quantile(0.75) - clean_series.quantile(0.25)),
            }

        return statistics

    def analyze_memory(self, df: pd.DataFrame) -> dict[str, Any]:
        """Return the dataset memory footprint in bytes and megabytes."""
        self._validate_dataframe(df)

        memory_usage_bytes = int(df.memory_usage(index=True, deep=True).sum())
        memory_usage_mb = round(max(memory_usage_bytes / (1024 * 1024), 0.01), 2)

        return {
            "memory_usage_mb": memory_usage_mb,
            "memory_usage_bytes": memory_usage_bytes,
        }

    def detect_mixed_types(self, df: pd.DataFrame) -> dict[str, Any]:
        """Find columns that contain more than one normalized Python value type."""
        self._validate_dataframe(df)

        mixed_type_columns: list[str] = []
        for column_name in df.columns:
            unique_types = {
                self._normalize_value_type(value)
                for value in df[column_name].dropna()
                if self._normalize_value_type(value) is not None
            }
            if len(unique_types) > 1:
                mixed_type_columns.append(str(column_name))

        return {"mixed_type_columns": mixed_type_columns}

    def detect_outliers(self, df: pd.DataFrame) -> dict[str, Any]:
        """Detect outliers in numeric columns using the IQR rule.

        Values outside the lower and upper IQR bounds are treated as outliers.
        Empty or constant-value columns return zero outliers safely.
        """
        self._validate_dataframe(df)

        numeric_columns = self._get_numeric_columns(df)
        outlier_summary: dict[str, dict[str, Any]] = {}
        total_outliers = 0

        for column_name in numeric_columns:
            numeric_series = pd.to_numeric(df[column_name], errors="coerce").dropna()
            if numeric_series.empty:
                outlier_summary[str(column_name)] = {
                    "outlier_count": 0,
                    "percentage": 0.0,
                }
                continue

            q1 = numeric_series.quantile(0.25)
            q3 = numeric_series.quantile(0.75)
            iqr = q3 - q1

            if pd.isna(iqr) or iqr == 0:
                outlier_summary[str(column_name)] = {
                    "outlier_count": 0,
                    "percentage": 0.0,
                }
                continue

            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)
            outlier_mask = (numeric_series < lower_bound) | (numeric_series > upper_bound)
            outlier_count = int(outlier_mask.sum())
            total_outliers += outlier_count
            percentage = round((outlier_count / len(numeric_series)) * 100, 2) if len(numeric_series) else 0.0

            outlier_summary[str(column_name)] = {
                "outlier_count": outlier_count,
                "percentage": percentage,
            }

        outlier_summary["total_outliers"] = total_outliers
        return outlier_summary

    def calculate_quality_score(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Calculate a simple dataset quality score from profiling metrics."""
        if not isinstance(profile, dict):
            raise TypeError("profile must be a dictionary")

        score = 100.0
        missing_values = profile.get("missing_values", {}).get("columns", {})
        duplicates = profile.get("duplicates", {})
        mixed_types = profile.get("mixed_types", {}).get("mixed_type_columns", [])
        outliers = profile.get("outliers", {})
        total_columns = profile.get("basic_info", {}).get("total_columns", 0)

        for column_details in missing_values.values():
            missing_percentage = float(column_details.get("percentage", 0.0))
            if missing_percentage == 0:
                continue
            if 0 < missing_percentage <= 5:
                score -= 5
            elif 5 < missing_percentage <= 10:
                score -= 10
            elif 10 < missing_percentage <= 20:
                score -= 20
            else:
                score -= 30

        duplicate_percentage = float(duplicates.get("duplicate_percentage", 0.0))
        if 0 < duplicate_percentage <= 2:
            score -= 5
        elif 2 < duplicate_percentage <= 5:
            score -= 10
        elif duplicate_percentage > 5:
            score -= 20

        mixed_count = min(len(mixed_types), 4)
        score -= mixed_count * 5

        outlier_percentages = [
            float(column_details.get("percentage", 0.0))
            for column_details in outliers.values()
            if isinstance(column_details, dict) and "percentage" in column_details
        ]
        if outlier_percentages:
            max_outlier_percentage = max(outlier_percentages)
            if 0 < max_outlier_percentage < 1:
                score -= 0
            elif 1 <= max_outlier_percentage <= 3:
                score -= 5
            elif 3 < max_outlier_percentage <= 5:
                score -= 10
            else:
                score -= 15

        if total_columns and total_columns > 0:
            object_columns = profile.get("data_types", {}).get("object_columns", [])
            if len(object_columns) / total_columns > 0.6:
                score -= 5

        score = max(0.0, min(100.0, round(score, 1)))

        if score >= 90:
            grade = "A"
            status = "Excellent"
        elif score >= 80:
            grade = "B"
            status = "Good"
        elif score >= 70:
            grade = "C"
            status = "Fair"
        elif score >= 60:
            grade = "D"
            status = "Poor"
        else:
            grade = "F"
            status = "Critical"

        return {"score": score, "grade": grade, "status": status}

    def generate_dataset_health(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Create a human-readable health summary for the dataset."""
        if not isinstance(profile, dict):
            raise TypeError("profile must be a dictionary")

        major_issues: list[str] = []
        recommendations: list[str] = []

        missing_columns = [
            column_name
            for column_name, details in profile.get("missing_values", {}).get("columns", {}).items()
            if int(details.get("count", 0)) > 0
        ]
        if missing_columns:
            major_issues.append("Missing values detected in one or more columns")
            recommendations.append("Fill missing values using column-appropriate strategies")

        duplicate_rows = int(profile.get("duplicates", {}).get("duplicate_rows", 0))
        if duplicate_rows > 0:
            major_issues.append("Duplicate rows detected")
            recommendations.append("Remove duplicate rows")

        mixed_type_columns = profile.get("mixed_types", {}).get("mixed_type_columns", [])
        if mixed_type_columns:
            major_issues.append("Mixed datatypes detected in one or more columns")
            recommendations.append("Standardize mixed-type columns before analysis")

        outlier_details = profile.get("outliers", {})
        outlier_columns = [
            column_name
            for column_name, details in outlier_details.items()
            if column_name != "total_outliers" and int(details.get("outlier_count", 0)) > 0
        ]
        if outlier_columns:
            major_issues.append("Outliers detected in numeric columns")
            recommendations.append("Review outlier values before modeling")

        if not major_issues:
            status = "Good"
        elif len(major_issues) == 1:
            status = "Fair"
        else:
            status = "Needs Attention"

        return {
            "status": status,
            "major_issues": major_issues,
            "recommendations": recommendations,
        }

    def generate_profile(self, df: pd.DataFrame, dataset_name: str | None = None) -> dict[str, Any]:
        """Build a compact KPI-style profile plus the richer profiling details.

        The returned structure is intentionally split into two sections:
        - summary: a small, frontend-friendly overview for KPI cards.
        - details: the detailed analysis payload used for deeper inspection.
        """
        self._validate_dataframe(df)

        missing_values = self.analyze_missing_values(df)
        duplicates = self.analyze_duplicates(df)
        outliers = self.detect_outliers(df)
        mixed_types = self.detect_mixed_types(df)
        data_types = self.analyze_data_types(df)
        statistics = self.analyze_statistics(df)
        memory_usage = self.analyze_memory(df)

        profile = {
            "basic_info": self._build_basic_info(df),
            "missing_values": missing_values,
            "duplicates": duplicates,
            "data_types": data_types,
            "statistics": statistics,
            "memory_usage": memory_usage,
            "mixed_types": mixed_types,
            "outliers": outliers,
        }

        profile["quality_score"] = self.calculate_quality_score(profile)
        profile["dataset_health"] = self.generate_dataset_health(profile)

        summary = {
            "dataset_name": dataset_name or "Unnamed Dataset",
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "missing_values": int(missing_values.get("total_missing_values", 0)),
            "duplicate_rows": int(duplicates.get("duplicate_rows", 0)),
            "outlier_count": int(outliers.get("total_outliers", 0)),
            "quality_score": int(profile["quality_score"].get("score", 0)),
            "grade": profile["quality_score"].get("grade", "F"),
            "status": profile["quality_score"].get("status", "Critical"),
        }

        return {
            "summary": summary,
            "details": {
                "missing_values": missing_values,
                "duplicates": duplicates,
                "statistics": statistics,
                "outliers": outliers,
                "data_types": data_types,
                "memory_usage": memory_usage,
                "mixed_types": mixed_types,
                "dataset_health": profile["dataset_health"],
            },
        }

    def _build_basic_info(self, df: pd.DataFrame) -> dict[str, Any]:
        """Create the basic profiling section for the dataset."""
        memory_usage = self.analyze_memory(df)
        return {
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "column_names": [str(column) for column in df.columns.tolist()],
            "data_types": {str(column): str(dtype) for column, dtype in df.dtypes.items()},
            "memory_usage": memory_usage["memory_usage_bytes"],
        }

    def _get_numeric_columns(self, df: pd.DataFrame) -> list[str]:
        """Return the names of numeric columns for the dataset."""
        return [str(column_name) for column_name in df.columns if is_numeric_dtype(df[column_name].dtype)]

    def _normalize_value_type(self, value: Any) -> str | None:
        """Normalize a scalar value to a stable type label for mixed-type detection."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, (bool, np.bool_)):
            return "boolean"
        if isinstance(value, (int, np.integer)) and not isinstance(value, (bool, np.bool_)):
            return "integer"
        if isinstance(value, (float, np.floating)):
            return "float"
        if isinstance(value, (datetime, np.datetime64, pd.Timestamp)):
            return "datetime"
        if isinstance(value, str):
            return "string"
        if isinstance(value, (list, tuple, dict, set)):
            return "complex"
        return type(value).__name__.lower()

    def _serialize_value(self, value: Any) -> Any:
        """Convert NumPy and pandas scalar values into plain Python types."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, (pd.Timestamp, datetime)):
            return value.isoformat()
        if isinstance(value, np.ndarray):
            return value.tolist()
        return value

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """Ensure the input is a pandas DataFrame."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")
