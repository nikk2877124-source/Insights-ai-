"""Dataset profile comparison service.

This service compares two *already computed* dataset profiles.
It performs no database access and no data cleaning.

The output is a JSON-serializable structure that highlights:
- total rows/columns
- missing values
- duplicate rows
- outlier counts
- quality score + grade + status
- improvements (missing fixed, duplicates removed, outliers removed,
  quality score improvement)
"""

from __future__ import annotations

from typing import Any, Mapping


class ComparisonService:
    """Compare before/after dataset profile dictionaries."""

    def compare_profiles(
        self,
        before_profile: Mapping[str, Any] | None,
        after_profile: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Compare two dataset profiles.

        Args:
            before_profile: Profile for the original dataset.
            after_profile: Profile for the cleaned dataset.

        Returns:
            JSON-serializable dictionary with:
              - before metrics
              - after metrics
              - improvements

        Notes:
            - Missing/unknown keys are handled gracefully.
            - Expects the project ProfilingService structure:
                profile = {"summary": {...}, "details": {...}}
              but will also work with flatter dictionaries.
        """

        before_profile = before_profile or {}
        after_profile = after_profile or {}

        before_summary = before_profile.get("summary", before_profile)
        after_summary = after_profile.get("summary", after_profile)

        before_details = before_profile.get("details", {})
        after_details = after_profile.get("details", {})

        before_metrics = self._build_metrics(before_summary=before_summary, before_details=before_details)
        after_metrics = self._build_metrics(after_summary=after_summary, after_details=after_details)

        improvements = self._build_improvements(before_metrics=before_metrics, after_metrics=after_metrics)

        return {
            "before": before_metrics,
            "after": after_metrics,
            "improvements": improvements,
        }

    def _build_metrics(self, *, before_summary: Mapping[str, Any], before_details: Mapping[str, Any]) -> dict[str, Any]:
        total_rows = self._safe_int(before_summary.get("total_rows"))
        total_columns = self._safe_int(before_summary.get("total_columns"))

        missing_values = self._safe_int(before_summary.get("missing_values"))
        duplicate_rows = self._safe_int(before_summary.get("duplicate_rows"))

        # ProfilingService summary uses `outlier_count`.
        outlier_count = self._safe_int(before_summary.get("outlier_count"))

        quality_score = self._safe_float(before_summary.get("quality_score"))
        grade = before_summary.get("grade")
        status = before_summary.get("status")

        return {
            "total_rows": total_rows,
            "total_columns": total_columns,
            "missing_values": missing_values,
            "duplicate_rows": duplicate_rows,
            "outlier_count": outlier_count,
            "quality_score": quality_score,
            "grade": grade,
            "status": status,
        }

    def _build_improvements(self, *, before_metrics: Mapping[str, Any], after_metrics: Mapping[str, Any]) -> dict[str, Any]:
        missing_fixed = self._safe_int(before_metrics.get("missing_values")) - self._safe_int(after_metrics.get("missing_values"))
        duplicates_removed = self._safe_int(before_metrics.get("duplicate_rows")) - self._safe_int(after_metrics.get("duplicate_rows"))
        outliers_removed = self._safe_int(before_metrics.get("outlier_count")) - self._safe_int(after_metrics.get("outlier_count"))

        quality_delta = self._safe_float(after_metrics.get("quality_score")) - self._safe_float(before_metrics.get("quality_score"))

        return {
            "missing_values_fixed": max(0, missing_fixed),
            "duplicate_rows_removed": max(0, duplicates_removed),
            "outliers_removed": max(0, outliers_removed),
            "quality_score_improvement": quality_delta,
        }

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            if value is None:
                return 0
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            if value is None:
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

