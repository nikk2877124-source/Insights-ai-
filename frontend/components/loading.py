from __future__ import annotations

import streamlit as st


def render_loading(message: str = "Working...") -> None:
    """Premium loading indicator."""
    st.markdown(
        f"""
        <div class="loading-wrap">
            <div class="loader"></div>
            <div class="loading-text">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
