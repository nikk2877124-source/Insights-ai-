from __future__ import annotations

import streamlit as st

from api.client import APIError
from components.chat_components import chat_bubble
from utils.auth import ensure_client
from utils.ui import choose_dataset, handle_api_error, page_title


def render_summary() -> None:
    page_title("AI Summary", "Generate a concise narrative summary from the dataset profile.")

    dataset = choose_dataset()
    if not dataset:
        return

    key = f"summary_{dataset['id']}"
    if st.button("Generate AI Summary", type="primary", use_container_width=True):
        try:
            with st.spinner("Asking Ollama for a dataset summary..."):
                st.session_state[key] = ensure_client().get_ai_summary(int(dataset["id"]))
        except APIError as exc:
            handle_api_error(exc)

    summary = st.session_state.get(key)
    if summary:
        chat_bubble("user", f"Summarize {dataset.get('filename')}.")
        chat_bubble("assistant", summary)
        st.markdown(summary)
    else:
        st.info("Generate a summary after selecting a dataset.")
