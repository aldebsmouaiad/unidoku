# /workspaces/unidoku/core/exporter.py
from __future__ import annotations

import io
import os
import re
import math
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import pandas as pd

# Optional imports (App soll nicht crashen, wenn Paket fehlt)
try:
    from fpdf import FPDF, FontFace  # fpdf2
except Exception:  # pragma: no cover
    FPDF = None
    FontFace = None

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None


def after_dash(text: str) -> str:
    """Nur den Teil nach dem ersten '-' zurückgeben (getrimmt)."""
    s = "" if text is None else str(text)
    return s.split("-", 1)[1].strip() if "-" in s else s.strip()


def _natural_code_key(code: str):
    """Natürliche Sortierung für Codes wie TD1.2, TD1.10."""
    parts = re.split(r"(\d+)", str(code))
    key = []
    for p in parts:
        key.append(int(p) if p.isdigit() else p)
    return tuple(key)


def df_results_for_export(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Normalisiert Ergebnis-DF für Anzeige/Export.
    Erwartet typischerweise: code, name, category, ist_level, target_level, gap, priority, action, timeframe
    """
    d = df_raw.copy()

    # Robust: fehlende Spalten auffüllen
    for col in ["code", "name", "category", "ist_level", "target_level", "gap", "priority", "action", "timeframe"]:
        if col not in d.columns:
            d[col] = ""

    d["Themenbereich"] = d["name"].apply(after_dash)

    out = d.rename(
        columns={
            "code": "Kürzel",
            "category": "Kategorie",
            "ist_level": "Ist-Reifegrad",
            "target_level": "Soll-Reifegrad",
            "gap": "Gap",
            "priority": "Priorität",
            "action": "Maßnahme",
            "timeframe": "Zeitraum",
        }
    )

    # Reihung
    cols = [
        "Kürzel",
        "Themenbereich",
        "Kategorie",
        "Ist-Reifegrad",
        "Soll-Reifegrad",
        "Gap",
        "Priorität",
        "Maßnahme",
        "Zeitraum",
    ]
    out = out[cols]

    # Sortierung nach Kürzel
    out = out.sort_values("Kürzel", key=lambda s: s.map(_natural_code_key))

    return out


def make_csv_bytes(df_export: pd.DataFrame) -> bytes:
    """
    CSV für Excel (DE) am besten mit ';' und UTF-8-SIG.
    """
    return df_export.to_csv(index=False, sep=";").encode("utf-8-sig")


def _find_font_paths() -> Tuple[Optional[str], Optional[str]]:
    """
    Versucht eine Unicode-fähige Schrift zu finden.
    Linux: DejaVu ist typischerweise vorhanden.
    Optional: du kannst eigene Fonts im Projekt ablegen (assets/fonts/...).
    """
    candidates = [
        ("assets/fonts/DejaVuSans.ttf", "assets/fonts/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    for regular, bold in candidates:
        if os.path.exists(regular) and os.path.exists(bold):
            return regular, bold
    return None, None


def _render_radar_png(df_export: pd.DataFrame, category: str, title: str) -> io.BytesIO:
    """
    Matplotlib-Radar als PNG (BytesIO).
    """
    if plt is None:
        raise RuntimeError("matplotlib ist nicht installiert. Bitte 'pip install matplotlib' ausführen.")

    d = df_export[df_export["Kategorie"] == category].copy()
    if d.empty:
        # leeres Bild (stabil)
        buf = io.BytesIO()
        fig = plt.figure(figsize=(6, 4))
        fig.text(0.5, 0.5, f"Keine Daten für {category}", ha="center", va="center")
        plt.axis("off")
        fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf

    d = d.sort_values("Kürzel", key=lambda s: s.map(_natural_code_key))
    labels = [f'{r["Kürzel"]}\n{r["Themenbereich"]}' for _, r in d.iterrows()]

    ist = [float(x) for x in d["Ist-Reifegrad"].tolist()]
    soll = [float(x) for x in d["Soll-Reifegrad"].tolist()]

    n = len(labels)
    angles = [2 * math.pi * i / n for i in range(n)]
    angles += angles[:1]
    ist_closed = ist + ist[:1]
    soll_closed = soll + soll[:1]

    # Farben wie bei dir: TD (Ist schwarz, Soll grün), OG (Ist blau, Soll orange)
    if category == "TD":
        c_ist = "#000000"
        c_soll = "#2ca02c"
    else:
        c_ist = "#1f77b4"
        c_soll = "#ff7f0e"

    fig = plt.figure(figsize=(6.2, 5.2))
    ax = plt.subplot(111, polar=True)
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=8)

    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], color="#d62728", fontsize=9)
    ax.grid(True, alpha=0.25)

    ax.plot(angles, ist_closed, linewidth=2.2, color=c_ist, label="Ist-Reifegrad")
    ax.plot(angles, soll_closed, linewidth=2.2, color=c_soll, label="Soll-Reifegrad")

    ax.set_title(title, fontsize=12, pad=14)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, -0.15), ncol=2, frameon=False, fontsize=9)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def make_pdf_bytes(meta: dict, df_raw: pd.DataFrame) -> bytes:
    """
    Robust PDF-Export (ReportLab), verhindert LayoutError:
    - Landscape A4
    - Tabellenzellen als Paragraph mit wordWrap='CJK'
    - Mindestbreiten für Spalten
    """
    from io import BytesIO
    from datetime import datetime
    from xml.sax.saxutils import escape as _xml_escape

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    # --- Helpers -------------------------------------------------
    def _safe_text(x) -> str:
        """Sicherer Text für Paragraph (escape + linebreaks + soft wrap points)."""
        if x is None:
            s = "-"
        else:
            try:
                # pandas NA sauber behandeln
                if pd.isna(x):
                    s = "-"
                else:
                    s = str(x)
            except Exception:
                s = str(x)

        s = s.strip() if s else "-"
        s = _xml_escape(s)                 # &,<,> escapen
        s = s.replace("\n", "<br/>")

        # Soft wrap opportunities für lange Tokens (zusätzlich zu wordWrap='CJK')
        for ch in ["/", "_", "-", ".", ":", ";", ","]:
            s = s.replace(ch, ch + "\u200b")

        return s

    def _P(text: str, style: ParagraphStyle) -> Paragraph:
        return Paragraph(_safe_text(text), style)

    def _colwidths(doc_width: float, cols: list[str]) -> list[float]:
        """
        Gewichtet Spaltenbreiten mit Mindestbreite, skaliert auf doc_width.
        Passe weights bei Bedarf an.
        """
        weights = {
            "Priorität": 0.9,
            "Kürzel": 1.1,
            "Themenbereich": 2.4,
            "Ist-Reifegrad": 1.0,
            "Soll-Reifegrad": 1.0,
            "Gap": 0.9,
            "Maßnahme": 3.2,
            "Zeitraum": 1.3,
        }
        min_w = 1.2 * cm  # Mindestbreite je Spalte

        w = [weights.get(c, 1.2) for c in cols]
        s = sum(w) if w else 1.0
        widths = [max(min_w, doc_width * (wi / s)) for wi in w]

        # Falls wegen min_w die Summe > doc_width, proportional runter skalieren (aber nicht unter min_w)
        total = sum(widths)
        if total > doc_width:
            # Skalierungsfaktor nur auf den Teil über min_w
            flex = [max(0.0, wi - min_w) for wi in widths]
            flex_sum = sum(flex)
            if flex_sum > 0:
                overflow = total - doc_width
                widths = [
                    (min_w + (fi * (1.0 - overflow / flex_sum))) if fi > 0 else min_w
                    for wi, fi in zip(widths, flex)
                ]
                # Safety clamp
                widths = [max(min_w, wi) for wi in widths]

        return widths

    # --- Document ------------------------------------------------
    buf = BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title="Reifegradmodell – Gesamtübersicht",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "rgm_title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        spaceAfter=10,
    )
    h_style = ParagraphStyle(
        "rgm_h",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        spaceBefore=8,
        spaceAfter=6,
    )
    cell_style = ParagraphStyle(
        "rgm_cell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        wordWrap="CJK",  # <- entscheidend: bricht auch lange Tokens
    )
    head_style = ParagraphStyle(
        "rgm_head",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.white,
        alignment=1,
    )

    story = []

    story.append(Paragraph("Reifegradmodell – Gesamtübersicht", title_style))
    story.append(Paragraph(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}", cell_style))
    story.append(Spacer(1, 8))

    # --- Meta ----------------------------------------------------
    story.append(Paragraph("Angaben zur Erhebung", h_style))
    meta_rows = [
        ["Name der Organisation", meta.get("org", "-"), "Datum der Durchführung", meta.get("date_str", "-")],
        ["Bereich", meta.get("area", "-"), "Angestrebtes Ziel", meta.get("target_label", "-")],
        ["Erhebung durchgeführt von", meta.get("assessor", "-"), "Soll-Niveau (global)", meta.get("global_target", "-")],
    ]
    meta_table = Table(
        [[_P(a, cell_style), _P(b, cell_style), _P(c, cell_style), _P(d, cell_style)] for a, b, c, d in meta_rows],
        colWidths=[3.8 * cm, 7.5 * cm, 3.8 * cm, doc.width - (3.8 * cm + 7.5 * cm + 3.8 * cm)],
        hAlign="LEFT",
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # --- Results Table ------------------------------------------
    story.append(Paragraph("Ergebnisse & Maßnahmen", h_style))

    # Nutze euren bestehenden Export-DF (stabil bzgl. Spaltennamen)
    df_export = df_results_for_export(df_raw).copy()

    # Sicherstellen, dass Spalten existieren (insb. nach deinen Änderungen)
    for c in ["Priorität", "Kürzel", "Themenbereich", "Ist-Reifegrad", "Soll-Reifegrad", "Gap", "Maßnahme", "Zeitraum"]:
        if c not in df_export.columns:
            df_export[c] = ""

    # Sortierung: Priorität, dann Gap
    prio_rank = {"A (hoch)": 0, "B (mittel)": 1, "C (niedrig)": 2}
    df_export["_prio_rank"] = df_export["Priorität"].map(lambda x: prio_rank.get(str(x), 9))
    df_export["Gap"] = pd.to_numeric(df_export["Gap"], errors="coerce")
    df_export["_gap_sort"] = df_export["Gap"].fillna(-1)
    df_export = df_export.sort_values(["_prio_rank", "_gap_sort"], ascending=[True, False]).drop(columns=["_prio_rank", "_gap_sort"], errors="ignore")

    cols = ["Priorität", "Kürzel", "Themenbereich", "Ist-Reifegrad", "Soll-Reifegrad", "Gap", "Maßnahme", "Zeitraum"]
    col_widths = _colwidths(doc.width, cols)

    # Header + Rows als Paragraph (wrap-sicher)
    data = [[_P(c, head_style) for c in cols]]
    for _, row in df_export.iterrows():
        data.append([_P(row.get(c, "-"), cell_style) for c in cols])

    t = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F5597")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#2F5597")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F7")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(t)

    doc.build(story)
    return buf.getvalue()
