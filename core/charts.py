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


def radar_ist_soll(
    df: pd.DataFrame,
    category: str,
    title: str = "",
    *,
    dark: bool = False,
) -> Optional[go.Figure]:
    """
    Erzeugt ein Radar-Diagramm (Ist vs Soll) für eine Kategorie (TD/OG).

    Erwartet Spalten:
      - code
      - name
      - ist_level
      - target_level
      - category

    dark: Theme-Schalter für Darkmode
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

    # Farbschema
    if category == "TD":
        ist_color = "#7AB0B4"   # teal
        soll_color = "#2ca02c"  # grün
    else:  # OG
        ist_color = "#1f77b4"   # blau
        soll_color = "#ff7f0e"  # orange

    # -------------------------
    # Theme Tokens (Light/Dark)
    # -------------------------
    red_ticks = "#d62728"  # rot wie Legende (0..5)

    if dark:
        title_color = "rgba(250,250,250,0.92)"        # TD-/OG-Titel heller
        angular_color = "rgba(250,250,250,0.88)"      # Achsenlabels heller
        grid_color = "rgba(255,255,255,0.14)"         # Grid heller
        axis_line = "rgba(255,255,255,0.22)"
        legend_bg = "rgba(15,23,42,0.85)"
        legend_border = "rgba(255,255,255,0.16)"
        legend_font_color = "rgba(250,250,250,0.92)"
        polar_bg = "rgba(255,255,255,0.02)"
    else:
        title_color = "rgba(0,0,0,0.88)"
        angular_color = "rgba(0,0,0,0.70)"
        grid_color = "rgba(0,0,0,0.15)"
        axis_line = "rgba(0,0,0,0.25)"
        legend_bg = "rgba(255,255,255,0.80)"
        legend_border = "rgba(0,0,0,0.15)"
        legend_font_color = "rgba(0,0,0,0.85)"
        polar_bg = "rgba(0,0,0,0)"

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
        # Titel (TD-/OG-Dimensionen) im Darkmode hell
        title=dict(
            text=title or "",
            x=0.0,
            xanchor="left",
            font=dict(color=title_color),
        ),

        showlegend=True,
        legend=dict(
            orientation="v",
            x=0.0,
            y=0.0,
            xanchor="left",
            yanchor="bottom",
            bgcolor=legend_bg,
            bordercolor=legend_border,
            borderwidth=1,
            font=dict(size=12, color=legend_font_color),
        ),

        dragmode=False,
        margin=dict(l=40, r=40, t=70, b=40),

        # Wichtig: NICHT "white" – transparent, damit Dark-Card-Hintergrund passt
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        polar=dict(
            bgcolor=polar_bg,

            radialaxis=dict(
                range=[0, 5],
                tickmode="array",
                tickvals=[0, 1, 2, 3, 4, 5],
                ticktext=["0", "1", "2", "3", "4", "5"],

                # 0..5 ROT wie Legende
                tickfont=dict(color=red_ticks, size=12),

                showgrid=True,
                gridcolor=grid_color,
                gridwidth=1,

                showline=False,
                ticks="",
                ticklen=0,
            ),

            angularaxis=dict(
                # Beschriftung (Codes+Namen) im Darkmode hell
                tickfont=dict(size=10, color=angular_color),
                rotation=90,
                direction="clockwise",
                gridcolor=grid_color,
                linecolor=axis_line,
                showline=True,
            ),
        ),
    )

    return fig

