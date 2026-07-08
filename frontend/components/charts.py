from __future__ import annotations

from typing import Iterable, Optional

import pandas as pd
import plotly.express as px
import streamlit as st


def bar_missing_values(labels: list[str], values: list[int], title: str = "Missing Values") -> None:
    fig = px.bar(x=labels, y=values, title=title)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


def pie_data_types(labels: list[str], values: list[int], title: str = "Data Types") -> None:
    fig = px.pie(names=labels, values=values, title=title)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


def line_quality_trend(points: Iterable[tuple[str, float]], title: str = "Quality Trend") -> None:
    df = pd.DataFrame(list(points), columns=["label", "quality"])
    fig = px.line(df, x="label", y="quality", markers=True, title=title)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

