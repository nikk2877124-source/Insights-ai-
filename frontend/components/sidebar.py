from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

from utils.session import get_token


PAGES: list[dict[str, str | bool]] = [
    {"label": "Dashboard", "icon": "speedometer2", "auth": True},
    {"label": "Upload Dataset", "icon": "cloud-arrow-up", "auth": True},
    {"label": "Dataset Profile", "icon": "database", "auth": True},
    {"label": "AI Summary", "icon": "stars", "auth": True},
    {"label": "AI Cleaning", "icon": "magic", "auth": True},
    {"label": "Comparison", "icon": "bar-chart-line", "auth": True},
    {"label": "Business Insights", "icon": "graph-up-arrow", "auth": True},
    {"label": "AI Chat", "icon": "chat-dots", "auth": True},
    {"label": "Settings", "icon": "gear", "auth": True},
]


def render_sidebar() -> str:
    """Render the single custom sidebar navigation and return the selected page."""

    authenticated = bool(get_token())
    pages = PAGES.copy() if authenticated else [{"label": "Login", "icon": "person-lock", "auth": False}]
    if authenticated:
        pages.append({"label": "Logout", "icon": "box-arrow-right", "auth": True})

    labels = [str(page["label"]) for page in pages]
    icons = [str(page["icon"]) for page in pages]

    current = st.session_state.get("insightai_selected_page")
    if current not in labels:
        current = "Dashboard" if authenticated else "Login"
        st.session_state["insightai_selected_page"] = current

    with st.sidebar:
        st.markdown('<div class="sidebar-title">Workspace</div>', unsafe_allow_html=True)
        choice = option_menu(
            menu_title=None,
            options=labels,
            icons=icons,
            menu_icon="cast",
            default_index=labels.index(current),
            key="insightai_option_menu",
            styles={
                "container": {"padding": "0px", "background-color": "transparent"},
                "icon": {"color": "#7dd3fc", "font-size": "15px"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "2px 0px",
                    "padding": "10px 12px",
                    "border-radius": "8px",
                    "color": "rgba(255,255,255,0.76)",
                    "--hover-color": "rgba(255,255,255,0.08)",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, rgba(20,184,166,0.25), rgba(99,102,241,0.22))",
                    "border": "1px solid rgba(125,211,252,0.28)",
                    "color": "#ffffff",
                },
            },
        )

    st.session_state["insightai_selected_page"] = str(choice)
    return str(choice)
