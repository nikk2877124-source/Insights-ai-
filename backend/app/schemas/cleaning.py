"""Pydantic schemas for dataset cleaning operations.

These schemas are intended to be used by FastAPI endpoints that start a
"cleaning" operation (prompt-driven) and return both immediate and historical
results.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CleaningRequest(BaseModel):
    """Request payload for starting a dataset cleaning operation."""

    dataset_id: int = Field(..., description="ID of the dataset to clean.")
    prompt: str = Field(
        ...,
        min_length=1,
        description="Cleaning instruction/prompt that guides the operation.",
    )


class CleaningResponse(BaseModel):
    """Response payload after a cleaning operation finishes."""

    success: bool = Field(..., description="Whether the cleaning operation succeeded.")
    message: str = Field(..., description="Human-readable status message.")
    session_id: int = Field(..., description="ID of the cleaning session record.")

    quality_before: float = Field(
        ..., description="Quality metric value before the cleaning operation."
    )
    quality_after: float = Field(
        ..., description="Quality metric value after the cleaning operation."
    )

    model_config = ConfigDict(from_attributes=True)


class CleaningHistoryResponse(BaseModel):
    """Represents a single historical cleaning operation for a dataset."""

    id: int = Field(..., description="Cleaning session ID.")
    dataset_name: str = Field(..., description="Name of the dataset." )
    operation: str = Field(
        ...,
        description="Cleaning operation name/type (e.g., the algorithm or workflow step).",
    )
    prompt: str = Field(..., description="Prompt used for the cleaning operation.")

    quality_before: float = Field(
        ..., description="Quality metric value before the cleaning operation."
    )
    quality_after: float = Field(
        ..., description="Quality metric value after the cleaning operation."
    )

    created_at: datetime = Field(..., description="When the cleaning session was created.")

    model_config = ConfigDict(from_attributes=True)

