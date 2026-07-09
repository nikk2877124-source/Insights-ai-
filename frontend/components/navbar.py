from __future__ import annotations

from html import escape
from typing import Any, Optional

import streamlit as st


def render_navbar(user: Optional[dict[str, Any]]) -> None:
    """Top navigation bar."""

    username = None
    if user:
        username = user.get("full_name") or user.get("email") or "User"

    user_block = ""
    if username:
        safe_name = escape(str(username))
        user_block = f"""
            <div class="user-chip">
                <div class="user-avatar">{escape(safe_name[:1].upper())}</div>
                <div class="user-meta">
                    <div class="user-name">{safe_name}</div>
                    <div class="user-sub">JWT authenticated</div>
                </div>
            </div>
        """

    st.markdown(
        f"""
        <div class="topbar">
            <div class="brand">
                <div class="brand-logo">IA</div>
                <div class="brand-name">InsightAI</div>
            </div>
            <div class="topbar-right">
                {user_block}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
