# core/export_pdf.py
# PDF-Bericht mit FPDF erzeugen

from typing import Dict

import numpy as np
import pandas as pd
from fpdf import FPDF


class SimplePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Reifegradbericht Technische Dokumentation", ln=True)
        self.ln(2)


def export_pdf_bytes(
    df_export: pd.DataFrame,
    overall: Dict[str, float],
    org: str,
    assessor: str,
    date_str: str,
    target_label: str,
) -> bytes:
    """
    Erzeugt einen einfachen PDF-Bericht.

    Erwartet df_export im Format von build_export_dataframe(), also z. B.:
      - Organisation
      - Bewertet_von
      - Datum
      - Globales_Ziel_Label
      - Code
      - Dimension
      - Kategorie
      - Ist_Level
      - Ziel_Level
      - Gap
      - Priorität
      - Maßnahme
      - Zeitraum

    'overall' sollte u. a. enthalten:
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
    pdf.cell(0, 8, f"Organisation: {org or '-'}", ln=True)
    pdf.cell(0, 8, f"Bewertet von: {assessor or '-'}", ln=True)
    pdf.cell(0, 8, f"Datum: {date_str}", ln=True)
    pdf.cell(0, 8, f"Globales Ziel: {target_label}", ln=True)
    pdf.ln(4)

    # Zusammenfassung
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Zusammenfassung", ln=True)
    pdf.set_font("Helvetica", "", 11)

    overall_ist = overall.get("overall_ist", np.nan)
    if not np.isnan(overall_ist):
        pdf.cell(
            0,
            6,
            (
                f"Gesamt-Reifegrad (Ist): {overall_ist:.2f} "
                f"(Stufe {int(overall.get('overall_ist_level', 0))} "
                f"– {overall.get('overall_ist_text', '-')})"
            ),
            ln=True,
        )
    else:
        pdf.cell(0, 6, "Gesamt-Reifegrad (Ist): n/a", ln=True)

    overall_target = overall.get("overall_target", np.nan)
    if not np.isnan(overall_target):
        pdf.cell(
            0,
            6,
            f"Gesamt-Sollniveau: Stufe {int(overall_target)}",
            ln=True,
        )
    else:
        pdf.cell(0, 6, "Gesamt-Sollniveau: n/a", ln=True)

    pdf.ln(6)

    # Tabellenkopf
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Dimensionen (Ist / Soll / Gap / Priorität)", ln=True)

    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(18, 5, "Code", border=1)
    pdf.cell(52, 5, "Dimension", border=1)
    pdf.cell(12, 5, "Ist", border=1)
    pdf.cell(12, 5, "Soll", border=1)
    pdf.cell(12, 5, "Gap", border=1)
    pdf.cell(16, 5, "Prio", border=1)
    pdf.cell(60, 5, "Maßnahme", border=1, ln=True)

    # Tabelleninhalt
    pdf.set_font("Helvetica", "", 8)
    for _, row in df_export.iterrows():
        code = str(row.get("Code", ""))
        name = str(row.get("Dimension", ""))[:30]

        ist = row.get("Ist_Level", np.nan)
        soll = row.get("Ziel_Level", np.nan)
        gap = row.get("Gap", np.nan)

        prio = str(row.get("Priorität", ""))
        measure = str(row.get("Maßnahme", ""))[:40]

        pdf.cell(18, 5, code, border=1)
        pdf.cell(52, 5, name, border=1)
        pdf.cell(12, 5, f"{ist:.2f}" if not pd.isna(ist) else "-", border=1)
        pdf.cell(12, 5, f"{soll:.0f}" if not pd.isna(soll) else "-", border=1)
        pdf.cell(12, 5, f"{gap:.2f}" if not pd.isna(gap) else "-", border=1)
        pdf.cell(16, 5, prio, border=1)
        pdf.cell(60, 5, measure, border=1, ln=True)

    # PDF als Bytes zurückgeben
    return pdf.output(dest="S").encode("latin-1")
