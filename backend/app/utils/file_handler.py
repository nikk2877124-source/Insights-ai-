import os
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings

# Allowed file extensions
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# Upload folder
UPLOAD_FOLDER = Path(__file__).resolve().parents[2] / "datasets" / "original"


def validate_file(file: UploadFile):
    """Check whether the uploaded file is supported."""
    if not file.filename:
        raise ValueError("No file selected.")

    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Only CSV, XLSX and XLS files are allowed.")

    return extension


def generate_filename(filename: str):
    """Generate a unique filename for storage."""
    unique_id = uuid4().hex
    return f"{unique_id}_{filename}"


def save_file(file: UploadFile):
    """Save an uploaded dataset locally after validating its size and format."""
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    extension = validate_file(file)

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size == 0:
        raise ValueError("Uploaded file is empty.")
    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise ValueError("File exceeds the maximum supported size.")

    stored_filename = generate_filename(file.filename)
    file_path = UPLOAD_FOLDER / stored_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "original_filename": file.filename,
        "stored_filename": stored_filename,
        "file_path": str(file_path),
        "file_type": extension,
        "file_size": os.path.getsize(file_path),
    }