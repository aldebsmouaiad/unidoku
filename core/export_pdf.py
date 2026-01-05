# core/export_pdf.py
# PDF-Bericht mit FPDF erzeugen

from typing import Dict, Any

import numpy as np
import pandas as pd
from fpdf import FPDF


def _safe_text(s: Any) -> str:
    """
    FPDF (Standard Helvetica) nutzt latin-1. Umlaute/ß gehen, aber nicht alle Unicode-Zeichen.
    Wir ersetzen nicht darstellbare Zeichen, damit der PDF-Export nie crasht.
    """
    txt = str(s) if s is not None else "-"
    return txt.encode("latin-1", errors="replace").decode("latin-1")


def _is_na_value(x: Any) -> bool:
    """
    True wenn x als n/a zu interpretieren ist:
    - NaN/None
    - "n.a." / "na" / "#N/A" (string)
    """
    if x is None:
        return True
    if isinstance(x, float) and np.isnan(x):
        return True
    try:
        if pd.isna(x):
            return True
    except Exception:
        pass

    if isinstance(x, str):
        t = x.strip().lower()
        return t in {"n.a.", "na", "n/a", "#n/a", "#na", "n.a", "nan"}
    return False


def _fmt_num(x: Any, decimals: int = 2, na_text: str = "n.a.") -> str:
    """
    Formatiert numerische Werte robust.
    Akzeptiert float/int oder string, und gibt bei n/a den Text zurück.
    """
    if _is_na_value(x):
        return na_text

    # Falls String numerisch ist
    if isinstance(x, str):
        try:
            x = float(x.replace(",", "."))
        except Exception:
            return na_text

    try:
        val = float(x)
    except Exception:
        return na_text

    if np.isnan(val):
        return na_text

    return f"{val:.{decimals}f}"


def _fmt_int(x: Any, na_text: str = "n.a.") -> str:
    """
    Formatiert Soll-Level typischerweise als ganze Zahl (Stufe).
    """
    if _is_na_value(x):
        return na_text

    if isinstance(x, str):
        try:
            x = float(x.replace(",", "."))
        except Exception:
            return na_text

    try:
        return f"{int(float(x))}"
    except Exception:
        return na_text


class SimplePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, _safe_text("Reifegradbericht Technische Dokumentation"), ln=True)
        self.ln(2)


def export_pdf_bytes(
    df_export: pd.DataFrame,
    overall: Dict[str, Any],
    org: str,
    assessor: str,
    date_str: str,
    target_label: str,
    area: str = "",  # neu: Bereich (optional, um Call-Sites nicht sofort zu brechen)
) -> bytes:
    """
    Erzeugt einen einfachen PDF-Bericht.

    Erwartet df_export im Format von build_export_dataframe(), z. B.:
      - Code, Dimension, Kategorie, Ist_Level, Ziel_Level, Gap
      - Priorität, Maßnahme, Zeitraum

    overall kann enthalten:
      - overall_ist
      - overall_ist_level
      - overall_ist_text
      - overall_target
    """
    pdf = SimplePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Kopf-Metadaten
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, _safe_text(f"Organisation: {org or '-'}"), ln=True)
    pdf.cell(0, 8, _safe_text(f"Bereich: {area or '-'}"), ln=True)  # neu
    pdf.cell(0, 8, _safe_text(f"Bewertet von: {assessor or '-'}"), ln=True)
    pdf.cell(0, 8, _safe_text(f"Datum: {date_str or '-'}"), ln=True)
    pdf.cell(0, 8, _safe_text(f"Globales Ziel: {target_label or '-'}"), ln=True)
    pdf.ln(4)

    # Zusammenfassung
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _safe_text("Zusammenfassung"), ln=True)
    pdf.set_font("Helvetica", "", 11)

    overall_ist = overall.get("overall_ist", np.nan)
    if not _is_na_value(overall_ist):
        ist_txt = _fmt_num(overall_ist, decimals=2)
        lvl_txt = _fmt_int(overall.get("overall_ist_level", np.nan))
        desc_txt = _safe_text(overall.get("overall_ist_text", "-"))
        pdf.cell(0, 6, _safe_text(f"Gesamt-Reifegrad (Ist): {ist_txt} (Stufe {lvl_txt} – {desc_txt})"), ln=True)
    else:
        pdf.cell(0, 6, _safe_text("Gesamt-Reifegrad (Ist): n.a."), ln=True)

    overall_target = overall.get("overall_target", np.nan)
    if not _is_na_value(overall_target):
        pdf.cell(0, 6, _safe_text(f"Gesamt-Sollniveau: Stufe {_fmt_int(overall_target)}"), ln=True)
    else:
        pdf.cell(0, 6, _safe_text("Gesamt-Sollniveau: n.a."), ln=True)

    pdf.ln(6)

    # Tabellenkopf
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _safe_text("Dimensionen (Ist / Soll / Gap / Priorität)"), ln=True)

    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(18, 5, _safe_text("Code"), border=1)
    pdf.cell(52, 5, _safe_text("Dimension"), border=1)
    pdf.cell(12, 5, _safe_text("Ist"), border=1)
    pdf.cell(12, 5, _safe_text("Soll"), border=1)
    pdf.cell(12, 5, _safe_text("Gap"), border=1)
    pdf.cell(16, 5, _safe_text("Prio"), border=1)
    pdf.cell(60, 5, _safe_text("Maßnahme"), border=1, ln=True)

    # Tabelleninhalt
    pdf.set_font("Helvetica", "", 8)

    for _, row in df_export.iterrows():
        code = _safe_text(row.get("Code", ""))
        name = _safe_text(row.get("Dimension", ""))[:30]

        ist = row.get("Ist_Level", np.nan)
        soll = row.get("Ziel_Level", np.nan)
        gap = row.get("Gap", np.nan)

        prio = _safe_text(row.get("Priorität", ""))
        measure = _safe_text(row.get("Maßnahme", ""))[:40]

        pdf.cell(18, 5, code, border=1)
        pdf.cell(52, 5, name, border=1)
        pdf.cell(12, 5, _safe_text(_fmt_num(ist, decimals=2, na_text="n.a.")), border=1)
        pdf.cell(12, 5, _safe_text(_fmt_int(soll, na_text="n.a.")), border=1)
        pdf.cell(12, 5, _safe_text(_fmt_num(gap, decimals=2, na_text="n.a.")), border=1)
        pdf.cell(16, 5, prio, border=1)
        pdf.cell(60, 5, measure, border=1, ln=True)

    # PDF als Bytes zurückgeben
    return pdf.output(dest="S").encode("latin-1", errors="replace")
