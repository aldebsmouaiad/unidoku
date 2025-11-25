# pages/02_Dashboard.py
# Radarplots, Tabellen & Export

from datetime import datetime

import streamlit as st

from core.model_loader import load_model
from core.state import ensure_session_state, render_sidebar_meta
from core.scoring import compute_results
from core.charts import create_radar_ist_soll
from core.export_csv import build_export_dataframe, export_csv_bytes
from core.export_pdf import export_pdf_bytes


def ensure_results():
    model = load_model()
    meta = st.session_state.meta
    if st.session_state.df_dim is None:
        df_dim, df_cat, overall = compute_results(
            model=model,
            answers=st.session_state.answers,
            global_target_level=meta["target_level"],
            dimension_targets=st.session_state.dimension_targets,
        )
        st.session_state.df_dim = df_dim
        st.session_state.df_cat = df_cat
        st.session_state.overall = overall


def main():
    ensure_session_state()
    meta = render_sidebar_meta()
    ensure_results()

    df_dim = st.session_state.df_dim
    df_cat = st.session_state.df_cat
    overall = st.session_state.overall

    st.title("Dashboard – Auswertung")

    if df_dim is None or df_dim.empty:
        st.info("Noch keine Ergebnisse vorhanden. Bitte zuerst die Erhebung ausfüllen.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Gesamt-Reifegrad (Ist)",
            f"{overall['overall_ist']:.2f}",
            help=f"Stufe {int(overall['overall_ist_level'])} – {overall['overall_ist_text']}",
        )
    with col2:
        st.metric(
            "Globales Sollniveau",
            f"Stufe {meta['target_level']} ({meta['target_label']})",
        )
    with col3:
        st.metric("Anzahl Dimensionen", len(df_dim))

    st.markdown("### Radarplots")

    col_td, col_og = st.columns(2)
    with col_td:
        td_df = df_dim[df_dim["Kategorie"] == "TD"]
        st.subheader("TD-Dimensionen")
        if td_df.empty:
            st.info("Keine TD-Dimensionen im Modell.")
        else:
            fig_td = create_radar_ist_soll(td_df, "TD – Ist vs. Soll")
            st.plotly_chart(fig_td, use_container_width=True)

    with col_og:
        og_df = df_dim[df_dim["Kategorie"] == "OG"]
        st.subheader("OG-Dimensionen")
        if og_df.empty:
            st.info("Keine OG-Dimensionen im Modell.")
        else:
            fig_og = create_radar_ist_soll(og_df, "OG – Ist vs. Soll")
            st.plotly_chart(fig_og, use_container_width=True)

    st.markdown("### Tabelle der Dimensionen")

    st.dataframe(
        df_dim[["Code", "Name", "Kategorie", "Ist", "Soll", "Gap", "Ist_Text"]]
        .sort_values(["Kategorie", "Code"])
        .style.format({"Ist": "{:.2f}", "Soll": "{:.0f}", "Gap": "{:+.2f}"})
    )

    st.markdown("---")
    st.markdown("### Export")

    df_export = build_export_dataframe(
        df_dim=df_dim,
        priorities_df=st.session_state.priorities_df,
        org=str(meta["organisation"]),
        assessor=str(meta["assessor"]),
        date_str=meta["date"].strftime("%d.%m.%Y"),
        target_label=str(meta["target_label"]),
    )

    csv_bytes = export_csv_bytes(df_export)
    pdf_bytes = export_pdf_bytes(
        df_export=df_export,
        overall=overall,
        org=str(meta["organisation"]),
        assessor=str(meta["assessor"]),
        date_str=meta["date"].strftime("%d.%m.%Y"),
        target_label=str(meta["target_label"]),
    )

    col_csv, col_pdf = st.columns(2)
    with col_csv:
        st.download_button(
            label="📄 CSV herunterladen",
            data=csv_bytes,
            file_name=f"reifegrad_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
    with col_pdf:
        st.download_button(
            label="📕 PDF herunterladen",
            data=pdf_bytes,
            file_name=f"reifegrad_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
        )

    st.caption("Hinweis: Die App speichert keine Daten dauerhaft. Bitte CSV/PDF lokal sichern.")


if __name__ == "__main__":
    main()
