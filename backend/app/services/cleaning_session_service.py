"""Cleaning session orchestration.

This module intentionally contains the business logic required to:
- Load the user-owned dataset from storage
- Compute before/after quality metrics
- Apply dataframe cleaning operations via CleaningService
- Persist CleaningSession records
- Persist cleaned dataset files for later download

Routers should remain thin (validation/auth/ownership checks + calling this module).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cleaning_session import CleaningSession
from app.models.dataset import Dataset
from app.services.cleaning_service import CleaningService
from app.services.prompt_parser import PromptParser




def _load_dataset_dataframe(dataset: Dataset) -> pd.DataFrame:
    file_path = Path(dataset.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored dataset file not found",
        )

    try:
        if dataset.file_type == ".csv":
            return pd.read_csv(file_path)
        # xls/xlsx are stored with the original extension mapped by file_handler
        return pd.read_excel(file_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read stored dataset file",
        ) from exc


def _compute_quality(df: pd.DataFrame) -> float:
    """Compute a lightweight data quality score.

    The project already computes a quality score during dataset upload.
    For cleaning, we keep this local, deterministic, and fast.
    """
    if df is None or df.empty:
        return 0.0

    missing_values = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    null_percentage = (missing_values / max(1, df.size)) * 100
    # Favor fewer nulls and fewer duplicates.
    score = 100 - int(null_percentage) - min(20, duplicate_rows)
    return float(max(0, min(100, score)))


def _apply_operation(
    df: pd.DataFrame,
    operation: dict[str, Any],
    prompt: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:

    """Apply a cleaning operation.

    The prompt currently serves as metadata stored into CleaningSession.
    Operation selection uses a simple mapping from prompt/operation keyword.

    Note: This is kept small and deterministic.
    """
    service = CleaningService()
    op = (operation or "").lower().strip()

    if not op:
        # Best-effort mapping using prompt keywords.
        prompt_lower = (prompt or "").lower()
        if "duplicate" in prompt_lower:
            op = "remove_duplicates"
        elif "mean" in prompt_lower:
            op = "fill_missing_mean"
        elif "median" in prompt_lower:
            op = "fill_missing_median"
        elif "mode" in prompt_lower:
            op = "fill_missing_mode"
        elif "trim" in prompt_lower:
            op = "trim_whitespace"
        elif "standard" in prompt_lower or "standardize" in prompt_lower:
            op = "standardize_text"
        elif "drop" in prompt_lower and "missing" in prompt_lower:
            op = "drop_missing_rows"
        else:
            op = "remove_duplicates"

    # Optional: infer target column for mean/median/mode.
    target_column = None
    if op in {"fill_missing_mean", "fill_missing_median", "fill_missing_mode"}:
        # Heuristic: look for "column=<name>" in prompt.
        import re

        prompt_text = prompt or ""
        match = re.search(r"column\s*=\s*([^\n\r]+)", prompt_text, flags=re.IGNORECASE)
        if match:
            target_column = match.group(1).strip()
        else:
            # Fallback: first numeric-like column with missing values.
            missing_cols = [c for c in df.columns if df[c].isna().any()]
            target_column = missing_cols[0] if missing_cols else (df.columns[0] if len(df.columns) else None)

    if op == "remove_duplicates":
        return service.remove_duplicates(df)
    if op == "drop_missing_rows":
        return service.drop_missing_rows(df)
    if op == "trim_whitespace":
        return service.trim_whitespace(df)
    if op == "standardize_text":
        return service.standardize_text(df)
    if op == "fill_missing_mean":
        if not target_column:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No target column available for mean fill")
        return service.fill_missing_mean(df, target_column)
    if op == "fill_missing_median":
        if not target_column:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No target column available for median fill")
        return service.fill_missing_median(df, target_column)
    if op == "fill_missing_mode":
        if not target_column:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No target column available for mode fill")
        return service.fill_missing_mode(df, target_column)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported cleaning operation: {operation}",
    )


def start_cleaning_session(
    *,
    db: Session,
    dataset: Dataset,
    user_id: int,
    prompt: str,
) -> CleaningSession:
    """Create, execute, and persist a CleaningSession."""

    original_df = _load_dataset_dataframe(dataset)
    quality_before = _compute_quality(original_df)

    # Parse prompt into a structured operation descriptor.
    parser = PromptParser()
    try:
        parsed = parser.parse(prompt)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    op = parsed["operation"]

    try:
        cleaned_df, metadata = _apply_operation(original_df, op, prompt)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cleaning operation failed",
        ) from exc

    quality_after = _compute_quality(cleaned_df)


    # Persist cleaned dataset
    cleaned_folder = Path(__file__).resolve().parents[2] / "datasets" / "cleaned"
    cleaned_folder.mkdir(parents=True, exist_ok=True)

    original_name = Path(dataset.file_path).name
    cleaned_name = f"cleaned_{dataset.id}_{original_name}"
    cleaned_path = cleaned_folder / cleaned_name

    # Choose output format based on original.
    if dataset.file_type == ".csv":
        cleaned_df.to_csv(cleaned_path, index=False)
    else:
        # Default to Excel output for xls/xlsx
        cleaned_df.to_excel(cleaned_path, index=False)

    session = CleaningSession(
        dataset_id=dataset.id,
        user_id=user_id,
        original_file=dataset.filename,
        original_file_path=dataset.file_path,
        cleaned_file=cleaned_name,
        cleaned_file_path=str(cleaned_path),
        prompt=prompt,
        operation=op,
        rows_before=int(len(original_df)),
        rows_after=int(len(cleaned_df)),
        quality_before=float(quality_before),
        quality_after=float(quality_after),
        status="completed",
    )

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_cleaning_session(db: Session, *, user_id: int, session_id: int) -> CleaningSession:
    session = db.query(CleaningSession).filter(CleaningSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cleaning session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this session")
    return session


def list_user_cleaning_history(db: Session, *, user_id: int) -> list[CleaningSession]:
    return (
        db.query(CleaningSession)
        .filter(CleaningSession.user_id == user_id)
        .order_by(CleaningSession.created_at.desc())
        .all()
    )


