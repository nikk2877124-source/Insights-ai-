from __future__ import annotations

import streamlit as st

from utils.ui import (
    choose_dataset,
    data_types_chart,
    dataframe_charts,
    dataset_kpis,
    load_dataframe,
    load_profile,
    missing_values_chart,
    outliers_chart,
    page_title,
    render_kpis,
)


def render_dashboard() -> None:
    page_title("Dashboard", "A live quality overview for the selected dataset.")

    dataset = choose_dataset()
    if not dataset:
        return

    render_kpis(dataset_kpis(dataset))

    profile = load_profile(int(dataset["id"]))
    profile_json = profile.get("profile_json") if profile else None

    tab_overview, tab_quality, tab_numeric = st.tabs(["Quality", "Structure", "Numeric Analysis"])
    with tab_overview:
        col_a, col_b = st.columns(2)
        with col_a:
            missing_values_chart(profile_json)
        with col_b:
            outliers_chart(profile_json)

    with tab_quality:
        data_types_chart(profile_json)
        if profile_json:
            health = (((profile_json.get("details") or {}).get("dataset_health")) or {})
            issues = health.get("major_issues") or []
            recommendations = health.get("recommendations") or []
            st.markdown("#### Dataset Health")
            st.write(health.get("status") or "No health status available.")
            if issues:
                st.markdown("#### Major Issues")
                st.table({"Issue": issues})
            if recommendations:
                st.markdown("#### Recommended Next Steps")
                st.table({"Recommendation": recommendations})

    with tab_numeric:
        df = load_dataframe(dataset)
        dataframe_charts(df)
