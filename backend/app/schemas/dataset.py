from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetResponse(BaseModel):
    id: int
    filename: str
    stored_filename: str
    file_path: str
    file_type: str
    file_size: int
    total_rows: int | None = None
    total_columns: int | None = None
    missing_values: int | None = None
    duplicate_rows: int | None = None
    null_percentage: float | None = None
    quality_score: int
    status: str
    upload_time: datetime
    uploaded_by: int

    model_config = ConfigDict(from_attributes=True)