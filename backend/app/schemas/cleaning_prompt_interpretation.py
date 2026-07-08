from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class InterpretCleaningPromptRequest(BaseModel):
    dataset_id: int
    prompt: str


class CleaningOperation(BaseModel):
    """An operation descriptor intended for the CleaningPipeline.

    This is intentionally aligned with the supported operation names used
    by CleaningPipeline/PromptParser/CleaningService.
    """

    operation: str
    column: str | None = None


class InterpretCleaningPromptResponse(BaseModel):
    success: bool
    operations: list[CleaningOperation]

    # Optional: include validation errors without failing the whole request.
    # Kept generic to avoid breaking API consumers.
    errors: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

