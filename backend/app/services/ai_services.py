from __future__ import annotations

import json
from typing import Any

from app.core.ollama import OllamaClient


class AIService:
    """Service responsible for interacting with the AI model."""

    # Keep the whitelist deterministic and aligned with CleaningService.
    _SUPPORTED_OPERATIONS: dict[str, dict[str, Any]] = {
        "remove_duplicates": {"needs_column": False},
        "fill_missing_mean": {"needs_column": True},
        "fill_missing_median": {"needs_column": True},
        "fill_missing_mode": {"needs_column": True},
        "drop_missing_rows": {"needs_column": False},
        "trim_whitespace": {"needs_column": False},
        "standardize_text": {"needs_column": False},
    }

    def __init__(self):
        self.ollama = OllamaClient()

    def generate_response(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the generated response."""
        return self.ollama.generate(prompt)

    def interpret_cleaning_prompt(self, prompt: str, dataset_profile: dict) -> dict[str, Any]:
        """Interpret a natural-language cleaning prompt into structured operations.

        The method:
        - uses the existing OllamaClient
        - asks the model to respond with ONLY JSON
        - validates operations against a fixed whitelist
        - validates column names against dataset_profile-derived columns
        - gracefully handles invalid JSON / invalid operations

        Returns:
            {"success": bool, "operations": [...]} (plus optional "errors").
        """

        if not isinstance(prompt, str) or not prompt.strip():
            return {"success": False, "operations": [], "errors": ["prompt must be a non-empty string"]}
        if not isinstance(dataset_profile, dict):
            return {"success": False, "operations": [], "errors": ["dataset_profile must be a dict"]}

        # Extract column names from dataset profile.
        # ProfilingService.generate_profile -> profile_json['summary']['basic_info']['column_names']
        # but earlier code is inconsistent across projects; we support a few shapes.
        column_names: list[str] = []
        summary = dataset_profile.get("summary") if isinstance(dataset_profile.get("summary"), dict) else None
        if summary and isinstance(summary, dict):
            basic_info = summary.get("basic_info")
            if isinstance(basic_info, dict) and isinstance(basic_info.get("column_names"), list):
                column_names = [str(c) for c in basic_info["column_names"]]
            elif isinstance(basic_info, dict) and isinstance(basic_info.get("column_names"), (list, tuple)):
                column_names = [str(c) for c in basic_info["column_names"]]

        if not column_names:
            # Fall back to top-level.
            if isinstance(dataset_profile.get("column_names"), list):
                column_names = [str(c) for c in dataset_profile["column_names"]]

        supported_ops = sorted(self._SUPPORTED_OPERATIONS.keys())

        operations_spec = [
            {"operation": op, "needs_column": self._SUPPORTED_OPERATIONS[op]["needs_column"]}
            for op in supported_ops
        ]

        ollama_prompt = (
            "You are an expert data-cleaning assistant. "
            "Convert the user's cleaning request into a JSON plan.\n\n"
            "OUTPUT REQUIREMENTS:\n"
            "- Return ONLY valid JSON. No markdown. No surrounding text.\n\n"
            "RESPONSE SCHEMA:\n"
            "{\n"
            "  \"operations\": [\n"
            "    {\n"
            "      \"operation\": <one of the supported operations>,\n"
            "      \"column\": <column name or null>\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            "SUPPORTED CLEANING OPERATIONS (whitelist):\n"
            f"{json.dumps(operations_spec, ensure_ascii=False, indent=2)}\n\n"
            "DATASET COLUMN NAMES:\n"
            f"{json.dumps(column_names, ensure_ascii=False, indent=2)}\n\n"
            "USER PROMPT:\n"
            f"{prompt}\n\n"
            "Rules:\n"
            "- Use only the supported operations listed above.\n"
            "- Only include a column name when the operation requires a target column.\n"
            "- If the prompt doesn't specify a needed column, set column to null.\n"
            "- If a specified column is not in the dataset column names, set column to null.\n"
        )

        raw = self.ollama.generate(ollama_prompt)

        # Parse JSON from the model output.
        try:
            parsed = json.loads(raw)
        except Exception:
            return {
                "success": False,
                "operations": [],
                "errors": ["Model returned invalid JSON"]
            }

        if not isinstance(parsed, dict) or "operations" not in parsed or not isinstance(parsed["operations"], list):
            return {"success": False, "operations": [], "errors": ["JSON must contain 'operations' as a list"]}

        validated_ops: list[dict[str, Any]] = []
        errors: list[str] = []

        col_set = {str(c) for c in column_names}

        for item in parsed["operations"]:
            if not isinstance(item, dict):
                errors.append("Each operation must be an object")
                continue

            op = item.get("operation")
            if not isinstance(op, str):
                errors.append("Operation name must be a string")
                continue

            if op not in self._SUPPORTED_OPERATIONS:
                errors.append(f"Unsupported operation: {op}")
                continue

            needs_column = bool(self._SUPPORTED_OPERATIONS[op]["needs_column"])

            column = item.get("column")
            if column is None:
                column_str = None
            else:
                column_str = str(column)

            if needs_column:
                if not column_str:
                    errors.append(f"Missing column for operation: {op}")
                    continue
                if column_str not in col_set:
                    errors.append(f"Column not in dataset profile: {column_str}")
                    continue
                validated_ops.append({"operation": op, "column": column_str})
            else:
                # Ignore any provided column for non-column operations.
                validated_ops.append({"operation": op})

        return {
            "success": len(validated_ops) > 0,
            "operations": validated_ops,
            "errors": errors,
        }

    def generate_dataset_summary(self, profile: dict) -> str:

        """Generate a business-friendly dataset summary from a dataset profile."""
        if not isinstance(profile, dict):
            raise TypeError("profile must be a dictionary")

        # Profile expected shape (based on ProfilingService.generate_profile):
        # - summary: { total_rows, total_columns, missing_values, duplicate_rows, outlier_count, quality_score, grade, status }
        # - details: ...
        # But we defensively support flattened or partially-populated structures.
        summary = profile.get("summary") if isinstance(profile.get("summary"), dict) else profile

        total_rows = summary.get("total_rows")
        total_columns = summary.get("total_columns")
        missing_values = summary.get("missing_values")
        duplicate_rows = summary.get("duplicate_rows")
        outlier_count = summary.get("outlier_count")
        quality_score = summary.get("quality_score")
        grade = summary.get("grade")
        status = summary.get("status")

        prompt = (
            "You are a Senior Data Analyst.\n\n"
            "Write a concise business-friendly summary.\n\n"
            "Use 3–5 sentences.\n"
            "Mention data quality.\n"
            "Mention whether cleaning is recommended.\n"
            "Do not invent information.\n"
            "Do not use markdown.\n\n"
            "Dataset profile metrics:\n"
            f"Total Rows: {total_rows}\n"
            f"Total Columns: {total_columns}\n"
            f"Missing Values: {missing_values}\n"
            f"Duplicate Rows: {duplicate_rows}\n"
            f"Outlier Count: {outlier_count}\n"
            f"Quality Score: {quality_score}\n"
            f"Grade: {grade}\n"
            f"Status: {status}\n"
        )

        return self.ollama.generate(prompt)

    def generate_cleaning_recommendations(self, profile: dict) -> str:
        """Generate prioritized cleaning recommendations from a dataset profile."""
        if not isinstance(profile, dict):
            raise TypeError("profile must be a dictionary")

        summary = profile.get("summary") if isinstance(profile.get("summary"), dict) else profile

        total_rows = summary.get("total_rows")
        total_columns = summary.get("total_columns")
        missing_values = summary.get("missing_values")
        duplicate_rows = summary.get("duplicate_rows")
        outlier_count = summary.get("outlier_count")
        quality_score = summary.get("quality_score")
        grade = summary.get("grade")
        status = summary.get("status")

        prompt = (
            "You are an expert Data Cleaning Consultant.\n\n"
            "Analyze the dataset profile.\n"
            "Recommend only the necessary cleaning actions.\n"
            "Explain why each action is recommended.\n"
            "Prioritize the actions.\n"
            "Estimate the expected improvement in data quality.\n"
            "Do not invent statistics.\n"
            "Keep the response concise and business-friendly.\n\n"
            "Output requirements: plain text only, no markdown.\n\n"
            "Dataset profile metrics:\n"
            f"Total Rows: {total_rows}\n"
            f"Total Columns: {total_columns}\n"
            f"Missing Values: {missing_values}\n"
            f"Duplicate Rows: {duplicate_rows}\n"
            f"Outlier Count: {outlier_count}\n"
            f"Quality Score: {quality_score}\n"
            f"Grade: {grade}\n"
            f"Status: {status}\n\n"
            "If you cannot estimate expected improvement in data quality from the provided metrics, say 'Not enough data to estimate.'"
        )

        return self.ollama.generate(prompt)

