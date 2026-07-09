from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.dataset import DatasetResponse
from app.schemas.profile import ProfileResponse
from app.services.dataset_services import (
    delete_user_dataset,
    download_user_dataset,
    get_latest_dataset_profile,
    get_user_dataset,
    list_user_datasets,
    upload_dataset,
)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def upload_dataset_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a new CSV/XLS/XLSX dataset for the current user."""
    return upload_dataset(db, file, current_user.id)


@router.get("/", response_model=list[DatasetResponse])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all datasets belonging to the current user."""
    return list_user_datasets(db, current_user.id)


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a single dataset when it belongs to the current user."""
    return get_user_dataset(db, dataset_id, current_user.id)


@router.get("/{dataset_id}/profile", response_model=ProfileResponse)
def get_dataset_profile(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the latest generated profile for a user-owned dataset."""
    dataset = get_user_dataset(db, dataset_id, current_user.id)
    return get_latest_dataset_profile(db, dataset.id)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a dataset record and its stored file if owned by the current user."""
    delete_user_dataset(db, dataset_id, current_user.id)
    return None


@router.get("/{dataset_id}/download")
def download_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the original uploaded dataset file for the current user."""
    file_path = download_user_dataset(db, dataset_id, current_user.id)
    return FileResponse(path=str(file_path), filename=file_path.name, media_type="application/octet-stream")
