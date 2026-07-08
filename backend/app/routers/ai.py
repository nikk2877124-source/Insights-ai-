from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.ai import (
    BusinessInsightsRequest,
    BusinessInsightsResponse,
    DatasetSummaryRequest,
    DatasetSummaryResponse,
)

from app.schemas.cleaning_ai import (
    CleaningRecommendationsRequest,
    CleaningRecommendationsResponse,
)
from app.schemas.cleaning_prompt_interpretation import (
    InterpretCleaningPromptRequest,
    InterpretCleaningPromptResponse,
)
from app.schemas.ai_chat import ChatRequest, ChatResponse, ChatHistoryResponse

from app.services.ai_services import AIService

# BusinessInsightsService is a higher-level orchestration that builds
# an LLM prompt from metadata/summary statistics only.

from app.services.chat_service import ChatService

from app.services.business_insight_service import BusinessInsightService
from app.services.dataset_services import get_latest_dataset_profile, get_user_dataset



router = APIRouter(prefix="/ai", tags=["AI"])



ai_service = AIService()
business_insight_service = BusinessInsightService(ai_service=ai_service)



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


@router.post(
    "/cleaning-recommendations",
    response_model=CleaningRecommendationsResponse,
)
def cleaning_recommendations(

    payload: CleaningRecommendationsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate prioritized cleaning recommendations from the latest dataset profile."""
    try:
        dataset = get_user_dataset(db, payload.dataset_id, current_user.id)
        latest_profile = get_latest_dataset_profile(db, dataset.id)

        profile_json = latest_profile.profile_json or {}
        if not isinstance(profile_json, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid dataset profile payload",
            )

        recommendations = ai_service.generate_cleaning_recommendations(profile_json)
        return CleaningRecommendationsResponse(recommendations=recommendations)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cleaning recommendations",
        ) from exc


@router.post(
    "/interpret-prompt",
    response_model=InterpretCleaningPromptResponse,
)
def interpret_prompt(
    payload: InterpretCleaningPromptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    """Interpret a natural-language cleaning prompt into structured operations.

    No cleaning is executed here.
    """
    try:
        dataset = get_user_dataset(db, payload.dataset_id, current_user.id)
        latest_profile = get_latest_dataset_profile(db, dataset.id)

        profile_json = latest_profile.profile_json or {}
        if not isinstance(profile_json, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid dataset profile payload",
            )

        result = ai_service.interpret_cleaning_prompt(
            prompt=payload.prompt,
            dataset_profile=profile_json,
        )

        # Graceful behavior: always return shape required by schema.
        # If LLM returned invalid JSON or validation failed, interpret_cleaning_prompt
        # returns success=False + operations=[].
        return InterpretCleaningPromptResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        return InterpretCleaningPromptResponse(
            success=False,
            operations=[],
            errors=["Failed to interpret prompt"],
        )


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask a question using ONLY dataset profile metadata and store the conversation."""
    try:
        chat_service = ChatService()
        item = chat_service.chat(
            db,
            dataset_id=payload.dataset_id,
            user=current_user,
            question=payload.question,
        )
        return ChatResponse(answer=item.answer)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request",
        ) from exc


@router.post(
    "/business-insights",
    response_model=BusinessInsightsResponse,
)
def business_insights(
    payload: BusinessInsightsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate AI business insights (metadata-only) for a dataset."""
    try:
        # Verify dataset ownership (requirement #1)
        dataset = get_user_dataset(db, payload.dataset_id, current_user.id)
        latest_profile = get_latest_dataset_profile(db, dataset.id)

        profile_json = latest_profile.profile_json or {}
        if not isinstance(profile_json, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid dataset profile payload",
            )

        # Only use metadata/summary statistics.
        summary_statistics: dict[str, object] = {}
        summary = profile_json.get("summary")
        if isinstance(summary, dict):
            # keep small KPI-like metrics only
            for k in (
                "total_rows",
                "total_columns",
                "missing_values",
                "duplicate_rows",
                "outlier_count",
                "quality_score",
                "grade",
                "status",
            ):
                if k in summary:
                    summary_statistics[k] = summary.get(k)

        insights = business_insight_service.generate_business_insights(
            dataset_profile=profile_json,
            summary_statistics=summary_statistics,
        )

        return BusinessInsightsResponse(success=True, insights=insights)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate business insights",
        ) from exc


@router.get("/chat/history/{dataset_id}", response_model=ChatHistoryResponse)
def chat_history(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve stored chat history for a dataset (ownership verified)."""
    # Ownership verification (requirement #5)
    get_user_dataset(db, dataset_id, current_user.id)

    chat_service = ChatService()
    history = chat_service.retrieve_history(
        db,
        dataset_id=dataset_id,
        user_id=current_user.id,
        limit=None,
    )

    return ChatHistoryResponse(
        history=[
            {
                "id": h.id,
                "dataset_id": h.dataset_id,
                "user_id": h.user_id,
                "question": h.question,
                "answer": h.answer,
                "created_at": h.created_at,
            }
            for h in history
        ]
    )


