# core/charts.py
from __future__ import annotations

import re
from typing import Optional

import pandas as pd
import plotly.graph_objects as go


def _natural_code_key(code: str):
    """
    Sortiert Codes wie TD1.2, TD1.10, OG2.1 "natürlich" nach Zahlen.
    """
    parts = re.split(r"(\d+)", str(code))
    key = []
    for p in parts:
        if p.isdigit():
            key.append(int(p))
        else:
            key.append(p)
    return tuple(key)


def after_dash(text: str) -> str:
    """
    Gibt nur den Teil nach dem ersten '-' zurück (getrimmt).
    Falls kein '-' vorhanden ist: gibt den Text getrimmt zurück.
    """
    s = "" if text is None else str(text)
    return s.split("-", 1)[1].strip() if "-" in s else s.strip()


def radar_ist_soll(df: pd.DataFrame, category: str, title: str = "") -> Optional[go.Figure]:
    """
    Erzeugt ein Radar-Diagramm (Ist vs Soll) für eine Kategorie (TD/OG).

    Erwartet Spalten:
      - code
      - name
      - ist_level
      - target_level
      - category
    """
    if df is None or df.empty:
        return None

    required = {"code", "name", "ist_level", "target_level", "category"}
    if not required.issubset(set(df.columns)):
        return None

    d = df[df["category"] == category].copy()
    if d.empty:
        return None

    # stabile Reihenfolge
    d = d.sort_values("code", key=lambda s: s.map(_natural_code_key))

    # Achsenbeschriftungen (wie Excel: Kürzel + Themenbereich)
    short_names = [after_dash(n) for n in d["name"]]
    theta = [f"{c}<br>{n}" for c, n in zip(d["code"], short_names)]

    ist = d["ist_level"].astype(float).tolist()
    soll = d["target_level"].astype(float).tolist()

    # Radar "schließen"
    theta_closed = theta + [theta[0]]
    ist_closed = ist + [ist[0]]
    soll_closed = soll + [soll[0]]

    # Farbschema wie im Screenshot
    if category == "TD":
        ist_color = "#7AB0B4"   # schwarz
        soll_color = "#2ca02c"  # grün
    else:  # OG
        ist_color = "#1f77b4"   # blau
        soll_color = "#ff7f0e"  # orange

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=ist_closed,
            theta=theta_closed,
            mode="lines",
            name="Ist-Reifegrad",
            line=dict(color=ist_color, width=2),
            hovertemplate="%{theta}<br>Ist: %{r:.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatterpolar(
            r=soll_closed,
            theta=theta_closed,
            mode="lines",
            name="Soll-Reifegrad",
            line=dict(color=soll_color, width=2),
            hovertemplate="%{theta}<br>Soll: %{r:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text=title or "", x=0.0, xanchor="left"),
        showlegend=True,
        legend=dict(
            orientation="v",
            x=0.0,
            y=0.0,
            xanchor="left",
            yanchor="bottom",
            bgcolor="rgba(255,255,255,0.80)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1,
            font=dict(size=12),
        ),
        dragmode=False,  # verhindert Drag-Zoom/Drag-Pan im Plot selbst
        margin=dict(l=40, r=40, t=70, b=40),
        paper_bgcolor="white",
        plot_bgcolor="white",
        polar=dict(
            radialaxis=dict(
                range=[0, 5],

                # Stufen 1..5 (ohne 0-Label)
                tickmode="array",
                tickvals=[0, 1, 2, 3, 4, 5],
                ticktext=["0", "1", "2", "3", "4", "5"],
                tickfont=dict(color="#d62728", size=12),

                # Stufen-Kreise beibehalten
                showgrid=True,
                gridcolor="rgba(0,0,0,0.15)",
                gridwidth=1,

                # Linie, auf der die Zahlen "sitzen", entfernen
                showline=False,

                # kleine Tick-Striche entfernen (Zahlen bleiben)
                ticks="",
                ticklen=0,
            ),
            angularaxis=dict(
                tickfont=dict(size=10, color="rgba(0,0,0,0.70)"),
                rotation=90,
                direction="clockwise",

                # Speichen (radiale Linien) kannst du optional ausdünnen:
                gridcolor="rgba(0,0,0,0.10)",
                linecolor="rgba(0,0,0,0.25)",
                showline=True,
            ),
        ),
    )

    return fig
