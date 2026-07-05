import pandas as pd

from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.utils.file_handler import save_file


def upload_dataset(
    db: Session,
    file,
    user_id: int
):
    """
    Upload a dataset and save its metadata.
    """

    # Save original file
    file_info = save_file(file)

    # Read dataset
    if file_info["file_type"] == ".csv":
        dataframe = pd.read_csv(file_info["file_path"])

    else:
        dataframe = pd.read_excel(file_info["file_path"])

    # Dataset information
    total_rows = len(dataframe)

    total_columns = len(dataframe.columns)

    # Initial quality score
    quality_score = 100

    # Create database object
    dataset = Dataset(
        filename=file_info["original_filename"],
        stored_filename=file_info["stored_filename"],
        file_path=file_info["file_path"],
        file_type=file_info["file_type"],
        file_size=file_info["file_size"],
        total_rows=total_rows,
        total_columns=total_columns,
        quality_score=quality_score,
        status="uploaded",
        uploaded_by=user_id
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset