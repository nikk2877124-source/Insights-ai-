from __future__ import annotations

from typing import Any, Iterable

import streamlit as st


def chat_bubble(role: str, content: str) -> None:
    if role == "user":
        css = "bubble user-bubble"
    else:
        css = "bubble ai-bubble"

    st.markdown(
        f"""
        <div class='{css}'>
            <div class='bubble-role'>{role.capitalize()}</div>
            <div class='bubble-content'>{content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_history(items: Iterable[dict[str, Any]]) -> None:
    for it in items:
        chat_bubble("user", it.get("question", ""))
        chat_bubble("assistant", it.get("answer", ""))
