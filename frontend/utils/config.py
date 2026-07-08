from __future__ import annotations

import os


def get_base_url() -> str:
    """Return FastAPI base URL.

    You can override via environment variable:
    - INSIGHTAI_API_BASE_URL

    Default: http://localhost:8000
    """

    return os.getenv("INSIGHTAI_API_BASE_URL", "http://localhost:8000").rstrip("/")

