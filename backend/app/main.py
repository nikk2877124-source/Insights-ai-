from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.routers import auth, dataset, cleaning
from app.routers import ai
from app.routers import comparison

app = FastAPI(
    title="InsightAI API",
    description="AI Business Intelligence Assistant",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
)


@app.get("/")
def root():
    return {"message": "Welcome to InsightAI 🚀"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
app.include_router(auth.router)
app.include_router(dataset.router)
app.include_router(cleaning.router)
app.include_router(ai.router)
app.include_router(comparison.router)

