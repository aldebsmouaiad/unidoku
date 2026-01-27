# /core/exporter.py
from __future__ import annotations

import csv as _csv
import io
import html as _html
import copy
from datetime import datetime
from typing import Optional, Any

import pandas as pd

# ReportLab (PDF)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    LongTable,
    TableStyle,
    Image,
    PageBreak,
)

# Plotly optional (für PNG-Export in PDF)
try:
    import plotly.io as pio  # noqa: F401
except Exception:
    pio = None


# ---------------------------------------------------------------------
# Public API (wird von pages importiert)
# ---------------------------------------------------------------------
__all__ = [
    "df_results_for_export",
    "make_csv_bytes",
    "make_pdf_bytes",
]


# ---------------------------------------------------------------------
# Helpers (robust, keine Streamlit-Abhängigkeiten)
# ---------------------------------------------------------------------
def _pick_first_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _fmt(v: Any, dash: str = "—") -> str:
    if v is None:
        return dash
    s = str(v).strip()
    return s if s else dash


def _to_int_str(x: Any) -> str:
    """Konvertiert robust zu Integer-String (für Ist/Soll/Gap)."""
    try:
        if x is None or (isinstance(x, float) and x != x):
            return ""
        if pd.isna(x):
            return ""
        return str(int(round(float(x))))
    except Exception:
        return ""


def _p(text: Any, style: ParagraphStyle, cjk_wrap: bool = False) -> Paragraph:
    """
    ReportLab Paragraph benötigt HTML-Escaping für &,<,> etc.
    cjk_wrap=True sorgt für Umbruch auch bei langen Strings ohne Leerzeichen.
    """
    s = "" if text is None else str(text)
    s = _html.escape(s).replace("\n", "<br/>")
    st = ParagraphStyle(name=style.name + ("_cjk" if cjk_wrap else ""), parent=style)
    if cjk_wrap:
        st.wordWrap = "CJK"
    return Paragraph(s, st)


def _plotly_fig_to_png_bytes(
    fig,
    *,
    width: int = 2000,
    height: int = 1400,
    scale: int = 2,
    dark_export: bool = False,
) -> Optional[bytes]:
    """
    Plotly-Export zu PNG (benötigt i.d.R. kaleido).
    - robust: gibt None zurück (kein Crash), falls nicht verfügbar
    - tuned: größere Margins + Domain, damit Labels NICHT abgeschnitten werden
    """
    if fig is None:
        return None

    # plotly / kaleido nicht verfügbar => kein Crash, aber None
    if pio is None:
        try:
            # falls fig.to_image intern verfügbar ist (manchmal ohne pio import)
            return fig.to_image(format="png", width=width, height=height, scale=scale)
        except Exception:
            return None

    # Figure nicht mutieren (wichtig: die gleiche Figure wird im UI gezeigt)
    try:
        f = fig.full_copy()
    except Exception:
        f = copy.deepcopy(fig)

    # Export-Theme: konsistent mit UI (dark/light), aber PDF-sicher
    bg = "#111827" if dark_export else "#FFFFFF"
    fg = "rgba(255,255,255,0.92)" if dark_export else "#111111"
    grid = "rgba(255,255,255,0.18)" if dark_export else "rgba(0,0,0,0.10)"
    axis_line = "rgba(255,255,255,0.25)" if dark_export else "rgba(0,0,0,0.14)"

    try:
        f.update_layout(
            template="plotly_dark" if dark_export else "plotly_white",
            paper_bgcolor=bg,
            plot_bgcolor=bg,
            font=dict(color=fg),
            showlegend=False,
            # Wichtig: genügend Margins für lange Achsenbeschriftungen
            margin=dict(l=120, r=120, t=70, b=140),
            title=None,
        )
    except Exception:
        pass

    # Polar tuning: Domain leicht einziehen -> mehr Platz für Labels, keine Cuts
    try:
        f.update_polars(
            domain=dict(x=[0.10, 0.90], y=[0.10, 0.90]),
            bgcolor=bg,
            radialaxis=dict(
                gridcolor=grid,
                linecolor=axis_line,
                tickfont=dict(color="#d62728", size=20),  # Skala (1..5) gut lesbar
                tickcolor="#d62728",
            ),
            angularaxis=dict(
                gridcolor=grid,
                linecolor=axis_line,
                tickfont=dict(color=fg, size=18),
            ),
        )
    except Exception:
        pass

    # PNG export (kaleido)
    try:
        # pio.to_image ist robuster als fig.to_image, wenn engine explizit ist
        return pio.to_image(f, format="png", width=width, height=height, scale=scale, engine="kaleido")
    except TypeError:
        # ältere plotly-Version ohne engine-Parameter
        try:
            return pio.to_image(f, format="png", width=width, height=height, scale=scale)
        except Exception:
            return None
    except Exception:
        # Fallback: fig.to_image versuchen
        try:
            return f.to_image(format="png", width=width, height=height, scale=scale)
        except Exception:
            return None


def _scaled_rl_image(png_bytes: bytes, *, max_width_pt: float) -> Optional[Image]:
    """
    Erzeugt ein ReportLab Image aus PNG-Bytes, skaliert proportional auf max_width_pt.
    """
    try:
        bio = io.BytesIO(png_bytes)
        reader = ImageReader(bio)
        iw, ih = reader.getSize()
        if not iw or not ih:
            return None

        w = float(max_width_pt)
        h = w * (float(ih) / float(iw))

        bio2 = io.BytesIO(png_bytes)
        bio2.seek(0)
        return Image(bio2, width=w, height=h)
    except Exception:
        return None


def _page_footer(canvas, doc, footer_left: str, footer_right: str) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#6B7280"))  # gray-500

    w, _h = A4
    y = 12 * mm
    canvas.drawString(doc.leftMargin, y, footer_left)

    page = canvas.getPageNumber()
    canvas.drawRightString(w - doc.rightMargin, y, f"{footer_right}   Seite {page}")
    canvas.restoreState()


def _split_text_into_chunks(text: Any, max_chars: int) -> list[str]:
    """
    Teilt sehr lange Texte in Chunks, damit eine Tabellenzeile nicht höher als eine Seite wird.
    - erhält Zeilenumbrüche
    - splittet auch sehr lange "Wörter" ohne Leerzeichen
    """
    s = "" if text is None else str(text)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    if max_chars <= 0:
        return [s]

    if len(s) <= max_chars:
        return [s]

    raw_lines = s.split("\n")
    lines: list[str] = []
    for line in raw_lines:
        if len(line) <= max_chars:
            lines.append(line)
            continue
        start = 0
        while start < len(line):
            lines.append(line[start : start + max_chars])
            start += max_chars

    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0

    for line in lines:
        add_len = len(line) + (1 if cur else 0)
        if cur and (cur_len + add_len > max_chars):
            chunks.append("\n".join(cur))
            cur = [line]
            cur_len = len(line)
        else:
            cur.append(line)
            cur_len += add_len

    if cur:
        chunks.append("\n".join(cur))

    return chunks if chunks else [""]


def _scale_col_widths_pt(desired_pt: list[float], available_pt: float) -> list[float]:
    """
    Skaliert gewünschte Spaltenbreiten so, dass Summe <= available_pt.
    """
    total = float(sum(desired_pt))
    if total <= 0:
        return desired_pt
    if total <= available_pt:
        return desired_pt

    factor = available_pt / total
    return [w * factor for w in desired_pt]


# ---------------------------------------------------------------------
# 1) DataFrame für Maßnahmen/Export aufbereiten (robust)
# ---------------------------------------------------------------------
def df_results_for_export(df_report: pd.DataFrame) -> pd.DataFrame:
    """
    Liefert eine exportfreundliche Maßnahmen-Tabelle in einheitlichen Spalten.

    Erwartet typischerweise df_report aus _clean_overview_df(df_raw) oder direkt df_raw.
    Funktion ist robust gegen unterschiedliche Spaltennamen.
    """
    if df_report is None or df_report.empty:
        return pd.DataFrame()

    d = df_report.copy()

    prio_col = _pick_first_col(d, ["Priorität", "Prioritaet", "priority", "prio", "Priority"])
    code_col = _pick_first_col(d, ["Kürzel", "Kuerzel", "code", "Code", "id", "ID"])
    topic_col = _pick_first_col(d, ["Themenbereich", "Themenfeld", "topic", "subdimension", "Subdimension", "Name", "name"])

    ist_col = _pick_first_col(d, ["Ist-Reifegrad", "ist_level", "ist", "Ist", "IST"])
    soll_col = _pick_first_col(d, ["Soll-Reifegrad", "target_level", "soll_level", "target", "Soll", "SOLL"])
    gap_col = _pick_first_col(d, ["Gap", "gap"])

    measure_col = _pick_first_col(d, ["Maßnahme", "Massnahme", "measure", "action", "Maßnahmenbeschreibung"])
    resp_col = _pick_first_col(d, ["Verantwortlich", "responsible", "owner", "Owner"])
    time_col = _pick_first_col(d, ["Zeitraum", "timeframe", "period", "Timeframe"])

    out = pd.DataFrame()

    out["Priorität"] = d[prio_col] if prio_col else ""
    out["Kürzel"] = d[code_col] if code_col else ""
    out["Themenbereich"] = d[topic_col] if topic_col else ""

    out["Ist-Reifegrad"] = pd.to_numeric(d[ist_col], errors="coerce") if ist_col else pd.NA
    out["Soll-Reifegrad"] = pd.to_numeric(d[soll_col], errors="coerce") if soll_col else pd.NA

    if gap_col:
        out["Gap"] = pd.to_numeric(d[gap_col], errors="coerce")
    else:
        out["Gap"] = out["Soll-Reifegrad"] - out["Ist-Reifegrad"]

    out["Maßnahme"] = d[measure_col] if measure_col else ""
    out["Verantwortlich"] = d[resp_col] if resp_col else ""
    out["Zeitraum"] = d[time_col] if time_col else ""

    for c in ["Priorität", "Kürzel", "Themenbereich", "Maßnahme", "Verantwortlich", "Zeitraum"]:
        out[c] = out[c].astype(str).fillna("")
        out[c] = out[c].replace({"nan": "", "None": ""})

    return out


# ---------------------------------------------------------------------
# 2) CSV Export (Excel-freundlich)
# ---------------------------------------------------------------------
def make_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    CSV für Excel (DE) robust:
    - UTF-8 BOM, damit Excel Umlaute korrekt erkennt
    - Semikolon als Separator
    """
    if df is None:
        df = pd.DataFrame()

    buf = io.StringIO()
    df.to_csv(
        buf,
        index=False,
        sep=";",
        quoting=_csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    return ("\ufeff" + buf.getvalue()).encode("utf-8")


# ---------------------------------------------------------------------
# 3) PDF Export (professionell + robust)
# ---------------------------------------------------------------------
def make_pdf_bytes(
    meta: dict,
    df_raw: pd.DataFrame,
    df_report: Optional[pd.DataFrame] = None,
    df_measures: Optional[pd.DataFrame] = None,
    fig_td=None,
    fig_og=None,
    dark: bool = False,
) -> bytes:
    """
    Professioneller PDF-Export (A4):
    - Titel + zweifarbige Accent-Line (TD/OG)
    - Angaben zur Erhebung (2-Spalten Key-Value)
    - Kennzahlen (Bewertet / Handlungsbedarf)
    - Optional: Radar-Charts als PNG (wenn Plotly/kaleido verfügbar)
    - Geplante Maßnahmen als LongTable (mehrseitig, Word-Wrap)
      + robuste Chunk-Splitting-Logik für extrem lange Textzellen
      + Spaltenbreiten werden auf doc.width skaliert (sonst "too large")
    """

    # --- Farben (zurückhaltend, hochwertig) ---
    TD_BLUE = colors.HexColor("#2F3DB8")
    OG_ORANGE = colors.HexColor("#F28C28")
    TEXT = colors.HexColor("#111111")
    BORDER = colors.HexColor("#D1D5DB")   # gray-300
    SOFT_BG = colors.HexColor("#F3F4F6")  # gray-100
    ZEBRA = colors.HexColor("#FAFAFA")    # very light

    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm,
        title="Reifegrad – Gesamtübersicht",
        author="UniDoku",
    )

    styles = getSampleStyleSheet()
    H1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=TEXT,
        spaceAfter=8,
    )
    H2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=16,
        textColor=TEXT,
        spaceBefore=10,
        spaceAfter=6,
    )
    P = ParagraphStyle(
        "P",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.0,
        leading=13,
        textColor=TEXT,
    )
    SMALL = ParagraphStyle(
        "SMALL",
        parent=P,
        fontSize=9.0,
        leading=11.5,
        textColor=colors.HexColor("#374151"),  # gray-700
    )

    story: list[Any] = []

    # --- Titel ---
    story.append(Paragraph("Gesamtübersicht – Reifegraderhebung", H1))

    # Zweifarbige Accent-Line (TD/OG)
    accent = Table(
        [["", ""]],
        colWidths=[doc.width * 0.55, doc.width * 0.45],
        rowHeights=[2.2 * mm],
    )
    accent.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), TD_BLUE),
                ("BACKGROUND", (1, 0), (1, 0), OG_ORANGE),
            ]
        )
    )
    story.append(accent)
    story.append(Spacer(1, 6 * mm))

    # --- Angaben zur Erhebung ---
    story.append(Paragraph("Angaben zur Erhebung", H2))

    left = [
        ("Name der Organisation", _fmt(meta.get("org", ""))),
        ("Bereich", _fmt(meta.get("area", ""))),
        ("Erhebung durchgeführt von", _fmt(meta.get("assessor", ""))),
    ]
    right = [
        ("Datum der Durchführung", _fmt(meta.get("date_str", ""))),
        ("Angestrebtes Ziel", _fmt(meta.get("target_label", ""))),
        ("Kontakt", _fmt(meta.get("assessor_contact", ""))),
    ]

    def _kv_table(pairs: list[tuple[str, str]]) -> Table:
        rows = []
        for k, v in pairs:
            rows.append(
                [
                    Paragraph(f"<b>{_html.escape(k)}</b>", SMALL),
                    Paragraph(_html.escape(_fmt(v)), P),
                ]
            )
        t = Table(rows, colWidths=[55 * mm, 60 * mm])
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return t

    meta_grid = Table(
        [[_kv_table(left), _kv_table(right)]],
        colWidths=[doc.width / 2, doc.width / 2],
    )
    meta_grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(meta_grid)
    story.append(Spacer(1, 5 * mm))

    # --- Kennzahlen ---
    story.append(Paragraph("Kennzahlen", H2))

    drep = df_report if (df_report is not None and not df_report.empty) else (df_raw.copy() if df_raw is not None else pd.DataFrame())
    n_total = int(len(drep))

    answered = 0
    if "answered" in drep.columns:
        answered = int(pd.to_numeric(drep["answered"], errors="coerce").fillna(0).astype(bool).sum())
    elif "ist_level" in drep.columns:
        answered = int(pd.to_numeric(drep["ist_level"], errors="coerce").notna().sum())
    elif "Ist-Reifegrad" in drep.columns:
        answered = int(pd.to_numeric(drep["Ist-Reifegrad"], errors="coerce").notna().sum())

    need_action = 0
    if "gap" in drep.columns:
        need_action = int((pd.to_numeric(drep["gap"], errors="coerce").fillna(0) > 0).sum())
    elif "Gap" in drep.columns:
        need_action = int((pd.to_numeric(drep["Gap"], errors="coerce").fillna(0) > 0).sum())
    else:
        ist_col = _pick_first_col(drep, ["ist_level", "Ist-Reifegrad"])
        soll_col = _pick_first_col(drep, ["target_level", "Soll-Reifegrad"])
        if ist_col and soll_col:
            tmp = pd.to_numeric(drep[soll_col], errors="coerce") - pd.to_numeric(drep[ist_col], errors="coerce")
            need_action = int((tmp.fillna(0) > 0).sum())

    kpi_tbl = Table(
        [
            ["Bewertet", f"{answered} / {n_total}"],
            ["Handlungsbedarf (Gap > 0)", str(need_action)],
            ["Erstellt am", datetime.now().strftime("%d.%m.%Y %H:%M")],
        ],
        colWidths=[70 * mm, 60 * mm],
    )
    kpi_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SOFT_BG),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10.0),
                ("TEXTCOLOR", (0, 0), (-1, -1), TEXT),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(kpi_tbl)
    story.append(Spacer(1, 6 * mm))

    # --- Charts optional (aber: wenn Figuren übergeben sind, immer Abschnitt anzeigen) ---
    have_figs = (fig_td is not None) or (fig_og is not None)

    td_png = _plotly_fig_to_png_bytes(fig_td, dark_export=dark)
    og_png = _plotly_fig_to_png_bytes(fig_og, dark_export=dark)

    if have_figs:
        story.append(Paragraph("Radar – Ist- vs. Soll-Reifegrad", H2))
        story.append(
            Paragraph(
                _html.escape("Skala: 1 Initial, 2 Gemanagt, 3 Definiert, 4 Quantitativ gemanagt, 5 Optimiert"),
                SMALL,
            )
        )
        story.append(Spacer(1, 3 * mm))

        def _img_block(png_bytes: bytes, title: str, border_color) -> None:
            # Frame hat padding links/rechts 6pt => Bildbreite <= doc.width - 12pt
            inner_w = float(doc.width) - 12.0
            img = _scaled_rl_image(png_bytes, max_width_pt=inner_w)
            if img is None:
                story.append(_p(f"{title}: Plot konnte nicht eingebettet werden.", P))
                story.append(Spacer(1, 4 * mm))
                return

            cap = Table([[Paragraph(f"<b>{_html.escape(title)}</b>", P)]], colWidths=[doc.width])
            cap.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))

            frame = Table([[img]], colWidths=[doc.width])
            frame.setStyle(
                TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 1.2, border_color),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.extend([cap, frame, Spacer(1, 6 * mm)])

        # TD / OG Blöcke
        if fig_td is not None:
            if td_png:
                _img_block(td_png, "TD-Dimensionen", TD_BLUE)
            else:
                story.append(
                    _p(
                        "TD-Dimensionen: Plot konnte nicht gerendert werden. "
                        "Hinweis: Für Plotly-Export im PDF wird in der Regel 'kaleido' benötigt "
                        "(pip install -U kaleido).",
                        P,
                    )
                )
                story.append(Spacer(1, 4 * mm))

        if fig_og is not None:
            if og_png:
                _img_block(og_png, "OG-Dimensionen", OG_ORANGE)
            else:
                story.append(
                    _p(
                        "OG-Dimensionen: Plot konnte nicht gerendert werden. "
                        "Hinweis: Für Plotly-Export im PDF wird in der Regel 'kaleido' benötigt "
                        "(pip install -U kaleido).",
                        P,
                    )
                )
                story.append(Spacer(1, 4 * mm))

        # Maßnahmen sauber auf neuer Seite starten, sobald Plots-Abschnitt existiert
        story.append(PageBreak())

    # --- Maßnahmen ---
    story.append(Paragraph("Geplante Maßnahmen", H2))

    if df_measures is None or df_measures.empty:
        base = drep if (drep is not None and not drep.empty) else df_raw
        df_measures = df_results_for_export(base) if (base is not None and not base.empty) else pd.DataFrame()

    if df_measures.empty:
        story.append(_p("Keine Einträge vorhanden.", P))
    else:
        ordered = [
            "Priorität",
            "Kürzel",
            "Themenbereich",
            "Ist-Reifegrad",
            "Soll-Reifegrad",
            "Gap",
            "Maßnahme",
            "Verantwortlich",
            "Zeitraum",
        ]
        cols = [c for c in ordered if c in df_measures.columns]
        d = df_measures[cols].copy()

        for c in ["Ist-Reifegrad", "Soll-Reifegrad", "Gap"]:
            if c in d.columns:
                d[c] = d[c].apply(_to_int_str)

        # --- Extrem lange Textzellen in mehrere Tabellenzeilen splitten ---
        wrap_cols = {"Maßnahme", "Verantwortlich", "Zeitraum"}
        chunk_limits = {
            "Maßnahme": 700,
            "Verantwortlich": 220,
            "Zeitraum": 120,
        }

        expanded_rows: list[dict[str, Any]] = []
        for _, r in d.iterrows():
            chunks_by_col: dict[str, list[str]] = {}
            max_parts = 1

            for c in cols:
                if c in wrap_cols:
                    parts = _split_text_into_chunks(r.get(c, ""), chunk_limits.get(c, 250))
                    chunks_by_col[c] = parts
                    max_parts = max(max_parts, len(parts))

            for i in range(max_parts):
                out_row: dict[str, Any] = {}
                for c in cols:
                    if c in wrap_cols:
                        parts = chunks_by_col.get(c, [""])
                        out_row[c] = parts[i] if i < len(parts) else ""
                    else:
                        out_row[c] = r.get(c, "") if i == 0 else ""
                expanded_rows.append(out_row)

        d2 = pd.DataFrame(expanded_rows, columns=cols)

        header = [Paragraph(f"<b>{_html.escape(c)}</b>", SMALL) for c in cols]
        rows: list[list[Any]] = [header]

        P_TAB = ParagraphStyle("P_TAB", parent=P, fontSize=9.2, leading=12)

        for _, r in d2.iterrows():
            row: list[Any] = []
            for c in cols:
                v = "" if pd.isna(r[c]) else r[c]
                if c in wrap_cols:
                    row.append(_p(v, P_TAB, cjk_wrap=True))
                else:
                    row.append(_p(v, P_TAB, cjk_wrap=False))
            rows.append(row)

        desired_mm = {
            "Priorität": 20,
            "Kürzel": 14,
            "Themenbereich": 28,
            "Ist-Reifegrad": 12,
            "Soll-Reifegrad": 12,
            "Gap": 10,
            "Maßnahme": 45,
            "Verantwortlich": 22,
            "Zeitraum": 15,
        }
        desired_pt = [float(desired_mm.get(c, 18)) * mm for c in cols]
        col_widths = _scale_col_widths_pt(desired_pt, float(doc.width))

        t = LongTable(rows, colWidths=col_widths, repeatRows=1)

        style_cmds: list[tuple] = [
            ("BACKGROUND", (0, 0), (-1, 0), SOFT_BG),
            ("TEXTCOLOR", (0, 0), (-1, -1), TEXT),
            ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]

        for i in range(1, len(rows)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))

        for c in ["Ist-Reifegrad", "Soll-Reifegrad", "Gap"]:
            if c in cols:
                j = cols.index(c)
                style_cmds.append(("ALIGN", (j, 1), (j, -1), "RIGHT"))

        t.setStyle(TableStyle(style_cmds))
        story.append(t)

    footer_left = "UniDoku – Reifegradmodell"
    footer_right = _fmt(meta.get("org", ""), dash="")

    doc.build(
        story,
        onFirstPage=lambda canv, d: _page_footer(canv, d, footer_left, footer_right),
        onLaterPages=lambda canv, d: _page_footer(canv, d, footer_left, footer_right),
    )

    return buf.getvalue()
