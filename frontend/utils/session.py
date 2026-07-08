from __future__ import annotations

from typing import Any, Optional

import streamlit as st


TOKEN_KEY = "insightai_jwt"
USER_KEY = "insightai_user"
SELECTED_DATASET_KEY = "insightai_selected_dataset"


def init_session_state() -> None:
    """Initialize required Streamlit session keys."""
    st.session_state.setdefault(TOKEN_KEY, None)
    st.session_state.setdefault(USER_KEY, None)
    st.session_state.setdefault(SELECTED_DATASET_KEY, None)


def get_token() -> Optional[str]:
    return st.session_state.get(TOKEN_KEY)


def set_token(token: Optional[str]) -> None:
    st.session_state[TOKEN_KEY] = token


def set_user(user: Optional[dict[str, Any]]) -> None:
    st.session_state[USER_KEY] = user


def get_session_user() -> Optional[dict[str, Any]]:
    return st.session_state.get(USER_KEY)


def set_selected_dataset(dataset: Optional[dict[str, Any]]) -> None:
    st.session_state[SELECTED_DATASET_KEY] = dataset


def get_selected_dataset() -> Optional[dict[str, Any]]:
    return st.session_state.get(SELECTED_DATASET_KEY)

