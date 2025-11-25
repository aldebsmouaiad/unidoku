# core/charts.py
from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go


def radar_ist_soll(df: pd.DataFrame, category: str, title: str) -> Optional[go.Figure]:
    """
    Erstellt einen Radarplot (Ist vs. Soll) für eine Kategorie (TD / OG).

    :param df: DataFrame aus build_overview_table.
    :param category: "TD" oder "OG".
    :param title: Titel für den Plot.
    :return: Plotly-Figure oder None, wenn keine Daten.
    """
    # Nach Kategorie filtern und stabil nach Code sortieren
    sub = df[df["category"] == category].sort_values("code")
    if sub.empty:
        return None

    labels = sub["code"].tolist()
    ist = pd.to_numeric(sub["ist_level"], errors="coerce").fillna(0).tolist()
    soll = pd.to_numeric(sub["target_level"], errors="coerce").fillna(0).tolist()

    # Kurven schließen
    labels += labels[:1]
    ist += ist[:1]
    soll += soll[:1]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=ist,
            theta=labels,
            fill="toself",
            name="Ist-Reifegrad",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=soll,
            theta=labels,
            fill="toself",
            name="Soll-Reifegrad",
        )
    )

    fig.update_layout(
        title=title,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
            )
        ),
        showlegend=True,
    )

    return fig
