from __future__ import annotations

from typing import Any, Optional

import streamlit as st
from streamlit_option_menu import option_menu


PAGES: list[dict[str, str]] = [
    {"label": "Dashboard", "key": "Dashboard"},
    {"label": "Upload Dataset", "key": "Upload Dataset"},
    {"label": "Dataset Profile", "key": "Dataset Profile"},
    {"label": "AI Summary", "key": "AI Summary"},
    {"label": "AI Cleaning", "key": "AI Cleaning"},
    {"label": "Comparison", "key": "Comparison"},
    {"label": "Business Insights", "key": "Business Insights"},
    {"label": "AI Chat", "key": "AI Chat"},
    {"label": "Downloads", "key": "Downloads"},
    {"label": "Login", "key": "Login"},
]


def render_sidebar() -> str:
    """Render left sidebar navigation and return selected key."""

    with st.sidebar:
        st.caption("Navigation")
        choice = option_menu(
            menu_title=None,
            options=[p["label"] for p in PAGES],
            icons=[
                "house",
                "upload",
                "database",
                "sparkles",
                "broom",
                "bar-chart",
                "lightbulb",
                "chat",
                "download",
                "key",
            ],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0px"},
                "icon": {"color": "#A78BFA"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "0px",
                    "padding": "10px 12px",
                    "border-radius": "12px",
                },
                "nav-link-selected": {
                    "background-color": "rgba(79,70,229,0.25)",
                    "border": "1px solid rgba(124,58,237,0.35)",
                },
            },
        )

    return str(choice)
