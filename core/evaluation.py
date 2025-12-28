from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak


# --------- Scoring (an dein ANSWER_OPTIONS angelehnt) ----------
ANSWER_TO_SCORE = {
    "Nicht anwendbar": None,
    "Gar nicht": 0.0,
    "In ein paar Fällen": 0.25,
    "In den meisten Fällen": 0.75,
    "Vollständig": 1.0,
}


def _code_sort_key(code: str):
    import re
    c = (code or "").strip()
    m = re.match(r"^([A-Za-z]+)(\d+)(?:\.(\d+))?$", c)
    if not m:
        return (99, c, 999, 999)
    prefix = m.group(1).upper()
    major = int(m.group(2))
    minor = int(m.group(3) or 0)
    prefix_order = {"TD": 0, "OG": 1}.get(prefix, 50)
    return (prefix_order, prefix, major, minor)


def compute_results_df(
    model: Dict[str, Any],
    answers: Dict[str, str],
    meta: Dict[str, str],
    global_target_level: float,
    dimension_targets: Dict[str, float],
    priorities: Dict[str, Any] | None = None,
) -> pd.DataFrame:
    """
    Erzeugt Ergebnis-Tabelle:
    code, name, category, ist_level, target_level, gap, priority, action, timeframe

    IST-Logik (robust + simpel):
    - pro Stufe: Mittelwert der beantworteten Fragen (0..1), NA wird ignoriert
    - Dimension-Ist = Summe der Stufenscores (max 5.0)
    """
    priorities = priorities or {}

    rows = []
    dims = sorted(model.get("dimensions", []) or [], key=lambda d: _code_sort_key(str(d.get("code", ""))))

    target_label = (meta or {}).get("target_label", "")

    for dim in dims:
        code = str(dim.get("code", "")).strip()
        name = str(dim.get("name", "")).strip()
        cat = str(dim.get("category", "")).strip()

        # Target
        if target_label == "Eigenes Ziel":
            target = float(dimension_targets.get(code, global_target_level))
        else:
            target = float(global_target_level)

        # IST
        ist_total = 0.0
        for lvl in dim.get("levels", []) or []:
            qs = lvl.get("questions", []) or []
            scores = []
            for q in qs:
                qid = q.get("id")
                if not qid:
                    continue
                a = answers.get(qid)
                if a not in ANSWER_TO_SCORE:
                    continue
                s = ANSWER_TO_SCORE[a]
                if s is None:
                    continue
                scores.append(float(s))

            lvl_score = float(sum(scores) / len(scores)) if scores else 0.0
            ist_total += lvl_score

        ist_total = round(ist_total, 2)
        gap = round(target - ist_total, 2)

        # Priorisierung / Maßnahmen (robust)
        pr_val = priorities.get(code, {})
        if isinstance(pr_val, dict):
            priority = str(pr_val.get("priority", "") or "")
            action = str(pr_val.get("action", "") or pr_val.get("measure", "") or "")
            timeframe = str(pr_val.get("timeframe", "") or pr_val.get("horizon", "") or "")
        else:
            priority = ""
            action = str(pr_val or "")
            timeframe = ""

        rows.append(
            {
                "code": code,
                "name": name,
                "category": cat,
                "ist_level": ist_total,
                "target_level": round(target, 2),
                "gap": gap,
                "priority": priority,
                "action": action,
                "timeframe": timeframe,
            }
        )

    return pd.DataFrame(rows)


def _radar_data(df: pd.DataFrame, category: str) -> Tuple[List[str], List[float], List[float]]:
    sub = df[df["category"] == category].copy()
    sub = sub.sort_values("code", key=lambda s: s.map(_code_sort_key))
    labels = sub["code"].tolist()
    ist = sub["ist_level"].astype(float).tolist()
    tgt = sub["target_level"].astype(float).tolist()
    return labels, ist, tgt


def make_radar_fig(labels: List[str], ist: List[float], tgt: List[float], title: str):
    """
    Matplotlib Radar (0..5). Gibt Figure zurück.
    """
    if not labels:
        fig = plt.figure(figsize=(6, 5))
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, "Keine Daten", ha="center", va="center")
        ax.axis("off")
        return fig

    import math

    n = len(labels)
    angles = [2 * math.pi * i / n for i in range(n)]
    angles += angles[:1]

    ist_c = ist + ist[:1]
    tgt_c = tgt + tgt[:1]

    fig = plt.figure(figsize=(6, 5))
    ax = fig.add_subplot(111, polar=True)
    ax.set_title(title, pad=18, fontweight="bold")
    ax.set_ylim(0, 5)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=8)

    ax.plot(angles, ist_c, linewidth=2, label="Ist-Reifegrad")
    ax.plot(angles, tgt_c, linewidth=2, label="Soll-Reifegrad")
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.10), fontsize=8)

    return fig


def results_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def figs_to_png_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def build_results_pdf(
    meta: Dict[str, str],
    df: pd.DataFrame,
    td_png: bytes | None,
    og_png: bytes | None,
) -> bytes:
    """
    PDF (Landscape A4): Meta + Radar(s) + Ergebnis-Tabelle.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
    )

    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    normal = styles["BodyText"]

    story = []
    story.append(Paragraph("Gesamtübersicht – Reifegradmodell Technische Dokumentation", h1))
    story.append(Spacer(1, 8))

    org = meta.get("org", "-")
    area = meta.get("area", "-")
    assessor = meta.get("assessor", "-")
    date_str = meta.get("date_str", "-")
    target_label = meta.get("target_label", "-")

    story.append(
        Paragraph(
            f"<b>Organisation:</b> {org} &nbsp;&nbsp; <b>Bereich:</b> {area} &nbsp;&nbsp; "
            f"<b>Datum:</b> {date_str} &nbsp;&nbsp; <b>Ziel:</b> {target_label} &nbsp;&nbsp; "
            f"<b>Erhebung durch:</b> {assessor}",
            normal,
        )
    )
    story.append(Spacer(1, 12))

    story.append(Paragraph("Visualisierte Reifegrade", h2))
    story.append(Spacer(1, 6))

    imgs = []
    if td_png:
        imgs.append(RLImage(io.BytesIO(td_png), width=12.5 * cm, height=9.5 * cm))
    if og_png:
        imgs.append(RLImage(io.BytesIO(og_png), width=12.5 * cm, height=9.5 * cm))

    if imgs:
        if len(imgs) == 2:
            t = Table([[imgs[0], imgs[1]]], colWidths=[13.0 * cm, 13.0 * cm])
            t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
            story.append(t)
        else:
            story.append(imgs[0])

    story.append(Spacer(1, 12))
    story.append(Paragraph("Ergebnis in Tabellenform", h2))
    story.append(Spacer(1, 6))

    # Tabelle: lange Texte als Paragraph
    df2 = df.copy()
    df2 = df2.sort_values("code", key=lambda s: s.map(_code_sort_key))

    headers = ["code", "name", "category", "ist_level", "target_level", "gap", "priority", "action", "timeframe"]
    data = [headers]

    # Styles für Zellen
    cell_style = styles["BodyText"]
    cell_style.fontSize = 8

    for _, r in df2.iterrows():
        row = []
        for h in headers:
            val = "" if pd.isna(r[h]) else str(r[h])
            if h in ("name", "action"):
                row.append(Paragraph(val.replace("\n", "<br/>"), cell_style))
            else:
                row.append(Paragraph(val, cell_style))
        data.append(row)

    col_widths = [2.2 * cm, 9.0 * cm, 2.0 * cm, 2.4 * cm, 2.6 * cm, 2.0 * cm, 2.6 * cm, 8.0 * cm, 3.0 * cm]
    tbl = Table(data, colWidths=col_widths, repeatRows=1)

    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    story.append(tbl)
    doc.build(story)

    buf.seek(0)
    return buf.getvalue()
