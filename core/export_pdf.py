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
    pdf = SimplePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Organisation: {org or '-'}", ln=True)
    pdf.cell(0, 8, f"Bewertet von: {assessor or '-'}", ln=True)
    pdf.cell(0, 8, f"Datum: {date_str}", ln=True)
    pdf.cell(0, 8, f"Globales Ziel: {target_label}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Zusammenfassung", ln=True)
    pdf.set_font("Helvetica", "", 11)

    if not np.isnan(overall["overall_ist"]):
        pdf.cell(
            0,
            6,
            f"Gesamt-Reifegrad (Ist): {overall['overall_ist']:.2f} "
            f"(Stufe {int(overall['overall_ist_level'])} – {overall['overall_ist_text']})",
            ln=True,
        )
    else:
        pdf.cell(0, 6, "Gesamt-Reifegrad (Ist): n/a", ln=True)

    pdf.cell(
        0,
        6,
        f"Gesamt-Sollniveau: Stufe {int(overall['overall_target'])}",
        ln=True,
    )
    pdf.ln(6)

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

    pdf.set_font("Helvetica", "", 8)
    for _, row in df_export.iterrows():
        name = str(row["Name"])[:30]
        measure = str(row.get("Maßnahme", ""))[:40]
        pdf.cell(18, 5, str(row["Code"]), border=1)
        pdf.cell(52, 5, name, border=1)
        pdf.cell(12, 5, f"{row['Ist']:.2f}" if not np.isnan(row["Ist"]) else "-", border=1)
        pdf.cell(12, 5, f"{row['Soll']:.0f}", border=1)
        pdf.cell(12, 5, f"{row['Gap']:.2f}" if not np.isnan(row["Gap"]) else "-", border=1)
        pdf.cell(16, 5, str(row.get("Priorität", "")), border=1)
        pdf.cell(60, 5, measure, border=1, ln=True)

    return pdf.output(dest="S").encode("latin-1")
