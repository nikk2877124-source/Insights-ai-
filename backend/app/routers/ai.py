from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.ai import DatasetSummaryRequest, DatasetSummaryResponse
from app.services.ai_services import AIService
from app.services.dataset_services import get_latest_dataset_profile, get_user_dataset


router = APIRouter(prefix="/ai", tags=["AI"])

ai_service = AIService()


@router.get("/test")
def test_ai():
    """Test Ollama connection."""
    response = ai_service.generate_response("Say hello from InsightAI in one sentence.")

    return {"success": True, "response": response}


@router.post(
    "/dataset-summary",
    response_model=DatasetSummaryResponse,
)
def dataset_summary(
    payload: DatasetSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a business-friendly dataset summary from the latest dataset profile."""
    try:
        dataset = get_user_dataset(db, payload.dataset_id, current_user.id)
        latest_profile = get_latest_dataset_profile(db, dataset.id)

        profile_json = latest_profile.profile_json or {}
        if not isinstance(profile_json, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid dataset profile payload",
            )

        summary = ai_service.generate_dataset_summary(profile_json)
        return DatasetSummaryResponse(summary=summary)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dataset summary",
        ) from exc
