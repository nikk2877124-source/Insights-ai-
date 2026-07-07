from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class DatasetProfile(Base):
    __tablename__ = "dataset_profiles"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key to the parent dataset
    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False,
        index=True,
    )

    # Profile versioning
    profile_version = Column(Integer, default=1, nullable=False)

    # Dataset summary metrics
    total_rows = Column(Integer, nullable=True)
    total_columns = Column(Integer, nullable=True)
    quality_score = Column(Float, default=0.0, nullable=False)

    # Stored profiling payload and AI summary
    profile_json = Column(JSON, nullable=True)
    ai_summary = Column(Text, nullable=True)

    # Audit information
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to the parent dataset
    dataset = relationship(
        "Dataset",
        back_populates="profiles"
    )
