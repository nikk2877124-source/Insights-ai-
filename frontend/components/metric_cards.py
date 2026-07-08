from __future__ import annotations

from typing import Any

import streamlit as st


def metric_card(title: str, value: Any, subtitle: str | None = None, icon: str = "") -> None:
    subtitle = subtitle or ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-top">
                <div class="metric-icon">{icon}</div>
                <div class="metric-title">{title}</div>
            </div>
            <div class="metric-value">{value}</div>
            {f'<div class="metric-sub">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )
