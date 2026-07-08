from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.dataset import Dataset
from app.models.user import User
from app.services.comparison_service import ComparisonService
from app.services.dataset_services import get_user_dataset
from app.services.cleaning_session_service import get_user_cleaning_session
from app.models.dataset_profile import DatasetProfile


router = APIRouter(prefix="/comparison", tags=["Comparison"])


@router.get("/session/{session_id}")
def compare_from_cleaning_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return before/after comparison metrics for a cleaning session.

    Contract:
    - { before: {...}, after: {...}, improvements: {...} }

    This endpoint builds comparison from:
    - dataset profile (for before)
    - dataset profile (for after) created during cleaning

    The cleaned profile is assumed to be the latest DatasetProfile after cleaning.
    """

    # Ownership check (ensures the session belongs to current user)
    s = get_user_cleaning_session(db, user_id=current_user.id, session_id=session_id)

    # Dataset ownership (belt-and-suspenders)
    dataset: Dataset = get_user_dataset(db, dataset_id=s.dataset_id, user_id=current_user.id)

    # Before profile: most recent profile BEFORE the cleaning session time.
    # After profile: most recent profile AFTER the cleaning time.
    # If we can't split by time, we fall back gracefully.
    try:
        before_profile = (
            db.query(DatasetProfile)
            .filter(DatasetProfile.dataset_id == dataset.id)
            .filter(DatasetProfile.created_at <= s.created_at)
            .order_by(DatasetProfile.created_at.desc())
            .first()
        )

        after_profile = (
            db.query(DatasetProfile)
            .filter(DatasetProfile.dataset_id == dataset.id)
            .filter(DatasetProfile.created_at >= s.created_at)
            .order_by(DatasetProfile.created_at.desc())
            .first()
        )

        if after_profile is None:
            after_profile = (
                db.query(DatasetProfile)
                .filter(DatasetProfile.dataset_id == dataset.id)
                .order_by(DatasetProfile.created_at.desc())
                .first()
            )

        if before_profile is None:
            before_profile = after_profile

        if before_profile is None or after_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset profile not found",
            )

        comparison = ComparisonService().compare_profiles(
            before_profile=before_profile.profile_json,
            after_profile=after_profile.profile_json,
        )

        return comparison
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate comparison: {exc}",
        ) from exc

