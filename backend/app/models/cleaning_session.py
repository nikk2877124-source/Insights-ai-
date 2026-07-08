from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class CleaningSession(Base):
    __tablename__ = "cleaning_sessions"

    id = Column(Integer, primary_key=True, index=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    original_file = Column(String(255), nullable=False)
    original_file_path = Column(String(500), nullable=False)

    cleaned_file = Column(String(255), nullable=True)
    cleaned_file_path = Column(String(500), nullable=True)

    prompt = Column(Text, nullable=False)
    operation = Column(String(100), nullable=False)

    rows_before = Column(Integer, nullable=True)
    rows_after = Column(Integer, nullable=True)

    quality_before = Column(Float, nullable=True)
    quality_after = Column(Float, nullable=True)

    status = Column(String(30), default="pending", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    dataset = relationship(
        "Dataset",
        back_populates="cleaning_sessions",
    )

    user = relationship(
        "User",
        back_populates="cleaning_sessions",
    )

