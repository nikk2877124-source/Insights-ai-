from __future__ import annotations

from io import BytesIO
from typing import Any, Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from api.client import APIError
from components.metric_cards import metric_card
from utils.auth import ensure_client
from utils.session import set_selected_dataset, set_token, set_user


def page_title(title: str, subtitle: str | None = None) -> None:
    st.markdown(
        f"""
        <section class="page-title">
            <div>
                <h1>{title}</h1>
                {f'<p>{subtitle}</p>' if subtitle else ''}
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def glass_panel(title: str, body: str = "") -> None:
    st.markdown(
        f"""
        <div class="glass-panel">
            <div class="panel-title">{title}</div>
            {f'<div class="panel-body">{body}</div>' if body else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def handle_api_error(error: APIError) -> None:
    if error.status_code == 401:
        set_token(None)
        set_user(None)
        st.session_state["insightai_selected_page"] = "Login"
        st.error("Your session expired. Please log in again.")
        st.stop()

    if error.status_code == 0:
        st.error(error.detail)
        return

    if error.status_code in {400, 422}:
        st.warning(error.detail)
        return

    if error.status_code == 404:
        st.info(error.detail)
        return

    if error.status_code >= 500:
        st.error(f"Backend service error: {error.detail}")
        return

    st.error(error.detail)


def fetch_datasets() -> list[dict[str, Any]]:
    try:
        return ensure_client().list_datasets()
    except APIError as exc:
        handle_api_error(exc)
        return []


def dataset_label(dataset: dict[str, Any]) -> str:
    rows = dataset.get("total_rows")
    cols = dataset.get("total_columns")
    size = format_bytes(dataset.get("file_size") or 0)
    shape = f"{rows or 0} rows x {cols or 0} cols"
    return f"{dataset.get('filename', 'Dataset')} - {shape} - {size}"


def choose_dataset(label: str = "Dataset") -> dict[str, Any] | None:
    datasets = fetch_datasets()
    if not datasets:
        st.info("No datasets yet. Upload a CSV or Excel file to begin.")
        if st.button("Go to Upload Dataset", use_container_width=True):
            st.session_state["insightai_selected_page"] = "Upload Dataset"
            st.rerun()
        return None

    current = st.session_state.get("insightai_selected_dataset")
    current_id = current.get("id") if isinstance(current, dict) else None
    ids = [dataset.get("id") for dataset in datasets]
    default_index = ids.index(current_id) if current_id in ids else 0

    selected = st.selectbox(
        label,
        datasets,
        index=default_index,
        format_func=dataset_label,
    )
    set_selected_dataset(selected)
    return selected


def load_profile(dataset_id: int) -> dict[str, Any] | None:
    try:
        return ensure_client().get_dataset_profile(dataset_id)
    except APIError as exc:
        handle_api_error(exc)
        return None


def load_dataframe(dataset: dict[str, Any]) -> pd.DataFrame | None:
    try:
        payload = ensure_client().download_dataset(int(dataset["id"]))
    except APIError as exc:
        handle_api_error(exc)
        return None

    buffer = BytesIO(payload)
    filename = str(dataset.get("filename") or "").lower()
    file_type = str(dataset.get("file_type") or "").lower()
    try:
        if filename.endswith(".csv") or file_type == ".csv":
            return pd.read_csv(buffer)
        return pd.read_excel(buffer)
    except Exception:
        st.warning("The dataset was downloaded, but Streamlit could not preview it locally.")
        return None


def format_bytes(size: int | float) -> str:
    value = float(size or 0)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def grade_from_score(score: int | float | None) -> str:
    value = float(score or 0)
    if value >= 90:
        return "A"
    if value >= 80:
        return "B"
    if value >= 70:
        return "C"
    if value >= 60:
        return "D"
    return "F"


def render_kpis(items: Iterable[tuple[str, Any, str, str]]) -> None:
    item_list = list(items)
    if not item_list:
        return
    cols = st.columns(len(item_list))
    for col, (title, value, subtitle, icon) in zip(cols, item_list):
        with col:
            metric_card(title, value, subtitle, icon)


def dataset_kpis(dataset: dict[str, Any]) -> list[tuple[str, Any, str, str]]:
    score = dataset.get("quality_score") or 0
    return [
        ("Total Rows", f"{dataset.get('total_rows') or 0:,}", "Records available", "table"),
        ("Total Columns", f"{dataset.get('total_columns') or 0:,}", "Fields detected", "columns"),
        ("Missing Values", f"{dataset.get('missing_values') or 0:,}", "Null cells", "slash"),
        ("Duplicate Rows", f"{dataset.get('duplicate_rows') or 0:,}", "Repeated records", "copy"),
        ("Quality Score", f"{score}/100", "Higher is cleaner", "activity"),
        ("Dataset Grade", grade_from_score(score), str(dataset.get("status") or "Uploaded"), "award"),
    ]


def empty_chart(message: str) -> None:
    st.markdown(f'<div class="empty-chart">{message}</div>', unsafe_allow_html=True)


def style_plotly(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "rgba(255,255,255,0.82)"},
        margin={"l": 10, "r": 10, "t": 48, "b": 10},
        legend={"orientation": "h", "y": -0.2},
    )
    return fig


def missing_values_chart(profile_json: dict[str, Any] | None) -> None:
    columns = (((profile_json or {}).get("details") or {}).get("missing_values") or {}).get("columns") or {}
    rows = [{"column": name, "missing": data.get("count", 0)} for name, data in columns.items()]
    rows = [row for row in rows if row["missing"]]
    if not rows:
        empty_chart("No missing values detected.")
        return
    fig = px.bar(pd.DataFrame(rows), x="column", y="missing", title="Missing Values by Column", color="missing")
    st.plotly_chart(style_plotly(fig), use_container_width=True)


def data_types_chart(profile_json: dict[str, Any] | None) -> None:
    data_types = (((profile_json or {}).get("details") or {}).get("data_types") or {}).get("column_types") or {}
    if not data_types:
        empty_chart("Data type profile is not available.")
        return
    counts: dict[str, int] = {}
    for dtype in data_types.values():
        key = str(dtype)
        counts[key] = counts.get(key, 0) + 1
    fig = px.pie(
        names=list(counts.keys()),
        values=list(counts.values()),
        title="Column Data Types",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    st.plotly_chart(style_plotly(fig), use_container_width=True)


def outliers_chart(profile_json: dict[str, Any] | None) -> None:
    outliers = (((profile_json or {}).get("details") or {}).get("outliers") or {})
    rows = [
        {"column": name, "outliers": data.get("outlier_count", 0)}
        for name, data in outliers.items()
        if isinstance(data, dict) and data.get("outlier_count", 0)
    ]
    if not rows:
        empty_chart("No outliers detected in numeric columns.")
        return
    fig = px.bar(pd.DataFrame(rows), x="column", y="outliers", title="Outlier Counts", color="outliers")
    st.plotly_chart(style_plotly(fig), use_container_width=True)


def dataframe_charts(df: pd.DataFrame | None) -> None:
    if df is None or df.empty:
        empty_chart("Dataset preview charts are not available.")
        return

    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] >= 2:
        fig = px.imshow(numeric.corr(numeric_only=True), title="Correlation Matrix", color_continuous_scale="RdBu_r")
        st.plotly_chart(style_plotly(fig), use_container_width=True)
    else:
        empty_chart("Correlation requires at least two numeric columns.")

    if numeric.shape[1] >= 1:
        column = st.selectbox("Distribution column", list(numeric.columns), key="distribution_column")
        fig = px.histogram(df, x=column, title=f"Distribution: {column}", nbins=30)
        st.plotly_chart(style_plotly(fig), use_container_width=True)
    else:
        empty_chart("Distribution charts require a numeric column.")
