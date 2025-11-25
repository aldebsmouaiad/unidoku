# core/charts.py
# Plotly-Radarplots für TD/OG

from typing import Optional

import plotly.graph_objects as go
import pandas as pd


def create_radar_ist_soll(df: pd.DataFrame, title: str) -> go.Figure:
    """
    Radarplot mit Ist- und Soll-Werten je Dimension.
    Erwartete Spalten: Code, Name, Ist, Soll
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="Keine Daten")
        return fig

    labels = [f"{c} – {n}" for c, n in zip(df["Code"], df["Name"])]
    ist_values = df["Ist"].fillna(0.0).tolist()
    soll_values = df["Soll"].fillna(0.0).tolist()

    labels_closed = labels + labels[:1]
    ist_closed = ist_values + ist_values[:1]
    soll_closed = soll_values + soll_values[:1]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=ist_closed,
            theta=labels_closed,
            fill="toself",
            name="Ist-Reifegrad",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=soll_closed,
            theta=labels_closed,
            fill="toself",
            name="Soll-Reifegrad",
            opacity=0.5,
        )
    )

    fig.update_layout(
        title=title,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[0, 1, 2, 3, 4, 5],
            )
        ),
        showlegend=True,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig
