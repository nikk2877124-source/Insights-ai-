from datetime import datetime
from pydantic import BaseModel


class DatasetResponse(BaseModel):
    id: int
    filename: str
    stored_filename: str
    file_path: str
    file_type: str
    file_size: int
    total_rows: int | None = None
    total_columns: int | None = None
    quality_score: int
    status: str
    upload_time: datetime
    uploaded_by: int

    class Config:
        from_attributes = True