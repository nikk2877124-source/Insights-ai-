from fastapi import FastAPI

from app.routers import dataset

app = FastAPI(
    title="InsightAI API",
    description="AI Business Intelligence Assistant",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Welcome to InsightAI 🚀"
    }


app.include_router(dataset.router)