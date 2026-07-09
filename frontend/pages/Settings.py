from __future__ import annotations

import streamlit as st

from api.client import APIError
from utils.auth import ensure_client, logout
from utils.config import get_base_url
from utils.session import get_session_user, get_token
from utils.ui import handle_api_error, page_title


def render_settings() -> None:
    page_title("Settings", "Local development status and account controls.")

    st.markdown("#### Connection")
    st.code(get_base_url())
    st.metric("Authentication", "Active" if get_token() else "Signed out")

    user = get_session_user() or {}
    st.markdown("#### Account")
    st.json(user)

    col_a, col_b = st.columns(2)
    if col_a.button("Check Backend", use_container_width=True):
        try:
            ensure_client().me()
            st.success("Backend and JWT authentication are reachable.")
        except APIError as exc:
            handle_api_error(exc)

    if col_b.button("Logout", use_container_width=True):
        logout()
        st.session_state["insightai_selected_page"] = "Login"
        st.rerun()
