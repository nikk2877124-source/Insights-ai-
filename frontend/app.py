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
        # streamlit page routing is based on option-menu; we still allow login page.
        # The Login page will be available via navigation.
        require_auth(allow_login=True)

    selected_page = render_sidebar()

    # Lazy import page modules to avoid circular imports
    # NOTE: this repo currently does not yet contain the full `frontend/pages/*` modules
    # from the requested target structure, so we guard imports to avoid syntax/tooling errors.
    # Once the pages are created, replace this block with real page module imports.
    st.warning(
        "Frontend pages are not implemented yet. Build them to enable navigation."
    )



if __name__ == "__main__":
    main()

