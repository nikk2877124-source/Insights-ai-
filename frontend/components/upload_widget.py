from __future__ import annotations

from typing import Any

import streamlit as st


def upload_widget() -> tuple[Any, str]:
    """Drag/drop upload widget.

    Returns: (uploaded_file, file_type)
    """

    st.markdown("### Upload your dataset")
    uploaded = st.file_uploader(
        "Drop CSV or Excel file here",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=False,
    )

    file_type = "text/csv"
    if uploaded is not None:
        name = uploaded.name.lower()
        if name.endswith(".csv"):
            file_type = "text/csv"
        else:
            file_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return uploaded, file_type
