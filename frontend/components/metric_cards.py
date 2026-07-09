from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st


def metric_card(title: str, value: Any, subtitle: str | None = None, icon: str = "") -> None:
    safe_title = escape(str(title))
    safe_value = escape(str(value))
    safe_subtitle = escape(str(subtitle or ""))
    safe_icon = escape(str(icon or ""))
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-top">
                <div class="metric-icon">{safe_icon}</div>
                <div class="metric-title">{safe_title}</div>
            </div>
            <div class="metric-value">{safe_value}</div>
            {f'<div class="metric-sub">{safe_subtitle}</div>' if safe_subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )
