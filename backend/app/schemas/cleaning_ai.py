from __future__ import annotations

from pydantic import BaseModel


class CleaningRecommendationsRequest(BaseModel):
    dataset_id: int


class CleaningRecommendationsResponse(BaseModel):
    recommendations: str

