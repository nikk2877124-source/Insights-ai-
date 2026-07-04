from fastapi import FastAPI

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
    
