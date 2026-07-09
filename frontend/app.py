from __future__ import annotations

import streamlit as st

from components.navbar import render_navbar
from components.sidebar import render_sidebar
from pages.AI_Chat import render_chat
from pages.AI_Cleaning import render_cleaning
from pages.AI_Summary import render_summary
from pages.Business_Insights import render_business_insights
from pages.Comparison import render_comparison
from pages.Dashboard import render_dashboard
from pages.Dataset import render_dataset
from pages.Login import render_login
from pages.Settings import render_settings
from pages.Upload import render_upload
from utils.auth import logout, require_auth
from utils.session import get_session_user, init_session_state


st.set_page_config(
    page_title="InsightAI",
    page_icon="IA",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    """Main Streamlit application with one custom navigation system."""

    init_session_state()
    user = get_session_user()

    try:
        with open("assets/styles.css", "r", encoding="utf-8") as css:
            st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Custom theme file was not found.")

    render_navbar(user=user)
    selected_page = render_sidebar()

    if selected_page == "Login":
        render_login()
        return

    if selected_page == "Logout":
        logout()
        st.session_state["insightai_selected_page"] = "Login"
        st.rerun()

    require_auth(allow_login=False)

    renderers = {
        "Dashboard": render_dashboard,
        "Upload Dataset": render_upload,
        "Dataset Profile": render_dataset,
        "AI Summary": render_summary,
        "AI Cleaning": render_cleaning,
        "Comparison": render_comparison,
        "Business Insights": render_business_insights,
        "AI Chat": render_chat,
        "Settings": render_settings,
    }

    renderers.get(selected_page, render_dashboard)()


if __name__ == "__main__":
    main()
