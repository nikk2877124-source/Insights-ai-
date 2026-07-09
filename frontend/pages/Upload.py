from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from api.client import APIError
from utils.auth import ensure_client
from utils.session import set_selected_dataset
from utils.ui import handle_api_error, page_title


def _mime_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".csv"):
        return "text/csv"
    if name.endswith(".xls"):
        return "application/vnd.ms-excel"
    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _preview_file(file_name: str, file_bytes: bytes) -> pd.DataFrame | None:
    try:
        if file_name.lower().endswith(".csv"):
            return pd.read_csv(BytesIO(file_bytes))
        return pd.read_excel(BytesIO(file_bytes))
    except Exception:
        st.warning("This file could not be previewed locally, but you can still try uploading it.")
        return None


def render_upload() -> None:
    page_title("Upload Dataset", "Add a CSV or Excel file and generate its first quality profile.")

    st.markdown('<div class="upload-shell">', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Drop a CSV, XLS, or XLSX file here",
        type=["csv", "xls", "xlsx"],
        accept_multiple_files=False,
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded is None:
        st.info("Supported formats: CSV, XLS, XLSX.")
        return

    file_bytes = uploaded.getvalue()
    st.success(f"Ready to upload: {uploaded.name}")

    preview = _preview_file(uploaded.name, file_bytes)
    if preview is not None:
        st.markdown("#### Dataset Preview")
        st.dataframe(preview.head(50), use_container_width=True, hide_index=True)

    if st.button("Upload and Profile Dataset", type="primary", use_container_width=True):
        progress = st.progress(0, text="Validating file")
        try:
            progress.progress(30, text="Uploading to FastAPI")
            dataset = ensure_client().upload_dataset(uploaded.name, file_bytes, _mime_type(uploaded.name))
            progress.progress(75, text="Generating profile")
            set_selected_dataset(dataset)
            progress.progress(100, text="Upload complete")
            st.toast("Dataset uploaded successfully.")
            st.balloons()
            st.session_state["insightai_selected_page"] = "Dataset Profile"
            st.rerun()
        except APIError as exc:
            handle_api_error(exc)
