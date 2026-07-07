import os
from pathlib import Path
from zipfile import BadZipFile

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.utils.file_handler import save_file


def upload_dataset(db: Session, file, user_id: int) -> Dataset:
    """Validate, store, inspect, and persist dataset metadata for the current user."""
    try:
        file_info = save_file(file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    file_path = Path(file_info["file_path"])
    try:
        if file_info["file_type"] == ".csv":
            dataframe = pd.read_csv(file_path)
        else:
            dataframe = pd.read_excel(file_path)
    except (BadZipFile, ImportError, OSError, pd.errors.ParserError, ValueError) as exc:
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file could not be read. Please verify it is not corrupted.",
        ) from exc

    if dataframe.empty:
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty.")

    total_rows = len(dataframe)
    total_columns = len(dataframe.columns)
    missing_values = int(dataframe.isna().sum().sum())
    duplicate_rows = int(dataframe.duplicated().sum())
    null_percentage = round((missing_values / max(1, dataframe.size)) * 100, 2)
    quality_score = max(0, min(100, 100 - int(null_percentage) - min(20, duplicate_rows)))

    dataset = Dataset(
        filename=file_info["original_filename"],
        stored_filename=file_info["stored_filename"],
        file_path=file_info["file_path"],
        file_type=file_info["file_type"],
        file_size=file_info["file_size"],
        total_rows=total_rows,
        total_columns=total_columns,
        missing_values=missing_values,
        duplicate_rows=duplicate_rows,
        null_percentage=null_percentage,
        quality_score=quality_score,
        status="uploaded",
        uploaded_by=user_id,
    )

    try:
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
    except Exception:
        db.rollback()
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        raise

    return dataset


def list_user_datasets(db: Session, user_id: int) -> list[Dataset]:
    """Return all datasets owned by the current user."""
    return (
        db.query(Dataset)
        .filter(Dataset.uploaded_by == user_id)
        .order_by(Dataset.upload_time.desc())
        .all()
    )


def get_user_dataset(db: Session, dataset_id: int, user_id: int) -> Dataset:
    """Return a single dataset only if it belongs to the current user."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    if dataset.uploaded_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this dataset")
    return dataset


def delete_user_dataset(db: Session, dataset_id: int, user_id: int) -> None:
    """Delete a dataset record and its stored file for the current user."""
    dataset = get_user_dataset(db, dataset_id, user_id)
    file_path = Path(dataset.file_path)

    db.delete(dataset)
    db.commit()

    if file_path.exists():
        file_path.unlink(missing_ok=True)


def download_user_dataset(db: Session, dataset_id: int, user_id: int):
    """Return a file download response for a dataset owned by the current user."""
    dataset = get_user_dataset(db, dataset_id, user_id)
    file_path = Path(dataset.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found")

    return file_path