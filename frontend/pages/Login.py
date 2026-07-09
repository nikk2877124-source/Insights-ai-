from __future__ import annotations

import streamlit as st

from api.client import APIError
from utils.auth import login, register
from utils.ui import handle_api_error, page_title


def render_login() -> None:
    page_title("InsightAI", "Local AI business intelligence for CSV and Excel analysis.")

    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        st.markdown(
            """
            <div class="hero-panel">
                <div class="eyebrow">LOCAL WORKSPACE</div>
                <h2>Analyze, clean, and question datasets with a FastAPI + Streamlit workflow.</h2>
                <p>Sign in to upload datasets, generate profiles, request AI summaries, run cleaning, and compare the results.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        tab_login, tab_register = st.tabs(["Login", "Register"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                try:
                    login(email=email.strip(), password=password)
                    st.session_state["insightai_selected_page"] = "Dashboard"
                    st.rerun()
                except APIError as exc:
                    handle_api_error(exc)
                except Exception as exc:
                    st.error(str(exc))

        with tab_register:
            with st.form("register_form"):
                full_name = st.text_input("Full name")
                email = st.text_input("Work email")
                password = st.text_input("Create password", type="password")
                submitted = st.form_submit_button("Create account", use_container_width=True)
            if submitted:
                try:
                    register(full_name=full_name.strip(), email=email.strip(), password=password)
                    st.session_state["insightai_selected_page"] = "Dashboard"
                    st.rerun()
                except APIError as exc:
                    handle_api_error(exc)
                except Exception as exc:
                    st.error(str(exc))
