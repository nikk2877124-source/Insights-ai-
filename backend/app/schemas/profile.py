"""Pydantic schemas for dataset profiling.

This module defines response models used by the AI Data Profiling module.
We keep multiple schemas because different endpoints require different levels
of detail (list vs. detail vs. immediate analyze response).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ProfileResponse(BaseModel):
    """Return the complete information for one analyzed dataset profile."""

    id: int
    dataset_id: int
    profile_version: int
    total_rows: int
    total_columns: int
    quality_score: float
    profile_json: dict[str, Any]
    ai_summary: str
    created_at: datetime

    # Enable ORM mode (SQLAlchemy model -> schema)
    model_config = ConfigDict(from_attributes=True)


class ProfileSummary(BaseModel):
    """Lightweight profile info used when listing profile versions."""

    id: int
    profile_version: int
    quality_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileAnalyzeResponse(BaseModel):
    """Immediate response after the dataset analysis job is triggered."""

    message: str
    profile_id: int
    quality_score: float
    total_rows: int
    total_columns: int

