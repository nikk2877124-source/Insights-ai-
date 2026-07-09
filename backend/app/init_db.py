"""Database initialization script for local development."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def init_db() -> None:
    from app import models  # noqa: F401 - register all SQLAlchemy models
    from app.main import _sync_local_schema
    from app.core.database import Base, engine

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    _sync_local_schema()
    print("Database tables created successfully.")


if __name__ == "__main__":
    try:
        init_db()
    except Exception as exc:
        print(f"Error creating tables: {exc}")
        raise
