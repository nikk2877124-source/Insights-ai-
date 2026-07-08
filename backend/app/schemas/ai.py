from __future__ import annotations

from pydantic import BaseModel


class DatasetSummaryRequest(BaseModel):
    dataset_id: int


class DatasetSummaryResponse(BaseModel):
    summary: str

