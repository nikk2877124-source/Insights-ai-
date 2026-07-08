from __future__ import annotations

from typing import Optional

import streamlit as st


def ai_response_card(title: str, text: str) -> None:
    """Render a premium AI response/glass card."""
    st.markdown(
        f"""
        <div class="ai-card">
            <div class="ai-card-title">{title}</div>
            <div class="ai-card-body">
                {text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def markdown_in_card(title: str, markdown_text: str) -> None:
    st.markdown(
        f"""
        <div class="ai-card">
            <div class="ai-card-title">{title}</div>
            <div class="ai-card-body">
                <div class="ai-md">{markdown_text}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
