from __future__ import annotations

import streamlit as st


def comparison_kpi(label: str, before: float | int, after: float | int) -> None:
    delta = None
    try:
        delta = float(after) - float(before)
    except Exception:
        delta = None

    delta_str = ""
    if delta is not None:
        sign = "+" if delta >= 0 else ""
        delta_str = f"delta {sign}{delta:.2f}"

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-top">
                <div class="metric-title">{label}</div>
            </div>
            <div class="metric-value">{before} to {after}</div>
            <div class="metric-sub">{delta_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
