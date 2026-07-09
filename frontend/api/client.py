from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

import requests
from requests import exceptions as request_exceptions


@dataclass
class APIError(Exception):
    """Raised when the API returns a non-2xx response."""

    status_code: int
    detail: str

    def __str__(self) -> str:  # pragma: no cover
        return f"APIError({self.status_code}): {self.detail}"


class APIClient:
    """REST API client for InsightAI frontend.

    Handles:
    - JWT auth header
    - request timeouts
    - consistent error parsing
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout_s: int = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.token = token
        self._sync_headers()

    def _sync_headers(self) -> None:
        headers: dict[str, str] = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.session.headers.update(headers)

    def set_token(self, token: Optional[str]) -> None:
        self.token = token
        # Clear any previous header (requests doesn't remove per-key automatically)
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        self._sync_headers()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout_s)

        try:
            resp = self.session.request(method, url, **kwargs)
        except request_exceptions.Timeout as exc:
            raise APIError(status_code=0, detail="The backend request timed out. Please try again.") from exc
        except request_exceptions.ConnectionError as exc:
            raise APIError(
                status_code=0,
                detail="The FastAPI backend is unavailable. Start it with: python -m uvicorn app.main:app --reload",
            ) from exc
        except request_exceptions.RequestException as exc:
            raise APIError(status_code=0, detail=f"Unable to reach the backend: {exc}") from exc

        if 200 <= resp.status_code < 300:
            if resp.headers.get("content-type", "").startswith("application/json"):
                return resp.json()
            return resp.content

        detail = None
        try:
            data = resp.json()
            detail = data.get("detail") if isinstance(data, dict) else None
        except Exception:
            detail = None

        if not detail:
            detail = resp.text or resp.reason
        raise APIError(status_code=resp.status_code, detail=str(detail))

    # -----------------
    # Auth
    # -----------------
    def login(self, email: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/login",
            json={"email": email, "password": password},
        )

    def register(self, full_name: str, email: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/register",
            json={"full_name": full_name, "email": email, "password": password},
        )

    def me(self) -> dict[str, Any]:
        return self._request("GET", "/auth/me")

    # -----------------
    # Datasets
    # -----------------
    def upload_dataset(self, file_name: str, file_bytes: bytes, file_type: str) -> dict[str, Any]:
        # FastAPI endpoint expects UploadFile (multipart)
        files = {
            "file": (file_name, file_bytes, file_type),
        }
        return self._request("POST", "/datasets/upload", files=files)

    def list_datasets(self) -> list[dict[str, Any]]:
        return self._request("GET", "/datasets/")

    def get_dataset(self, dataset_id: int) -> dict[str, Any]:
        return self._request("GET", f"/datasets/{dataset_id}")

    def get_dataset_profile(self, dataset_id: int) -> dict[str, Any]:
        return self._request("GET", f"/datasets/{dataset_id}/profile")

    def download_dataset(self, dataset_id: int) -> bytes:
        # For downloading, return bytes (caller decides file name)
        return self._request("GET", f"/datasets/{dataset_id}/download")

    # -----------------
    # AI: Summary / Cleaning recs / Business insights / Chat
    # -----------------
    def get_ai_summary(self, dataset_id: int) -> str:
        data = self._request(
            "POST",
            "/ai/dataset-summary",
            json={"dataset_id": dataset_id},
        )
        return data.get("summary", "")

    def get_cleaning_recommendations(self, dataset_id: int) -> str:
        data = self._request(
            "POST",
            "/ai/cleaning-recommendations",
            json={"dataset_id": dataset_id},
        )
        return data.get("recommendations", "")

    def interpret_cleaning_prompt(self, dataset_id: int, prompt: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/ai/interpret-prompt",
            json={"dataset_id": dataset_id, "prompt": prompt},
        )

    def clean_dataset(self, dataset_id: int, prompt: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/cleaning/start",
            json={"dataset_id": dataset_id, "prompt": prompt},
        )

    def get_cleaning_history(self) -> list[dict[str, Any]]:
        return self._request("GET", "/cleaning/history")

    def get_comparison(self, session_id: int) -> dict[str, Any]:
        return self._request("GET", f"/comparison/session/{session_id}")

    def get_business_insights(self, dataset_id: int) -> str:
        data = self._request(
            "POST",
            "/ai/business-insights",
            json={"dataset_id": dataset_id},
        )
        # Backend schema: {success: bool, insights: str}
        return data.get("insights", "")

    def chat(self, dataset_id: int, question: str) -> str:
        data = self._request(
            "POST",
            "/ai/chat",
            json={"dataset_id": dataset_id, "question": question},
        )
        return data.get("answer", "")

    def chat_history(self, dataset_id: int) -> list[dict[str, Any]]:
        data = self._request("GET", f"/ai/chat/history/{dataset_id}")
        return data.get("history", [])

    # -----------------
    # Cleaning downloads
    # -----------------
    def download_cleaning_result(self, session_id: int) -> bytes:
        return self._request("GET", f"/cleaning/download/{session_id}")

