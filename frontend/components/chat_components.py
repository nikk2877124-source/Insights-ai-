from __future__ import annotations

from html import escape
from typing import Any, Iterable

import streamlit as st


def chat_bubble(role: str, content: str) -> None:
    if role == "user":
        css = "bubble user-bubble"
    else:
        css = "bubble ai-bubble"

    safe_role = escape(str(role).capitalize())
    safe_content = escape(str(content))
    st.markdown(
        f"""
        <div class='{css}'>
            <div class='bubble-role'>{safe_role}</div>
            <div class='bubble-content'>{safe_content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_history(items: Iterable[dict[str, Any]]) -> None:
    for it in items:
        chat_bubble("user", it.get("question", ""))
        chat_bubble("assistant", it.get("answer", ""))
