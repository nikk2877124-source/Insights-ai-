from __future__ import annotations

import pandas as pd
import streamlit as st

from api.client import APIError
from utils.auth import ensure_client
from utils.ui import choose_dataset, handle_api_error, page_title


def render_cleaning() -> None:
    page_title("AI Cleaning", "Review recommendations, choose operations, and execute a cleaning session.")

    dataset = choose_dataset()
    if not dataset:
        return

    rec_key = f"cleaning_recs_{dataset['id']}"

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("Get Cleaning Recommendations", use_container_width=True):
            try:
                with st.spinner("Generating cleaning recommendations..."):
                    st.session_state[rec_key] = ensure_client().get_cleaning_recommendations(int(dataset["id"]))
            except APIError as exc:
                handle_api_error(exc)
    with col_b:
        if st.button("Open Comparison", use_container_width=True):
            st.session_state["insightai_selected_page"] = "Comparison"
            st.rerun()

    if st.session_state.get(rec_key):
        st.markdown("#### Cleaning Recommendations")
        st.markdown(st.session_state[rec_key])

    prompt = st.text_area(
        "Cleaning instruction",
        value="remove_duplicates",
        height=120,
        help="Examples: remove_duplicates, drop_missing_rows, fill_missing_mean column=amount",
    )

    action_a, action_b = st.columns(2)
    with action_a:
        if st.button("Preview Selected Operations", use_container_width=True):
            try:
                result = ensure_client().interpret_cleaning_prompt(int(dataset["id"]), prompt)
                operations = result.get("operations") or []
                errors = result.get("errors") or []
                if operations:
                    st.dataframe(pd.DataFrame(operations), use_container_width=True, hide_index=True)
                if errors:
                    st.warning("; ".join(errors))
                if not operations and not errors:
                    st.info("No operations were inferred from the prompt.")
            except APIError as exc:
                handle_api_error(exc)

    with action_b:
        if st.button("Execute Cleaning", type="primary", use_container_width=True):
            progress = st.progress(0, text="Preparing cleaning job")
            try:
                progress.progress(35, text="Applying operations")
                result = ensure_client().clean_dataset(int(dataset["id"]), prompt)
                progress.progress(100, text="Cleaning complete")
                st.session_state["insightai_last_cleaning_session_id"] = result.get("session_id")
                st.success(result.get("message", "Cleaning completed."))
                st.metric("Quality before", result.get("quality_before", 0))
                st.metric("Quality after", result.get("quality_after", 0))
            except APIError as exc:
                handle_api_error(exc)

    st.markdown("#### Cleaning History")
    try:
        history = ensure_client().get_cleaning_history()
        if history:
            st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
        else:
            st.info("No cleaning sessions have been run yet.")
    except APIError as exc:
        handle_api_error(exc)
