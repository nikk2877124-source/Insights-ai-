from __future__ import annotations

import streamlit as st

from api.client import APIError
from components.chat_components import chat_bubble, render_chat_history
from components.loading import render_loading
from utils.auth import ensure_client
from utils.ui import choose_dataset, handle_api_error, page_title


def render_chat() -> None:
    page_title("AI Chat", "Ask questions about the selected dataset profile.")

    dataset = choose_dataset()
    if not dataset:
        return

    local_key = f"chat_local_{dataset['id']}"
    st.session_state.setdefault(local_key, [])

    controls = st.columns([1, 1, 4])
    if controls[0].button("Refresh", use_container_width=True):
        st.session_state[local_key] = []
    if controls[1].button("Clear", use_container_width=True):
        st.session_state[local_key] = []

    try:
        history = ensure_client().chat_history(int(dataset["id"]))
    except APIError:
        history = []

    st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
    if history:
        render_chat_history(history)
    for item in st.session_state[local_key]:
        chat_bubble(item["role"], item["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    question = st.chat_input("Ask about missing values, trends, quality risks, or business recommendations")
    if question:
        chat_bubble("user", question)
        render_loading("Thinking through the dataset profile...")
        try:
            answer = ensure_client().chat(int(dataset["id"]), question)
            st.session_state[local_key].extend(
                [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": answer},
                ]
            )
            st.rerun()
        except APIError as exc:
            handle_api_error(exc)
