from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from api.client import APIError
from components.comparison_cards import comparison_kpi
from utils.auth import ensure_client
from utils.ui import handle_api_error, page_title, style_plotly


def render_comparison() -> None:
    page_title("Comparison", "Compare dataset quality before and after cleaning.")

    try:
        history = ensure_client().get_cleaning_history()
    except APIError as exc:
        handle_api_error(exc)
        return

    if not history:
        st.info("Run a cleaning session first to unlock before and after comparison.")
        if st.button("Go to AI Cleaning", use_container_width=True):
            st.session_state["insightai_selected_page"] = "AI Cleaning"
            st.rerun()
        return

    last_session_id = st.session_state.get("insightai_last_cleaning_session_id")
    ids = [item.get("id") for item in history]
    default_index = ids.index(last_session_id) if last_session_id in ids else 0
    selected = st.selectbox(
        "Cleaning session",
        history,
        index=default_index,
        format_func=lambda item: f"#{item.get('id')} - {item.get('dataset_name')} - {item.get('created_at')}",
    )

    try:
        comparison = ensure_client().get_comparison(int(selected["id"]))
    except APIError as exc:
        handle_api_error(exc)
        return

    before = comparison.get("before") or {}
    after = comparison.get("after") or {}
    improvements = comparison.get("improvements") or {}

    cols = st.columns(4)
    for col, label, key in zip(
        cols,
        ["Missing Values", "Duplicate Rows", "Outliers", "Quality Score"],
        ["missing_values", "duplicate_rows", "outlier_count", "quality_score"],
    ):
        with col:
            comparison_kpi(label, before.get(key, 0), after.get(key, 0))

    chart_rows = []
    for metric in ["missing_values", "duplicate_rows", "outlier_count", "quality_score"]:
        chart_rows.append({"metric": metric, "stage": "Before", "value": before.get(metric, 0)})
        chart_rows.append({"metric": metric, "stage": "After", "value": after.get(metric, 0)})
    fig = px.bar(pd.DataFrame(chart_rows), x="metric", y="value", color="stage", barmode="group", title="Before vs After")
    st.plotly_chart(style_plotly(fig), use_container_width=True)

    st.markdown("#### Improvements")
    st.dataframe(pd.DataFrame([improvements]), use_container_width=True, hide_index=True)

    try:
        cleaned = ensure_client().download_cleaning_result(int(selected["id"]))
        st.download_button(
            "Download Cleaned Dataset",
            data=cleaned,
            file_name=f"cleaned_session_{selected['id']}.csv",
            mime="application/octet-stream",
            use_container_width=True,
        )
    except APIError as exc:
        handle_api_error(exc)
