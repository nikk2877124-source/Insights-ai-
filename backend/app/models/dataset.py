from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # File Information
    filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), unique=True, index=True, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger, nullable=False)

    # Dataset Information
    total_rows = Column(Integer, nullable=True)
    total_columns = Column(Integer, nullable=True)

    # Data quality metrics
    missing_values = Column(Integer, nullable=True)
    duplicate_rows = Column(Integer, nullable=True)
    null_percentage = Column(Float, nullable=True)

    # AI Data Quality Score (0-100)
    quality_score = Column(Integer, default=100, nullable=False)

    # Dataset Status
    status = Column(
        String(30),
        default="uploaded",
        nullable=False
    )

    # Upload Information
    upload_time = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Foreign Key
    uploaded_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # Relationship
    owner = relationship(
        "User",
        back_populates="datasets"
    )