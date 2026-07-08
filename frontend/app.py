import streamlit as st

from .components.navbar import render_navbar
from .components.sidebar import render_sidebar
from .utils.auth import require_auth
from .utils.session import get_session_user, init_session_state



st.set_page_config(
    page_title="InsightAI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    """Streamlit UI entrypoint (removed Streamlit agent behavior).

    This project’s UI pages are not wired; keep the file stable but do not
    perform any agent-like routing.
    """
    init_session_state()

    # Load user from JWT (if present)
    user = get_session_user()

    # Theme: include custom CSS
    st.markdown(
        """
        <style>
        @import url("assets/styles.css");
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Top + left navigation
    render_navbar(user=user)

    # Gate protected content
    if not user:
        require_auth(allow_login=True)

    # Pages are intentionally not rendered in this repo snapshot.
    # Remove Streamlit “agent”/routing behavior.
    st.info("UI pages are not wired in this repository. Use backend APIs for local testing.")


if __name__ == "__main__":
    main()

