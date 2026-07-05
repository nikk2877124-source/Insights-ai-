import os
import shutil
from uuid import uuid4

from fastapi import UploadFile

# Allowed file extensions
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# Upload folder
UPLOAD_FOLDER = "datasets/original"


def validate_file(file: UploadFile):
    """
    Check whether the uploaded file is supported.
    """

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Only CSV, XLSX and XLS files are allowed."
        )

    return extension


def generate_filename(filename: str):
    """
    Generate a unique filename.
    """

    unique_id = uuid4().hex

    return f"{unique_id}_{filename}"


def save_file(file: UploadFile):
    """
    Save the uploaded file locally.
    """

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    extension = validate_file(file)

    stored_filename = generate_filename(file.filename)

    file_path = os.path.join(
        UPLOAD_FOLDER,
        stored_filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "original_filename": file.filename,
        "stored_filename": stored_filename,
        "file_path": file_path,
        "file_type": extension,
        "file_size": os.path.getsize(file_path)
    }