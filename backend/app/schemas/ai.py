from __future__ import annotations

from pydantic import BaseModel


class DatasetSummaryRequest(BaseModel):
    dataset_id: int


class DatasetSummaryResponse(BaseModel):
    summary: str


class BusinessInsightsRequest(BaseModel):
    """Request payload for generating AI business insights."""

    dataset_id: int


class BusinessInsightsResponse(BaseModel):
    """Response payload for generated business insights."""

    success: bool
    insights: str


