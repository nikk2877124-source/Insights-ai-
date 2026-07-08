"""Cleaning pipeline orchestration.

This module provides :class:`CleaningPipeline`, an orchestration layer that
coordinates the full AI cleaning workflow.

Important:
- It must not implement dataframe cleaning logic.
- It only coordinates existing services:
  - Dataset persistence/lookup
  - Prompt parsing
  - Dataframe transformations
  - Dataset profiling
  - CleaningSession persistence

It returns a structured response suitable for API responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cleaning_session import CleaningSession
from app.models.dataset import Dataset
from app.services.cleaning_service import CleaningService
from app.services.cleaning_session_service import _compute_quality, _load_dataset_dataframe
from app.services.dataset_services import get_user_dataset
from app.services.prompt_parser import PromptParser, PromptParseError
from app.services.profiling_service import ProfilingService


@dataclass(frozen=True)
class CleaningPipelineResponse:
    """Structured response returned by the pipeline."""

    session_id: int
    quality_before: float
    quality_after: float
    duplicates_removed: int
    missing_values_fixed: int
    cleaned_file_path: str
    download_ready: bool

    # Keeping JSON-friendly conversion local.
    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "quality_before": self.quality_before,
            "quality_after": self.quality_after,
            "duplicates_removed": self.duplicates_removed,
            "missing_values_fixed": self.missing_values_fixed,
            "cleaned_file_path": self.cleaned_file_path,
            "download_ready": self.download_ready,
        }


class CleaningPipeline:
    """Coordinate the end-to-end cleaning workflow."""

    def __init__(
        self,
        *,
        prompt_parser: PromptParser | None = None,
        cleaning_service: CleaningService | None = None,
        profiling_service: ProfilingService | None = None,
    ) -> None:
        self._prompt_parser = prompt_parser or PromptParser()
        self._cleaning_service = cleaning_service or CleaningService()
        self._profiling_service = profiling_service or ProfilingService()

    def run(
        self,
        *,
        db: Session,
        dataset_id: int,
        user_id: int,
        prompt: str,
    ) -> dict[str, Any]:
        """Execute the cleaning pipeline.

        Workflow:
        1. Load uploaded dataset.
        2. Parse user prompt using PromptParser.
        3. Execute requested operation using CleaningService.
        4. Save cleaned dataset with a new filename.
        5. Generate a new dataset profile using ProfilingService.
        6. Compare before/after statistics.
        7. Update the CleaningSession record.
        8. Return a structured response.
        """

        dataset: Dataset = get_user_dataset(db, dataset_id, user_id)

        original_df: pd.DataFrame = _load_dataset_dataframe(dataset)
        quality_before: float = _compute_quality(original_df)
        duplicates_before: int = int(original_df.duplicated().sum()) if not original_df.empty else 0
        missing_values_before: int = int(original_df.isna().sum().sum()) if not original_df.empty else 0

        # 2. Parse the prompt.
        try:
            parsed = self._prompt_parser.parse(prompt)
        except PromptParseError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        operation_name: str = parsed["operation"]
        column: str | None = parsed.get("column")

        # 3. Execute via CleaningService (no cleaning logic here).
        try:
            cleaned_df, op_metadata = self._execute_operation(df=original_df, operation=operation_name, column=column)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cleaning operation failed",
            ) from exc

        quality_after: float = _compute_quality(cleaned_df)

        duplicates_after: int = int(cleaned_df.duplicated().sum()) if not cleaned_df.empty else 0
        missing_values_after: int = int(cleaned_df.isna().sum().sum()) if not cleaned_df.empty else 0

        # 4. Save cleaned dataset.
        cleaned_folder = Path(__file__).resolve().parents[2] / "datasets" / "cleaned"
        cleaned_folder.mkdir(parents=True, exist_ok=True)

        original_name = Path(dataset.file_path).name
        cleaned_name = f"cleaned_{dataset.id}_{original_name}"
        cleaned_path = cleaned_folder / cleaned_name

        if dataset.file_type == ".csv":
            cleaned_df.to_csv(cleaned_path, index=False)
        else:
            cleaned_df.to_excel(cleaned_path, index=False)

        # 5. Generate profile (not stored here to DB; current project doesn't persist it in models).
        #    This keeps the pipeline aligned with the workflow request while avoiding duplication.
        _profile = self._profiling_service.generate_profile(cleaned_df, dataset_name=dataset.filename)

        # 7. Update CleaningSession record.
        #    Current project already has CleaningSession persistence in cleaning_session_service.
        #    To avoid duplicating logic, we create a minimal record update here.
        #    If your codebase expects more fields, align with CleaningSession schema/model.
        session = CleaningSession(
            dataset_id=dataset.id,
            user_id=user_id,
            original_file=dataset.filename,
            original_file_path=dataset.file_path,
            cleaned_file=cleaned_name,
            cleaned_file_path=str(cleaned_path),
            prompt=prompt,
            operation=operation_name,
            rows_before=int(len(original_df)),
            rows_after=int(len(cleaned_df)),
            quality_before=float(quality_before),
            quality_after=float(quality_after),
            status="completed",
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        response = CleaningPipelineResponse(
            session_id=session.id,
            quality_before=quality_before,
            quality_after=quality_after,
            duplicates_removed=max(0, duplicates_before - duplicates_after),
            missing_values_fixed=max(0, missing_values_before - missing_values_after),
            cleaned_file_path=str(cleaned_path),
            download_ready=True,
        )

        return response.to_dict()

    def _execute_operation(
        self,
        *,
        df: pd.DataFrame,
        operation: str,
        column: str | None,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Map operation name to CleaningService methods.

        This mapping is orchestration glue; the actual transformation logic is
        still implemented in CleaningService.
        """
        if operation == "remove_duplicates":
            return self._cleaning_service.remove_duplicates(df)
        if operation == "drop_missing_rows":
            return self._cleaning_service.drop_missing_rows(df)
        if operation == "trim_whitespace":
            return self._cleaning_service.trim_whitespace(df)
        if operation == "standardize_text":
            return self._cleaning_service.standardize_text(df)

        if operation in {"fill_missing_mean", "fill_missing_median", "fill_missing_mode"}:
            if not column:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing target column for operation '{operation}'",
                )

            if operation == "fill_missing_mean":
                return self._cleaning_service.fill_missing_mean(df, column)
            if operation == "fill_missing_median":
                return self._cleaning_service.fill_missing_median(df, column)
            if operation == "fill_missing_mode":
                return self._cleaning_service.fill_missing_mode(df, column)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported cleaning operation: {operation}",
        )

