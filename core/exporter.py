# /core/exporter.py
from __future__ import annotations

import csv as _csv
import io
import html as _html
import copy
from datetime import datetime
from typing import Optional, Any

import os
import hashlib
from pathlib import Path
import tempfile

import pandas as pd

# ReportLab (PDF)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    LongTable,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
)


TU_GREEN = colors.HexColor("#639A00")

# ---------------------------------------------------------------------
# Plot cache (Streamlit Cloud: /tmp ist beschreibbar)
# ---------------------------------------------------------------------
_PLOT_CACHE_DIR = Path(tempfile.gettempdir()) / "rgm_plot_cache"
_PLOT_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _plot_cache_path(fig, width: int, height: int, scale: int, dark_export: bool) -> Path:
    j = fig.to_json() if hasattr(fig, "to_json") else str(fig)
    h = hashlib.sha1()
    h.update(j.encode("utf-8"))
    h.update(f"|{width}|{height}|{scale}|{int(dark_export)}".encode("utf-8"))
    return _PLOT_CACHE_DIR / f"{h.hexdigest()}.png"


# Plotly optional (für PNG-Export in PDF)
try:
    import plotly.io as pio  # noqa: F401
except Exception:
    pio = None


def _ensure_kaleido_browser() -> Optional[str]:
    """
    Stellt sicher, dass ein Chrome/Chromium für Kaleido verfügbar ist.
    Installiert Chrome in /tmp (Streamlit Cloud: beschreibbar) und setzt BROWSER_PATH.
    """
    try:
        import plotly.io as _pio

        if not hasattr(_pio, "get_chrome"):
            return None

        chrome_dir = Path(tempfile.gettempdir()) / "plotly-chrome"
        chrome_dir.mkdir(parents=True, exist_ok=True)

        chrome_exe = _pio.get_chrome(path=chrome_dir)
        os.environ["BROWSER_PATH"] = str(chrome_exe)
        return str(chrome_exe)
    except Exception:
        return None


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
    """Konvertiert robust zu Integer-String (für Soll-Reifegrad)."""
    try:
        if x is None or (isinstance(x, float) and x != x):
            return ""
        if pd.isna(x):
            return ""
        return str(int(round(float(x))))
    except Exception:
        return ""


def _to_float_str(x: Any, *, decimals: int = 2, decimal_comma: bool = True) -> str:
    """Robust: Float-String mit Dezimalstellen (ohne Rundung auf Integer)."""
    try:
        if x is None:
            return ""
        if isinstance(x, float) and x != x:
            return ""
        if pd.isna(x):
            return ""

        v = float(x)

        # Ganze Zahlen ohne .00 anzeigen
        if abs(v - round(v)) < 1e-12:
            s = str(int(round(v)))
        else:
            s = f"{v:.{decimals}f}"
            if decimal_comma:
                s = s.replace(".", ",")

        return s
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


def _get_trace_color(fig, idx: int, fallback_hex: str) -> str:
    """Versucht Line/Marker-Farbe aus Plotly-Trace zu ziehen."""
    if fig is None:
        return fallback_hex
    try:
        t = fig.data[idx]
        if hasattr(t, "line") and getattr(t.line, "color", None):
            return str(t.line.color)
        if hasattr(t, "marker") and getattr(t.marker, "color", None):
            return str(t.marker.color)
    except Exception:
        pass
    return fallback_hex


def _plotly_fig_to_png_bytes(
    fig,
    *,
    width: int = 1500,
    height: int = 1100,
    scale: int = 2,
    dark_export: bool = False,
) -> tuple[Optional[bytes], Optional[str]]:
    """
    Exportiert eine Plotly-Figure robust nach PNG (für PDF-Einbettung).
    - mutiert die Original-Figure NICHT
    - versucht Export (kaleido) -> bei Fehler: Browser vorbereiten -> retry
    - cached PNGs in /tmp für schnelle wiederholte Exporte
    """
    if fig is None:
        return None, "fig is None"

    # 0) Figure copy (nicht mutieren)
    try:
        f = fig.full_copy()
    except Exception:
        f = copy.deepcopy(fig)

    # 1) Styling für Export: möglichst wie Download (großes Radar, klare Labels)
    bg = "#111827" if dark_export else "#FFFFFF"
    fg = "rgba(255,255,255,0.92)" if dark_export else "#111111"
    grid = "rgba(255,255,255,0.18)" if dark_export else "rgba(0,0,0,0.10)"
    axis_line = "rgba(255,255,255,0.25)" if dark_export else "rgba(0,0,0,0.14)"
    red_ticks = "#d62728"

    try:
        f.update_layout(
            template="plotly_dark" if dark_export else "plotly_white",
            paper_bgcolor=bg,
            plot_bgcolor=bg,
            font=dict(color=fg),
            showlegend=False,
            margin=dict(l=90, r=90, t=50, b=90),
            title=None,
        )
        f.update_polars(
            domain=dict(x=[0.04, 0.96], y=[0.04, 0.96]),
            bgcolor=bg,
            radialaxis=dict(
                gridcolor=grid,
                linecolor=axis_line,
                tickfont=dict(color=red_ticks, size=20),
                tickcolor=red_ticks,
            ),
            angularaxis=dict(
                gridcolor=grid,
                linecolor=axis_line,
                tickfont=dict(color=fg, size=20),
            ),
        )
    except Exception:
        pass

    # 2) Cache
    try:
        cache_path = _plot_cache_path(f, width, height, scale, dark_export)
    except Exception:
        cache_path = None

    if cache_path is not None and cache_path.exists():
        try:
            return cache_path.read_bytes(), None
        except Exception:
            pass

    # 3) Render helper
    def _try_render() -> tuple[Optional[bytes], Optional[str]]:
        if pio is None:
            try:
                return f.to_image(format="png", width=width, height=height, scale=scale), None
            except Exception as e:
                return None, f"{type(e).__name__}: {e}"

        try:
            return pio.to_image(f, format="png", width=width, height=height, scale=scale, engine="kaleido"), None
        except TypeError:
            try:
                return pio.to_image(f, format="png", width=width, height=height, scale=scale), None
            except Exception as e:
                return None, f"{type(e).__name__}: {e}"
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"

    # 4) 1. Versuch
    png, err = _try_render()
    if png:
        if cache_path is not None:
            try:
                cache_path.write_bytes(png)
            except Exception:
                pass
        return png, None

    # 5) 2. Versuch: Browser sicherstellen + retry
    try:
        _ensure_kaleido_browser()
    except Exception:
        pass

    png2, err2 = _try_render()
    if png2:
        if cache_path is not None:
            try:
                cache_path.write_bytes(png2)
            except Exception:
                pass
        return png2, None

    return None, (err2 or err or "unknown export error")


def _scaled_rl_image(png_bytes: bytes, *, max_width_pt: float) -> Optional[Image]:
    """Erzeugt ein ReportLab Image aus PNG-Bytes, skaliert proportional auf max_width_pt."""
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


def _find_ips_logo() -> Optional[Path]:
    """
    Sucht IPS-Logo robust:
    - bevorzugt: <project_root>/images/IPS-Logo-RGB.png (core/.. /images)
    - fallback: core/IPS-Logo-RGB.png
    """
    try:
        core_dir = Path(__file__).resolve().parent
        candidates = [
            core_dir.parent / "images" / "IPS-Logo-RGB.png",
            core_dir / "IPS-Logo-RGB.png",
        ]
        for p in candidates:
            if p.exists():
                return p
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------
# Footer (Canvas) Helpers
# ---------------------------------------------------------------------
def _wrap_words(text: str, max_w: float, font: str, size: float) -> list[str]:
    """Einfaches Word-Wrap für Canvas.drawString."""
    words = (text or "").split()
    if not words:
        return [""]

    lines: list[str] = []
    cur = ""

    for w in words:
        test = (cur + " " + w).strip()
        if stringWidth(test, font, size) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w

    if cur:
        lines.append(cur)

    return lines if lines else [""]


def _draw_text_wrapped(canvas, text: str, x: float, y: float, max_w: float, font: str, size: float, leading: float) -> float:
    """
    Zeichnet wrapped Text ab Baseline y nach unten.
    Rückgabe: Baseline-y der nächsten Zeile.
    """
    lines = _wrap_words(text, max_w, font, size)
    for line in lines:
        if line:
            canvas.drawString(x, y, line)
        y -= leading
    return y


def _draw_mail_icon(
    canvas,
    x: float,
    y_baseline: float,
    *,
    size: float = 6.2,
    color=TU_GREEN,
    stroke_w: float = 0.85,
) -> float:
    """
    Kleines Mail-Icon (SVG-Stil), baseline-aligned.
    """
    s = float(size)
    w = s
    h = s

    # baseline alignment
    y_bottom = y_baseline - h * 0.18

    canvas.saveState()
    canvas.setStrokeColor(color)
    canvas.setLineWidth(stroke_w)
    canvas.setLineCap(1)   # round
    canvas.setLineJoin(1)  # round

    # square
    canvas.rect(x, y_bottom, w, h, stroke=1, fill=0)

    # flap (V nach unten)
    y_top = y_bottom + h * 0.86
    y_mid = y_bottom + h * 0.46
    canvas.line(x + w, y_top, x + w / 2.0, y_mid)
    canvas.line(x + w / 2.0, y_mid, x, y_top)

    canvas.restoreState()
    return w

def _draw_prefix_icon_only_line(
    canvas,
    *,
    x: float,
    y: float,
    max_w: float,
    prefix: str,
    email: str,
    font: str,
    size: float,
    leading: float,
    icon_size: float = 6.2,
) -> float:
    """
    Zeichnet: "<prefix> [mail-icon]" (Icon ist mailto-link).
    KEIN Email-Text.
    """
    prefix = (prefix or "").strip()
    email = (email or "").strip()
    gap = 3.0

    prefix_w = stringWidth(prefix, font, size) if prefix else 0.0

    # 1-Zeile möglich?
    if prefix and (prefix_w + gap + icon_size <= max_w):
        canvas.drawString(x, y, prefix)
        ix = x + prefix_w + gap

        icon_w = _draw_mail_icon(canvas, ix, y, size=icon_size, color=TU_GREEN)

        # Klickfläche exakt wie Icon-Position
        y_bottom = y - icon_size * 0.18
        canvas.linkURL(
            f"mailto:{email}",
            (ix, y_bottom, ix + icon_w, y_bottom + icon_size),
            relative=0,
        )
        return y - leading

    # sonst: prefix umbrechen, dann Icon nächste Zeile links
    y2 = _draw_text_wrapped(canvas, prefix, x, y, max_w, font, size, leading)

    ix = x
    icon_w = _draw_mail_icon(canvas, ix, y2, size=icon_size, color=TU_GREEN)

    y_bottom = y2 - icon_size * 0.18
    canvas.linkURL(
        f"mailto:{email}",
        (ix, y_bottom, ix + icon_w, y_bottom + icon_size),
        relative=0,
    )
    return y2 - leading


def _link_mailto(canvas, x: float, y_baseline: float, text: str, font: str, size: float, email: str) -> None:
    """Setzt klickbaren mailto-Link über dem gezeichneten Text."""
    try:
        if not email or "@" not in email:
            return
        w = stringWidth(text, font, size)
        # Link-Rechteck grob um Textzeile (Baseline-basiert)
        y0 = y_baseline - size * 0.25
        y1 = y_baseline + size * 0.95
        canvas.linkURL(f"mailto:{email}", (x, y0, x + w, y1), relative=0)
    except Exception:
        return


def _draw_email(
    canvas,
    x: float,
    y: float,
    max_w: float,
    email: str,
    *,
    font: str,
    size: float,
    leading: float,
) -> float:
    """Zeichnet E-Mail; falls zu lang: Split bei '@' als Fallback. Rückgabe: nächste Baseline."""
    email = (email or "").strip()
    if not email:
        return y - leading

    if stringWidth(email, font, size) <= max_w:
        canvas.drawString(x, y, email)
        _link_mailto(canvas, x, y, email, font, size, email)
        return y - leading

    if "@" in email:
        user, dom = email.split("@", 1)
        part1 = user + "@"
        part2 = dom
        canvas.drawString(x, y, part1)
        _link_mailto(canvas, x, y, part1, font, size, email)
        y -= leading
        canvas.drawString(x, y, part2)
        _link_mailto(canvas, x, y, part2, font, size, email)
        return y - leading

    # Worst-case: hart splitten
    cur = ""
    start_x = x
    for ch in email:
        test = cur + ch
        if stringWidth(test, font, size) <= max_w or not cur:
            cur = test
        else:
            canvas.drawString(start_x, y, cur)
            _link_mailto(canvas, start_x, y, cur, font, size, email)
            y -= leading
            cur = ch
    if cur:
        canvas.drawString(start_x, y, cur)
        _link_mailto(canvas, start_x, y, cur, font, size, email)
        y -= leading
    return y


def _draw_prefix_mail_line(
    canvas,
    *,
    x: float,
    y: float,
    max_w: float,
    prefix: str,
    email: str,
    gray_color,
    font: str,
    size: float,
    leading: float,
    icon_size: float = 8.0,
) -> float:
    """
    Zeichnet exakt wie gewünscht:
      "<prefix> [mail icon] <email>"
    - Icon ist korrekt orientiert und baseline-aligned (nicht versetzt).
    - Wenn nicht genug Platz: prefix wrapped, dann Icon+Email darunter.
    Rückgabe: neue Baseline-y.
    """
    prefix = (prefix or "").strip()
    email = (email or "").strip()
    gap = 3.0

    prefix_w = stringWidth(prefix, font, size) if prefix else 0.0
    email_w = stringWidth(email, font, size) if email else 0.0
    icon_w = float(icon_size)

    # Passt in eine Zeile?
    if prefix and email and (prefix_w + gap + icon_w + gap + email_w <= max_w):
        canvas.drawString(x, y, prefix)
        ix = x + prefix_w + gap
        _draw_mail_icon(canvas, ix, y, size=icon_size, color=gray_color)
        # optional: Icon klickbar
        try:
            canvas.linkURL(f"mailto:{email}", (ix, y - icon_size * 0.11, ix + icon_w, y - icon_size * 0.11 + icon_size), relative=0)
        except Exception:
            pass

        return _draw_email(
            canvas,
            ix + icon_w + gap,
            y,
            max_w - (prefix_w + gap + icon_w + gap),
            email,
            font=font,
            size=size,
            leading=leading,
        )

    # Sonst: prefix (wrap), dann Icon+Email darunter
    y2 = _draw_text_wrapped(canvas, prefix, x, y, max_w, font, size, leading)

    ix = x
    _draw_mail_icon(canvas, ix, y2, size=icon_size, color=gray_color)
    try:
        canvas.linkURL(f"mailto:{email}", (ix, y2 - icon_size * 0.11, ix + icon_w, y2 - icon_size * 0.11 + icon_size), relative=0)
    except Exception:
        pass

    return _draw_email(
        canvas,
        ix + icon_w + gap,
        y2,
        max_w - (icon_w + gap),
        email,
        font=font,
        size=size,
        leading=leading,
    )


def _page_footer(canvas, doc, *, org_right: str = "") -> None:
    """
    Footer auf jeder Seite:
    - IPS Logo links
    - daneben: Reifegradmodell + Kontaktinfos mit Mail-Icon (sauber aligned, nicht umgedreht)
    - rechts: optional org + Seite
    """
    canvas.saveState()

    w, _h = A4

    # Farben/Typo
    gray = colors.HexColor("#6B7280")  # gray-500
    canvas.setFillColor(gray)

    # Positionen (innerhalb bottomMargin)
    y0 = 8 * mm
    x0 = doc.leftMargin

    # Logo
    logo_path = _find_ips_logo()
    logo_w = 0.0
    logo_h = 9 * mm
    gap = 5 * mm

    if logo_path and logo_path.exists():
        try:
            reader = ImageReader(str(logo_path))
            iw, ih = reader.getSize()
            if iw and ih:
                logo_w = logo_h * (float(iw) / float(ih))
                canvas.drawImage(
                    reader,
                    x0,
                    y0,
                    width=logo_w,
                    height=logo_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
        except Exception:
            logo_w = 0.0

    # Textblock (links)
    tx = x0 + (logo_w + gap if logo_w > 0 else 0.0)
    max_left_w = (w - doc.rightMargin) - tx - 8 * mm

    font = "Helvetica"
    size = 8.4
    leading = 9.4
    canvas.setFont(font, size)

    # Beginne oben am Logo
    y = y0 + logo_h - 1.0 * mm

    # 1) Titel (wrap-sicher)
    y = _draw_text_wrapped(
        canvas,
        "Reifegradmodell für die Technische Dokumentation",
        tx,
        y,
        max_left_w,
        font,
        size,
        leading,
    )

    y = _draw_prefix_icon_only_line(
        canvas,
        x=tx,
        y=y,
        max_w=max_left_w,
        prefix="Erstellt durch: Christian Koch",
        email="christian4.koch@tu-dortmund.de",
        font=font,
        size=size,
        leading=leading,
        icon_size=6.2,
    )

    y = _draw_prefix_icon_only_line(
        canvas,
        x=tx,
        y=y,
        max_w=max_left_w,
        prefix="Technischer Support: Mouaiad Aldebs",
        email="mouaiad.aldebs@tu-dortmund.de",
        font=font,
        size=size,
        leading=leading,
        icon_size=6.2,
    )

    # Rechte Seite: Org + Seite
    page = canvas.getPageNumber()
    right_txt = f"{org_right}   Seite {page}".strip() if org_right else f"Seite {page}"
    canvas.setFont(font, size)
    canvas.drawRightString(w - doc.rightMargin, y0 + 1.2 * mm, right_txt)

    canvas.restoreState()


def _split_text_into_chunks(text: Any, max_chars: int) -> list[str]:
    """Teilt sehr lange Texte in Chunks, damit eine Tabellenzeile nicht höher als eine Seite wird."""
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
    """Skaliert gewünschte Spaltenbreiten so, dass Summe <= available_pt."""
    total = float(sum(desired_pt))
    if total <= 0:
        return desired_pt
    if total <= available_pt:
        return desired_pt
    factor = available_pt / total
    return [w * factor for w in desired_pt]


def _kpi_counts_by_prefix(df: pd.DataFrame, prefix: str) -> tuple[int, int, int]:
    """
    Liefert (ntotal, n_answered, n_need_action) für TD/OG.
    Logik wie in Gesamtübersicht: Handlungsbedarf zählt nur aus beantworteten Zeilen.
    """
    if df is None or df.empty:
        return 0, 0, 0

    code_col = _pick_first_col(df, ["Kürzel", "Kuerzel", "code", "Code"])
    if not code_col:
        return 0, 0, 0

    pref = (
        df[code_col]
        .astype(str)
        .fillna("")
        .str.strip()
        .str.upper()
        .str.extract(r"^(TD|OG)")[0]
        .fillna("")
    )
    d = df[pref.eq(prefix)].copy()
    nt = int(len(d))

    # answered
    if "answered" in d.columns:
        answered_mask = pd.to_numeric(d["answered"], errors="coerce").fillna(0).astype(bool)
        na = int(answered_mask.sum())
    else:
        ist_col = _pick_first_col(d, ["ist_level", "Ist-Reifegrad"])
        if ist_col:
            answered_mask = pd.to_numeric(d[ist_col], errors="coerce").notna()
            na = int(answered_mask.sum())
        else:
            na = 0
            answered_mask = pd.Series([False] * len(d), index=d.index)

    # need action: nur beantwortete
    gap_col = _pick_first_col(d, ["gap", "Gap"])
    if na > 0 and gap_col:
        g = pd.to_numeric(d.loc[answered_mask, gap_col], errors="coerce").fillna(0.0)
        nn = int((g > 0).sum())
    else:
        nn = 0

    return nt, na, nn


def _mini_legend_table(ist_color_hex: str, soll_color_hex: str, *, P_STYLE: ParagraphStyle) -> Table:
    """Mini-Legende wie in Download: farbiger Strich + Label."""
    sw_w = 34
    sw_h = 3

    sw_ist = Table([[""]], colWidths=[sw_w], rowHeights=[sw_h])
    sw_ist.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(ist_color_hex))]))

    sw_soll = Table([[""]], colWidths=[sw_w], rowHeights=[sw_h])
    sw_soll.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(soll_color_hex))]))

    row = [
        sw_ist,
        Paragraph("Ist-Reifegrad", P_STYLE),
        sw_soll,
        Paragraph("Soll-Reifegrad", P_STYLE),
    ]
    t = Table([row], colWidths=[sw_w, 120, sw_w, 120])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return t


def _scale_legend_box(*, width_pt: float, BORDER, BG, TEXT, SMALL: ParagraphStyle) -> Table:
    """Skalen-Legende unten (Box) wie in Download."""
    red = "#d62728"
    html = (
        "<b>Legende:</b> "
        f'<font color="{red}"><b>1</b></font> - Initial&nbsp;&nbsp;&nbsp;'
        f'<font color="{red}"><b>2</b></font> - Gemanagt&nbsp;&nbsp;&nbsp;'
        f'<font color="{red}"><b>3</b></font> - Definiert&nbsp;&nbsp;&nbsp;'
        f'<font color="{red}"><b>4</b></font> - Quantitativ gemanagt&nbsp;&nbsp;&nbsp;'
        f'<font color="{red}"><b>5</b></font> - Optimiert'
    )
    p = Paragraph(html, SMALL)
    t = Table([[p]], colWidths=[width_pt])
    t.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("BACKGROUND", (0, 0), (-1, -1), BG),
                ("TEXTCOLOR", (0, 0), (-1, -1), TEXT),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


# ---------------------------------------------------------------------
# 1) DataFrame für Maßnahmen/Export aufbereiten (robust)
# ---------------------------------------------------------------------
def df_results_for_export(df_report: pd.DataFrame) -> pd.DataFrame:
    """Liefert eine exportfreundliche Maßnahmen-Tabelle in einheitlichen Spalten."""
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
    - Dezimal-Komma
    """
    if df is None:
        df = pd.DataFrame()

    d = df.copy()

    for col in ["Ist-Reifegrad", "Soll-Reifegrad", "Gap"]:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce")

    buf = io.StringIO()
    d.to_csv(
        buf,
        index=False,
        sep=";",
        decimal=",",
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
    - Angaben zur Erhebung
    - Kennzahlen: 2 Cards (TD/OG) wie Gesamtübersicht
    - Radar-Charts: Card-Look wie Download (Titel + Mini-Legende + Skalen-Legende unten)
    - Maßnahmen als LongTable
    - Footer: IPS Logo + Kontakte auf jeder Seite (Mail-Icon korrekt + aligned)
    """

    # Farben
    TD_BLUE = colors.HexColor("#2F3DB8")
    OG_ORANGE = colors.HexColor("#F28C28")

    # PDF-Theme (hell; dark aktuell nur für Plot-Export genutzt)
    TEXT = colors.HexColor("#111111")
    BORDER = colors.HexColor("#D1D5DB")      # gray-300
    SOFT_BG = colors.HexColor("#F3F4F6")     # gray-100
    CARD_BG = colors.white
    ZEBRA = colors.HexColor("#FAFAFA")

    buf = io.BytesIO()

    # BottomMargin höher: Platz für Logo + Textzeilen im Footer
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=26 * mm,
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
        textColor=colors.HexColor("#374151"),
    )
    
    # -----------------------------
    # Einführung: TD/OG Block (PDF) – verbessert
    # -----------------------------
    TD_BLUE_HEX = "#2F3DB8"
    OG_ORANGE_HEX = "#F28C28"

    # Layoutbreiten wie UI
    INTRO_LEFT_W = doc.width * 0.36
    INTRO_GAP_W = 9 * mm
    INTRO_RIGHT_W = doc.width - INTRO_LEFT_W - INTRO_GAP_W

    P_SEC_TITLE_TD = ParagraphStyle(
        "P_SEC_TITLE_TD",
        parent=P,
        fontName="Helvetica-Bold",
        fontSize=11.2,
        leading=14,
        textColor=colors.HexColor(TD_BLUE_HEX),
    )
    P_SEC_TITLE_OG = ParagraphStyle(
        "P_SEC_TITLE_OG",
        parent=P,
        fontName="Helvetica-Bold",
        fontSize=11.2,
        leading=14,
        textColor=colors.HexColor(OG_ORANGE_HEX),
    )
    P_SEC_DESC = ParagraphStyle(
        "P_SEC_DESC",
        parent=P,
        fontSize=10.0,
        leading=13,
        textColor=colors.HexColor("#374151"),
    )
    P_CARD_HEAD = ParagraphStyle(
        "P_CARD_HEAD",
        parent=P,
        fontName="Helvetica-Bold",
        fontSize=10.3,
        leading=13,
        alignment=1,  # center
        textColor=TEXT,
    )
    P_ITEM = ParagraphStyle(
        "P_ITEM",
        parent=P,
        fontSize=9.8,
        leading=12.4,
        textColor=TEXT,
    )
    P_BADGE = ParagraphStyle(
        "P_BADGE",
        parent=P,
        fontName="Helvetica-Bold",
        fontSize=9.0,
        leading=10.4,
        alignment=1,
    )

    def _divider_line() -> Table:
        # Ein dünner, einheitlicher Trennstrich (wie KPI-Linien)
        t = Table([[""]], colWidths=[doc.width], rowHeights=[1])  # Höhe egal, Linie kommt aus LINEBELOW
        t.setStyle(
            TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, 0), 0.6, BORDER),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        return t

    def _badge(label: str, *, fg_hex: str, tint_hex: str) -> Table:
        fg = colors.HexColor(fg_hex)
        bg = colors.HexColor(tint_hex)

        t = Table(
            [[Paragraph(_html.escape(label), ParagraphStyle(f"P_BADGE_{label}", parent=P_BADGE, textColor=fg))]],
            colWidths=[14 * mm],
            rowHeights=[6.0 * mm],
        )
        t.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1.1, fg),
                    ("BACKGROUND", (0, 0), (-1, -1), bg),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        return t

    def _intro_card(title: str, items: list[tuple[str, str]], *, border_color, card_w_pt: float) -> Table:
        badge_w = 16 * mm
        text_w = float(card_w_pt) - float(badge_w)

        # Farben pro Card (wie UI-Tints)
        if str(border_color).lower().endswith(TD_BLUE_HEX.lower().lstrip("#")):
            fg_hex = TD_BLUE_HEX
            tint_hex = "#EEF0FF"  # blau getönt
        else:
            fg_hex = OG_ORANGE_HEX
            tint_hex = "#FFF3E8"  # orange getönt

        rows: list[list[Any]] = [[Paragraph(_html.escape(title), P_CARD_HEAD), ""]]
        for code, txt in items:
            rows.append(
                [
                    _badge(code, fg_hex=fg_hex, tint_hex=tint_hex),
                    Paragraph(_html.escape(txt), P_ITEM),
                ]
            )

        t = Table(rows, colWidths=[badge_w, text_w])

        style: list[tuple] = [
            ("SPAN", (0, 0), (-1, 0)),
            ("BOX", (0, 0), (-1, -1), 1.6, border_color),
            ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, BORDER),

            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

            # allgemeine Innenabstände
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),

            # Titelzeile kompakt
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),

            # Items: wie „Chips“
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),

            # Badge-Spalte etwas enger
            ("LEFTPADDING", (0, 1), (0, -1), 4),
            ("RIGHTPADDING", (0, 1), (0, -1), 6),
        ]

        for r in range(1, len(rows) - 1):
            style.append(("BACKGROUND", (0, r), (-1, r), SOFT_BG))
            style.append(("LINEBELOW", (0, r), (-1, r), 0.6, BORDER))

        # letzte Zeile bekommt nur Background, keine Linie
        last = len(rows) - 1
        style.append(("BACKGROUND", (0, last), (-1, last), SOFT_BG))

        t.setStyle(TableStyle(style))
        return t

    def _intro_block(left_title: Paragraph, left_desc: Paragraph, right_card: Table) -> Table:
        left_flow = [left_title, Spacer(1, 1.2 * mm), left_desc]
        t = Table([[left_flow, "", right_card]], colWidths=[INTRO_LEFT_W, INTRO_GAP_W, INTRO_RIGHT_W])
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        return t

    story: list[Any] = []

    # --- Titel ---
    story.append(Paragraph("Gesamtübersicht – Reifegraderhebung", H1))

    # Accent-Line (TD/OG)
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
    story.append(Spacer(1, 4 * mm))

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

    def _meta_table(left_pairs: list[tuple[str, str]], right_pairs: list[tuple[str, str]]) -> Table:
        # gleiche Zeilenanzahl wie im UI (3 links / 3 rechts)
        n = max(len(left_pairs), len(right_pairs))
        rows: list[list[Any]] = []

        for i in range(n):
            kL, vL = left_pairs[i] if i < len(left_pairs) else ("", "")
            kR, vR = right_pairs[i] if i < len(right_pairs) else ("", "")

            rows.append(
                [
                    Paragraph(f"<b>{_html.escape(kL)}</b>", SMALL),
                    Paragraph(_html.escape(_fmt(vL)), P),
                    "",  # GAP
                    Paragraph(f"<b>{_html.escape(kR)}</b>", SMALL),
                    Paragraph(_html.escape(_fmt(vR)), P),
                ]
            )

        # --- Spaltenbreiten so, dass die Linie bis ganz rechts läuft ---
        gap_w = 12 * mm

        # Labels: an Textbreite orientiert, aber begrenzt
        maxL = max((stringWidth(k, "Helvetica-Bold", 9.0) for k, _ in left_pairs), default=0.0)
        maxR = max((stringWidth(k, "Helvetica-Bold", 9.0) for k, _ in right_pairs), default=0.0)

        labelL_w = min(max(maxL + 3 * mm, 44 * mm), doc.width * 0.34)
        labelR_w = min(max(maxR + 3 * mm, 44 * mm), doc.width * 0.34)

        values_total = float(doc.width) - float(labelL_w) - float(labelR_w) - float(gap_w)
        valueL_w = values_total / 2.0
        valueR_w = values_total / 2.0

        t = Table(rows, colWidths=[labelL_w, valueL_w, gap_w, labelR_w, valueR_w])

        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

                    # ✅ Durchgehender Trennstrich pro Zeile bis ganz rechts
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER),

                    # Werte rechtsbündig wie Formular
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("ALIGN", (4, 0), (4, -1), "RIGHT"),

                    # Paddings: sauber wie im Screenshot
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                    ("RIGHTPADDING", (0, 0), (0, -1), 10),

                    ("LEFTPADDING", (1, 0), (1, -1), 6),
                    ("RIGHTPADDING", (1, 0), (1, -1), 2),

                    ("LEFTPADDING", (2, 0), (2, -1), 0),
                    ("RIGHTPADDING", (2, 0), (2, -1), 0),

                    ("LEFTPADDING", (3, 0), (3, -1), 0),
                    ("RIGHTPADDING", (3, 0), (3, -1), 10),

                    ("LEFTPADDING", (4, 0), (4, -1), 6),
                    ("RIGHTPADDING", (4, 0), (4, -1), 0),

                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return t

    story.append(_meta_table(left, right))
    story.append(Spacer(1, 2.5 * mm))


    # --- Einführung: Bereiche (TD/OG) ---
    td_left_title = Paragraph("Technische Dokumentation (TD)", P_SEC_TITLE_TD)
    td_left_desc = Paragraph("Relevante Themenbereiche der technischen Dokumentation.", P_SEC_DESC)
    td_card = _intro_card(
        "Technische Dokumentation",
        [("TD1", "Redaktionsprozess"),
         ("TD2", "Content Management"),
         ("TD3", "Content Delivery"),
         ("TD4", "Zielgruppenorientierung")],
        border_color=TD_BLUE,
        card_w_pt=float(INTRO_RIGHT_W),
    )
    story.append(KeepTogether([_intro_block(td_left_title, td_left_desc, td_card)]))
    story.append(Spacer(1, 3 * mm))
    story.append(_divider_line())
    story.append(Spacer(1, 3 * mm))

    og_left_title = Paragraph("Organisation (OG)", P_SEC_TITLE_OG)
    og_left_desc = Paragraph(
        "Relevante Themenbereiche der Organisation, die mit der technischen Dokumentation in Verbindung stehen bzw. diese beeinflussen.",
        P_SEC_DESC,
    )
    og_card = _intro_card(
        "Organisation",
        [("OG1", "Wissensmanagement"),
         ("OG2", "Organisationale Verankerung der technischen Dokumentation"),
         ("OG3", "Schnittstellen"),
         ("OG4", "Technologische Infrastruktur")],
        border_color=OG_ORANGE,
        card_w_pt=float(INTRO_RIGHT_W),
    )
    story.append(KeepTogether([_intro_block(og_left_title, og_left_desc, og_card)]))
    story.append(Spacer(1, 3.5 * mm))

    # Trennlinie vor Kennzahlen
    story.append(Spacer(1, 2.0 * mm))
    story.append(_divider_line())
    story.append(Spacer(1, 2.2 * mm))
    
    # --- Kennzahlen (wie Gesamtübersicht: 2 Cards) ---
    story.append(Paragraph("Kennzahlen", H2))

    drep = df_report if (df_report is not None and not df_report.empty) else (df_raw.copy() if df_raw is not None else pd.DataFrame())

    td_nt, td_na, td_nn = _kpi_counts_by_prefix(drep, "TD")
    og_nt, og_na, og_nn = _kpi_counts_by_prefix(drep, "OG")

    def _kpi_card(title: str, nt: int, na: int, nn: int, border_color) -> Table:
        P_CARD = ParagraphStyle("P_CARD", parent=P, fontSize=10.0, leading=13, textColor=TEXT)
        P_LBL = ParagraphStyle("P_LBL", parent=P, fontSize=9.6, leading=12, textColor=TEXT)

        rows = [
            [Paragraph(f"<b>{_html.escape(title)}</b>", P_CARD), ""],
            [Paragraph("Bewertet", P_LBL), Paragraph(f"<b>{na} / {nt}</b>", P_LBL)],
            [Paragraph("Handlungsbedarf (Gap &gt; 0)", P_LBL), Paragraph(f"<b>{nn}</b>", P_LBL)],
        ]
        t = Table(rows, colWidths=[(doc.width * 0.48) * 0.72, (doc.width * 0.48) * 0.28])
        t.setStyle(
            TableStyle(
                [
                    ("SPAN", (0, 0), (1, 0)),
                    ("BOX", (0, 0), (-1, -1), 1.4, border_color),
                    ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                    ("LINEABOVE", (0, 1), (-1, 1), 0.6, BORDER),
                    ("LINEABOVE", (0, 2), (-1, 2), 0.6, BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return t

    gap_w = doc.width * 0.04
    card_w = (doc.width - gap_w) / 2

    card_td = _kpi_card("TD-Dimensionen", td_nt, td_na, td_nn, TD_BLUE)
    card_og = _kpi_card("OG-Dimensionen", og_nt, og_na, og_nn, OG_ORANGE)

    kpi_grid = Table([[card_td, "", card_og]], colWidths=[card_w, gap_w, card_w])
    kpi_grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(kpi_grid)

    # --- Charts (Card-Look wie Download) ---
    have_figs = (fig_td is not None) or (fig_og is not None)

    td_png, td_err = _plotly_fig_to_png_bytes(fig_td, dark_export=dark) if fig_td is not None else (None, None)
    og_png, og_err = _plotly_fig_to_png_bytes(fig_og, dark_export=dark) if fig_og is not None else (None, None)

    def _radar_card(png_bytes: bytes, title: str, border_color, fig_for_colors) -> Table:
        pad = 10
        inner_w = float(doc.width) - 2 * pad

        # Farben für Mini-Legende aus echten Traces (wie UI)
        ist_hex = _get_trace_color(fig_for_colors, 0, "#1f77b4")
        soll_hex = _get_trace_color(fig_for_colors, 1, "#ff7f0e")

        P_TITLE = ParagraphStyle("P_TITLE", parent=P, fontSize=12.0, leading=15, textColor=TEXT)
        P_LEG = ParagraphStyle("P_LEG", parent=P, fontSize=9.6, leading=12, textColor=TEXT)

        img = _scaled_rl_image(png_bytes, max_width_pt=inner_w)
        if img is None:
            inner = [Paragraph(f"{_html.escape(title)}: Plot konnte nicht eingebettet werden.", P)]
        else:
            mini_leg = _mini_legend_table(ist_hex, soll_hex, P_STYLE=P_LEG)
            scale_leg = _scale_legend_box(width_pt=inner_w, BORDER=BORDER, BG=CARD_BG, TEXT=TEXT, SMALL=SMALL)

            inner = [
                Paragraph(f"<b>{_html.escape(title)}</b>", P_TITLE),
                Spacer(1, 2),
                mini_leg,
                Spacer(1, 6),
                img,
                Spacer(1, 6),
                scale_leg,
            ]

        card = Table([[inner]], colWidths=[doc.width])
        card.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1.6, border_color),
                    ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                    ("LEFTPADDING", (0, 0), (-1, -1), pad),
                    ("RIGHTPADDING", (0, 0), (-1, -1), pad),
                    ("TOPPADDING", (0, 0), (-1, -1), pad),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return card

    if have_figs:
        story.append(PageBreak())
        story.append(Paragraph("Visualisiertes Ergebnis der Reifegraderhebung", H2))
        story.append(Spacer(1, 3 * mm))

        # TD (eigene Seite, groß)
        if fig_td is not None:
            if td_png:
                story.append(KeepTogether([_radar_card(td_png, "TD-Dimensionen", TD_BLUE, fig_td), Spacer(1, 4 * mm)]))
                story.append(PageBreak())
            else:
                story.append(_p(f"TD-Dimensionen: Plot-Export fehlgeschlagen: {_fmt(td_err)}", P))
                story.append(Spacer(1, 4 * mm))

        # OG
        if fig_og is not None:
            if og_png:
                story.append(KeepTogether([_radar_card(og_png, "OG-Dimensionen", OG_ORANGE, fig_og), Spacer(1, 4 * mm)]))
                story.append(PageBreak())
            else:
                story.append(_p(f"OG-Dimensionen: Plot-Export fehlgeschlagen: {_fmt(og_err)}", P))
                story.append(Spacer(1, 4 * mm))

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

        # Ist & Gap als Dezimalwerte ausgeben
        for c in ["Ist-Reifegrad", "Gap"]:
            if c in d.columns:
                d[c] = d[c].apply(lambda x: _to_float_str(x, decimals=2, decimal_comma=True))

        # Soll bleibt typischerweise ganzzahlig
        if "Soll-Reifegrad" in d.columns:
            d["Soll-Reifegrad"] = d["Soll-Reifegrad"].apply(_to_int_str)

        # --- Extrem lange Textzellen splitten ---
        wrap_cols = {"Maßnahme", "Verantwortlich", "Zeitraum"}
        chunk_limits = {"Maßnahme": 700, "Verantwortlich": 220, "Zeitraum": 120}

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

        P_TAB = ParagraphStyle("P_TAB", parent=P, fontSize=9.2, leading=12, textColor=TEXT)

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

    # Footer rechts: Organisation (optional)
    org_right = _fmt(meta.get("org", ""), dash="").strip()

    doc.build(
        story,
        onFirstPage=lambda canv, d: _page_footer(canv, d, org_right=org_right),
        onLaterPages=lambda canv, d: _page_footer(canv, d, org_right=org_right),
    )

    return buf.getvalue()
