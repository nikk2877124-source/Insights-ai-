from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import Base, engine
from app import models  # noqa: F401 - ensure SQLAlchemy models are registered
from app.routers import ai, auth, cleaning, comparison, dataset


app = FastAPI(
    title="InsightAI API",
    description="AI Business Intelligence Assistant",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
)


@app.get("/")
def root():
    return {"message": "Welcome to InsightAI"}


@app.on_event("startup")
def startup() -> None:
    """Initialize local development database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        _sync_local_schema()
    except SQLAlchemyError as exc:
        raise RuntimeError(
            "Database is unavailable or misconfigured. Check DATABASE_URL and make sure MySQL is running."
        ) from exc


def _sync_local_schema() -> None:
    """Add missing local-dev columns after model changes.

    SQLAlchemy create_all creates missing tables only; it does not migrate older
    tables. This project is local-development only, so a small additive sync is
    enough to keep existing MySQL/SQLite databases usable without Alembic.
    """

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "datasets" not in table_names:
        return

    columns = {column["name"] for column in inspector.get_columns("datasets")}
    dialect = engine.dialect.name
    quote_l = "`" if dialect == "mysql" else '"'
    quote_r = "`" if dialect == "mysql" else '"'

    def q(identifier: str) -> str:
        return f"{quote_l}{identifier}{quote_r}"

    missing_dataset_columns = {
        "total_rows": "INTEGER NULL",
        "total_columns": "INTEGER NULL",
        "missing_values": "INTEGER NULL",
        "duplicate_rows": "INTEGER NULL",
        "null_percentage": "FLOAT NULL",
        "quality_score": "INTEGER NOT NULL DEFAULT 100",
        "status": "VARCHAR(30) NOT NULL DEFAULT 'uploaded'",
    }

    with engine.begin() as connection:
        for column_name, definition in missing_dataset_columns.items():
            if column_name not in columns:
                connection.execute(text(f"ALTER TABLE {q('datasets')} ADD COLUMN {q(column_name)} {definition}"))


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
