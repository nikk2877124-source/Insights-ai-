from __future__ import annotations

import pandas as pd
import streamlit as st

from api.client import APIError
from utils.auth import ensure_client
from utils.ui import (
    choose_dataset,
    data_types_chart,
    dataset_kpis,
    format_bytes,
    handle_api_error,
    load_profile,
    missing_values_chart,
    outliers_chart,
    page_title,
    render_kpis,
)


def render_dataset() -> None:
    page_title("Dataset Profile", "Inspect schema, quality, missing values, duplicates, and memory usage.")

    dataset = choose_dataset()
    if not dataset:
        return

    render_kpis(dataset_kpis(dataset))

    profile = load_profile(int(dataset["id"]))
    profile_json = profile.get("profile_json") if profile else {}
    details = (profile_json or {}).get("details") or {}

    tab_summary, tab_missing, tab_stats, tab_download = st.tabs(["Summary", "Missing and Types", "Statistics", "Download"])

    with tab_summary:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("File size", format_bytes(dataset.get("file_size") or 0))
        with col_b:
            memory = (details.get("memory_usage") or {}).get("memory_usage_mb")
            st.metric("Memory usage", f"{memory or 0} MB")
        with col_c:
            st.metric("Null percentage", f"{dataset.get('null_percentage') or 0}%")

        health = details.get("dataset_health") or {}
        st.markdown("#### Dataset Health")
        st.write(health.get("status") or "No health status available.")
        if health.get("major_issues"):
            st.table(pd.DataFrame({"Major issues": health["major_issues"]}))
        if health.get("recommendations"):
            st.table(pd.DataFrame({"Recommendations": health["recommendations"]}))

    with tab_missing:
        col_a, col_b = st.columns(2)
        with col_a:
            missing_values_chart(profile_json)
        with col_b:
            data_types_chart(profile_json)
        outliers_chart(profile_json)

    with tab_stats:
        statistics = details.get("statistics") or {}
        if statistics:
            st.dataframe(pd.DataFrame(statistics).T, use_container_width=True)
        else:
            st.info("No numeric statistics are available for this dataset.")

        data_types = (details.get("data_types") or {}).get("column_types") or {}
        if data_types:
            st.markdown("#### Column Types")
            st.dataframe(
                pd.DataFrame({"column": list(data_types.keys()), "dtype": list(data_types.values())}),
                use_container_width=True,
                hide_index=True,
            )

    with tab_download:
        try:
            file_bytes = ensure_client().download_dataset(int(dataset["id"]))
            st.download_button(
                "Download Original Dataset",
                data=file_bytes,
                file_name=dataset.get("filename") or "dataset",
                mime="application/octet-stream",
                use_container_width=True,
            )
        except APIError as exc:
            handle_api_error(exc)
