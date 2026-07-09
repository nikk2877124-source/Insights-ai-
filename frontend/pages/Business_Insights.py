from __future__ import annotations

import streamlit as st

from api.client import APIError
from utils.auth import ensure_client
from utils.ui import choose_dataset, handle_api_error, load_profile, page_title


def render_business_insights() -> None:
    page_title("Business Insights", "Executive recommendations generated from profile metrics.")

    dataset = choose_dataset()
    if not dataset:
        return

    profile = load_profile(int(dataset["id"]))
    summary = ((profile or {}).get("profile_json") or {}).get("summary") or {}

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Quality score", summary.get("quality_score", dataset.get("quality_score", 0)))
    col_b.metric("Grade", summary.get("grade", "N/A"))
    col_c.metric("Status", summary.get("status", dataset.get("status", "Uploaded")))

    key = f"insights_{dataset['id']}"
    if st.button("Generate Business Insights", type="primary", use_container_width=True):
        try:
            with st.spinner("Generating executive insights with Ollama..."):
                st.session_state[key] = ensure_client().get_business_insights(int(dataset["id"]))
        except APIError as exc:
            handle_api_error(exc)

    if st.session_state.get(key):
        st.markdown("#### Executive Summary")
        st.markdown(st.session_state[key])
    else:
        st.info("Generate insights after selecting a dataset.")
