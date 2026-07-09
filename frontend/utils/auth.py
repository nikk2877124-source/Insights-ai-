from __future__ import annotations

from typing import Optional

import streamlit as st

from api.client import APIClient, APIError
from utils.config import get_base_url
from utils.session import get_token, set_token, set_user


def require_auth(allow_login: bool = False) -> None:
    """Gate protected pages.

    If not authenticated, either show a login CTA or stop rendering.
    """

    token = get_token()
    if token:
        return

    if allow_login:
        st.info("Please log in to continue.")
        return

    st.error("You must be logged in to access this page.")
    st.stop()


def ensure_client() -> APIClient:
    return APIClient(base_url=get_base_url(), token=get_token())


def login(email: str, password: str) -> None:
    client = ensure_client()
    data = client.login(email=email, password=password)

    token = data.get("access_token")
    if not token:
        raise RuntimeError("No access_token returned from backend")

    set_token(token)

    # Load /me profile for better UI
    try:
        me = client.me()
        set_user(me)
    except APIError:
        set_user(None)


def register(full_name: str, email: str, password: str) -> None:
    client = ensure_client()
    # Register endpoint returns message + user
    client.register(full_name=full_name, email=email, password=password)

    # Auto login after register
    login(email=email, password=password)


def logout() -> None:
    set_token(None)
    set_user(None)

