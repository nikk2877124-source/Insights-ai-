"""Prompt parsing for dataset cleaning operations.

This module provides a small, deterministic parser that converts a natural
language cleaning prompt into a structured operation description.

Key design goals:
- Independent from FastAPI and the database (pure parsing logic only).
- Deterministic behavior (no randomness, no I/O).
- Case-insensitive + whitespace-tolerant parsing.
- Validate supported operations and return clear errors for unsupported
  prompts.
- Keep parsing logic modular and SOLID-friendly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Final


class PromptParseError(ValueError):
    """Raised when the prompt cannot be mapped to a supported operation."""


@dataclass(frozen=True)
class _OperationSpec:
    """Internal representation of one supported operation."""

    operation: str
    # Keywords/phrases used to detect the operation.
    # All matching is done against a normalized prompt.
    patterns: tuple[str, ...]
    # Whether the operation expects a column extraction.
    needs_column: bool = False


class PromptParser:
    """Parse user prompts into a cleaning operation descriptor.

    The parser returns a JSON-serializable dictionary with at minimum:
      - {"operation": <operation_name>}

    For operations that require a target column, it may also include:
      - {"operation": <operation_name>, "column": <column_name>}

    Supported operations:
    - remove_duplicates
    - fill_missing_mean
    - fill_missing_median
    - fill_missing_mode
    - drop_missing_rows
    - trim_whitespace
    - standardize_text
    """

    _SUPPORTED: Final[tuple[_OperationSpec, ...]] = (
        _OperationSpec(
            operation="remove_duplicates",
            patterns=(
                "remove duplicates",
                "duplicate rows",
                "duplicates",
                "deduplicate",
                "remove duplicate",
            ),
        ),
        _OperationSpec(
            operation="fill_missing_mean",
            patterns=(
                "fill missing",
                "fill na",
                "mean",
                "average",
            ),
            needs_column=True,
        ),
        _OperationSpec(
            operation="fill_missing_median",
            patterns=(
                "fill missing",
                "fill na",
                "median",
            ),
            needs_column=True,
        ),
        _OperationSpec(
            operation="fill_missing_mode",
            patterns=(
                "fill missing",
                "fill na",
                "mode",
            ),
            needs_column=True,
        ),
        _OperationSpec(
            operation="drop_missing_rows",
            patterns=(
                "drop missing",
                "drop na",
                "delete missing",
                "remove missing",
                "rows with missing",
            ),
        ),
        _OperationSpec(
            operation="trim_whitespace",
            patterns=(
                "trim whitespace",
                "trim spaces",
                "strip whitespace",
                "remove leading trailing spaces",
                "trim",
            ),
        ),
        _OperationSpec(
            operation="standardize_text",
            patterns=(
                "standardize text",
                "standardize",
                "standardise",
                "normalize text",
                "normalize",
                "clean text",
            ),
        ),
    )

    # Column extraction helpers
    _COLUMN_EQ_RE: Final[re.Pattern[str]] = re.compile(
        r"\bcolumn\s*=\s*([^\n\r]+)", flags=re.IGNORECASE
    )
    _COLUMN_FOR_RE: Final[re.Pattern[str]] = re.compile(
        r"\b(?:for|with)\s+([A-Za-z_][A-Za-z0-9_\- ]*)\b",
        flags=re.IGNORECASE,
    )
    _COLUMN_FILL_RE: Final[re.Pattern[str]] = re.compile(
        r"\bfill\s+missing\s+(.+?)\s+(?:with|using)\b",
        flags=re.IGNORECASE,
    )

    def parse(self, prompt: str) -> dict[str, Any]:
        """Parse a natural language prompt.

        Args:
            prompt: Raw user prompt.

        Returns:
            A dictionary describing the parsed cleaning operation.

        Raises:
            PromptParseError: If the prompt cannot be mapped to a supported
                operation.
        """
        if prompt is None:
            raise PromptParseError("Prompt must be a non-empty string")

        normalized = self._normalize(prompt)
        if not normalized:
            raise PromptParseError("Prompt must be a non-empty string")

        spec = self._identify_operation(normalized)

        result: dict[str, Any] = {"operation": spec.operation}
        if spec.needs_column:
            column = self._extract_column(normalized)
            if not column:
                raise PromptParseError(
                    f"Missing target column for operation '{spec.operation}'. "
                    "Use a prompt like 'Fill missing <Column> with median' or 'column=<Column>'."
                )
            result["column"] = column

        return result

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize prompt: lowercase + collapse whitespace."""
        # Lowercase + trim.
        lowered = text.strip().lower()
        # Collapse multiple whitespace to single spaces.
        return re.sub(r"\s+", " ", lowered)

    def _identify_operation(self, normalized_prompt: str) -> _OperationSpec:
        """Identify which operation the prompt requests."""
        # Match longer/more specific phrases first by ordering in _SUPPORTED.
        for spec in self._SUPPORTED:
            for pattern in spec.patterns:
                if pattern in normalized_prompt:
                    return spec

        raise PromptParseError(
            "Unsupported cleaning operation in prompt. "
            "Supported operations: remove_duplicates, fill_missing_mean, fill_missing_median, "
            "fill_missing_mode, drop_missing_rows, trim_whitespace, standardize_text."
        )

    def _extract_column(self, normalized_prompt: str) -> str | None:
        """Extract the target column name from a prompt.

        Supported styles (case-insensitive):
        - "column=Salary"
        - "Fill missing Salary with median"
        - "Fill missing Salary using median"
        - "Fill missing with median for Salary"

        Notes:
        - We keep this best-effort and deterministic.
        - Column names are returned as-is from the prompt (trimmed).
        """
        # column=<name>
        m = self._COLUMN_EQ_RE.search(normalized_prompt)
        if m:
            col = m.group(1).strip()
            return col if col else None

        # Fill missing <col> with/using <strategy>
        m = self._COLUMN_FILL_RE.search(normalized_prompt)
        if m:
            col = m.group(1).strip()
            return col if col else None

        # Generic: "for <col>" / "with <col>"
        # Avoid picking up the strategy token by preferring cases where
        # the prompt contains "missing".
        if "missing" in normalized_prompt:
            m = self._COLUMN_FOR_RE.search(normalized_prompt)
            if m:
                col = m.group(1).strip()
                return col if col else None

        return None

