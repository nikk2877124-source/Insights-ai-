import os
from io import BytesIO

from fastapi import UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.services.dataset_services import upload_dataset


def test_upload_dataset_service_persists_metadata():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        file_bytes = b"id,name\n1,Alice\n2,Bob\n"
        upload_file = UploadFile(filename="sample.csv", file=BytesIO(file_bytes))

        dataset = upload_dataset(session, upload_file, user_id=1)

        assert dataset.filename == "sample.csv"
        assert dataset.file_type == ".csv"
        assert dataset.total_rows == 2
        assert dataset.total_columns == 2
        assert os.path.exists(dataset.file_path)
    finally:
        session.close()
