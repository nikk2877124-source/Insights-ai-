from fastapi import APIRouter
from app.services.ai_services import AIService


router = APIRouter(prefix="/ai", tags=["AI"])

ai_service = AIService()


@router.get("/test")
def test_ai():
    """
    Test Ollama connection.
    """
    response = ai_service.generate_response(
        "Say hello from InsightAI in one sentence."
    )

    return {
        "success": True,
        "response": response
    }