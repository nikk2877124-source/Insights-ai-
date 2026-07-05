from fastapi import APIRouter

router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"]
)


@router.get("/")
def test_dataset_router():
    return {
        "message": "Dataset Router Working Successfully!"
    }