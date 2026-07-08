from __future__ import annotations

from typing import Any, Optional

import streamlit as st


def render_navbar(user: Optional[dict[str, Any]]) -> None:
    """Top navigation bar."""

    username = None
    if user:
        username = user.get("full_name") or user.get("email") or "User"

    st.markdown(
        """
        <div class="topbar">
            <div class="brand">
                <div class="brand-logo">✨</div>
                <div class="brand-name">InsightAI</div>
            </div>
            <div class="topbar-right">
                {user_block}
            </div>
        </div>
        """.format(
            user_block=(
                f"""
                <div class="user-chip">
                    <div class="user-avatar">{username[:1] if username else 'U'}</div>
                    <div class="user-meta">
                        <div class="user-name">{username}</div>
                        <div class="user-sub">JWT authenticated</div>
                    </div>
                </div>
                """
            )
            if username
            else ""
        ),
        unsafe_allow_html=True,
    )
