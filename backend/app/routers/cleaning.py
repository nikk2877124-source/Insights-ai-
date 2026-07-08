from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.cleaning_session import CleaningSession
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.cleaning import (
    CleaningHistoryResponse,
    CleaningRequest,
    CleaningResponse,
)
from app.services.cleaning_service import CleaningService
from app.services.dataset_services import get_user_dataset
from app.services.cleaning_session_service import (
    list_user_cleaning_history,
    get_user_cleaning_session,
    start_cleaning_session,
)

router = APIRouter(prefix="/cleaning", tags=["Cleaning"])


@router.post("/start", response_model=CleaningResponse)
def start_cleaning(
    payload: CleaningRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a cleaning session for a dataset the current user owns."""
    # Verify dataset ownership (404/403 semantics are handled by get_user_dataset).
    dataset: Dataset = get_user_dataset(db, payload.dataset_id, current_user.id)

    # Router remains thin: delegate orchestration + persistence to service-layer.
    session = start_cleaning_session(
        db=db,
        dataset=dataset,
        user_id=current_user.id,
        prompt=payload.prompt,
    )

    return CleaningResponse(
        success=True,
        message="Cleaning completed successfully",
        session_id=session.id,
        quality_before=float(session.quality_before or 0.0),
        quality_after=float(session.quality_after or 0.0),
    )


@router.get("/history", response_model=list[CleaningHistoryResponse])
def cleaning_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return cleaning history for the current user."""
    sessions: list[CleaningSession] = list_user_cleaning_history(db, user_id=current_user.id)

    # Map to schema. Dataset name is not stored directly in the model; use dataset relation.
    results: list[CleaningHistoryResponse] = []
    for s in sessions:
        dataset_name = getattr(getattr(s, "dataset", None), "filename", None) or "Unknown Dataset"
        results.append(
            CleaningHistoryResponse(
                id=s.id,
                dataset_name=dataset_name,
                operation=s.operation,
                prompt=s.prompt,
                quality_before=float(s.quality_before or 0.0),
                quality_after=float(s.quality_after or 0.0),
                created_at=s.created_at,
            )
        )
    return results


@router.get("/{session_id}", response_model=CleaningResponse)
def get_cleaning_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a single cleaning session."""
    s = get_user_cleaning_session(db, user_id=current_user.id, session_id=session_id)

    return CleaningResponse(
        success=(s.status == "completed"),
        message=f"Cleaning session {s.status}",
        session_id=s.id,
        quality_before=float(s.quality_before or 0.0),
        quality_after=float(s.quality_after or 0.0),
    )


@router.get("/download/{session_id}")
def download_cleaning_result(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download cleaned dataset produced by the given cleaning session."""
    s = get_user_cleaning_session(db, user_id=current_user.id, session_id=session_id)

    if not s.cleaned_file_path:
        # The session exists, but there's nothing to download.
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cleaned file not available")

    # FileResponse expects an actual filesystem path.
    return FileResponse(
        path=str(s.cleaned_file_path),
        filename=s.cleaned_file or f"cleaned_{s.id}",
        media_type="application/octet-stream",
    )

