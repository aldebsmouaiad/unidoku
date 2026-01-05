# /workspaces/unidoku/pages/05_Gesamtuebersicht.py
from __future__ import annotations

import streamlit as st
import pandas as pd

from core.state import init_session_state
from core.model_loader import load_model_config
from core.overview import build_overview_table
from core.charts import radar_ist_soll
from core.exporter import df_results_for_export, make_csv_bytes, make_pdf_bytes


def get_answers():
    return st.session_state.get("answers", {})


def _clean_overview_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Bereinigt die Overview-Tabelle für Reporting (KPI/Maßnahmen/Export):
    - ist_level <= 0 oder NaN => "nicht bewertet" (NaN)
    - target_level <= 0 oder NaN => NaN
    - gap neu berechnen
    - negative gaps auf 0
    - answered Flag
    """
    d = df.copy()

    if "ist_level" in d.columns:
        d["ist_level"] = pd.to_numeric(d["ist_level"], errors="coerce")
        d.loc[d["ist_level"].isna() | (d["ist_level"] <= 0), "ist_level"] = pd.NA

    if "target_level" in d.columns:
        d["target_level"] = pd.to_numeric(d["target_level"], errors="coerce")
        d.loc[d["target_level"].isna() | (d["target_level"] <= 0), "target_level"] = pd.NA

    if "ist_level" in d.columns and "target_level" in d.columns:
        d["gap"] = d["target_level"] - d["ist_level"]
        d.loc[d["gap"].notna() & (d["gap"] < 0), "gap"] = 0.0

    d["answered"] = d.get("ist_level").notna() if "ist_level" in d.columns else False
    return d


def _kpi_block(df: pd.DataFrame) -> int:
    """
    KPIs berechnen nur auf bewerteten Dimensionen (damit ØIst nicht verfälscht wird).
    """
    if df.empty:
        return 0

    d = df.copy()
    n_total = len(d)
    n_answered = int(d["answered"].sum()) if "answered" in d.columns else 0
    d_ans = d[d["answered"]].copy() if n_answered else d.iloc[0:0].copy()

    n_need = int(
        (pd.to_numeric(d_ans.get("gap", 0), errors="coerce").fillna(0.0) > 0).sum()
    ) if n_answered else 0

    if n_answered:
        avg_ist = float(pd.to_numeric(d_ans["ist_level"], errors="coerce").mean())
        avg_soll = float(pd.to_numeric(d_ans["target_level"], errors="coerce").mean())
        max_gap = float(pd.to_numeric(d_ans["gap"], errors="coerce").max())
    else:
        avg_ist = 0.0
        avg_soll = float(
            pd.to_numeric(d["target_level"], errors="coerce").dropna().mean()
        ) if "target_level" in d.columns else 0.0
        max_gap = 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Dimensionen", f"{n_total}")
    c2.metric("Bewertet", f"{n_answered} / {n_total}")
    c3.metric("Handlungsbedarf (Gap > 0)", f"{n_need}")
    c4.metric("Ø Ist / Ø Soll", f"{avg_ist:.2f} / {avg_soll:.2f}")
    c5.metric("Max. Gap", f"{max_gap:.2f}")

    return n_answered


def _scale_legend_centered() -> None:
    st.markdown(
        """
        <style>
          .rgm-legend-wrap { display:flex; justify-content:center; margin-top: 10px; }
          .rgm-legend-box {
            padding: 8px 14px;
            border: 1px solid rgba(0,0,0,0.10);
            border-radius: 10px;
            background: rgba(255,255,255,0.90);
            font-size: 14px;
            line-height: 1.4;
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            align-items: center;
          }
          .rgm-legend-box .rgm-num { color: #d62728 !important; font-weight: 700 !important; }
        </style>

        <div class="rgm-legend-wrap">
          <div class="rgm-legend-box">
            <span style="font-weight:600;">Legende:</span>
            <span><span class="rgm-num">1</span> - Initial</span>
            <span><span class="rgm-num">2</span> - Gemanagt</span>
            <span><span class="rgm-num">3</span> - Definiert</span>
            <span><span class="rgm-num">4</span> - Quantitativ gemanagt</span>
            <span><span class="rgm-num">5</span> - Optimiert</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _pick_first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def main():
    init_session_state()

    st.title("Gesamtübersicht")
    st.caption("Zusammenfassung der Angaben zur Erhebung, visualisierte Ergebnisse und geplante Maßnahmen.")
    st.markdown("---")

    model = load_model_config()
    answers = get_answers()
    global_target = st.session_state.get("global_target_level", 3.0)
    dim_targets = st.session_state.get("dimension_targets", {})
    priorities = st.session_state.get("priorities", {})
    meta = st.session_state.get("meta", {}) or {}

    # 1) Rohdaten wie im Dashboard
    df_raw = build_overview_table(
        model=model,
        answers=answers,
        global_target_level=global_target,
        per_dimension_targets=dim_targets,
        priorities=priorities,
    )

    if df_raw.empty:
        st.info("Noch keine Ergebnisse vorhanden – bitte zuerst die Erhebung durchführen.")
        return

    # 2) Bereinigte Daten NUR für KPI/Maßnahmen/Export
    df_report = _clean_overview_df(df_raw)

    # --------------------------------
    # 1) Angaben zur Erhebung
    # --------------------------------
    a1, a2 = st.columns(2)
    with a1:
        st.write(f"**Name der Organisation:** {meta.get('org','') or '-'}")
        st.write(f"**Bereich:** {meta.get('area','') or '-'}")
        st.write(f"**Erhebung durchgeführt von:** {meta.get('assessor','') or '-'}")
    with a2:
        st.write(f"**Datum der Durchführung:** {meta.get('date_str','') or '-'}")
        st.write(f"**Angestrebtes Ziel:** {meta.get('target_label','') or '-'}")
        st.write(f"**Soll-Niveau (global):** {float(global_target):.1f}")

    st.markdown("")
    n_answered = _kpi_block(df_report)

    if n_answered == 0:
        st.warning("Noch keine Dimensionen bewertet.")
        if st.button("Zur Erhebung", type="primary", use_container_width=True):
            st.session_state["nav_request"] = "Erhebung"
            st.rerun()

    st.markdown("---")

    # --------------------------------
    # 2) Graphen (Netzdiagramme) – EXAKT WIE DASHBOARD
    # --------------------------------
    st.subheader("Visualisiertes Ergebnis der Reifegraderhebung")

    # WICHTIG: Für Charts ausschließlich df_raw verwenden (keine Bereinigung/Umbenennung)
    df_chart = df_raw

    plotly_cfg = {
        "displayModeBar": "hover",
        "displaylogo": False,
        "scrollZoom": False,
        "doubleClick": False,
        "editable": False,
        "responsive": True,
        "modeBarButtonsToRemove": [
            "zoom2d", "pan2d", "select2d", "lasso2d",
            "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d",
        ],
        "toImageButtonOptions": {
            "format": "png",
            "filename": "reifegrad_radar",
            "scale": 2,
        },
    }

    c1, c2 = st.columns(2)
    with c1:
        fig_td = radar_ist_soll(df_chart, category="TD", title="TD-Dimensionen")
        if fig_td:
            st.plotly_chart(fig_td, use_container_width=True, config=plotly_cfg)
        else:
            st.info("Keine TD-Daten vorhanden.")

    with c2:
        fig_og = radar_ist_soll(df_chart, category="OG", title="OG-Dimensionen")
        if fig_og:
            st.plotly_chart(fig_og, use_container_width=True, config=plotly_cfg)
        else:
            st.info("Keine OG-Daten vorhanden.")

    _scale_legend_centered()
    st.markdown("---")

    # --------------------------------
    # 3) Maßnahmen
    # --------------------------------
    st.subheader("Geplante Maßnahmen")

    df_export = df_results_for_export(df_report)
    m = df_export.copy()

    m["Gap"] = pd.to_numeric(m.get("Gap", pd.NA), errors="coerce")

    ist_col = _pick_first_col(m, ["Ist-Reifegrad", "Ist", "Ist Level", "Ist-Level", "ist_level"])
    soll_col = _pick_first_col(m, ["Soll-Reifegrad", "Soll", "Soll Level", "Soll-Level", "target_level"])

    if ist_col is not None and ist_col != "Ist-Reifegrad":
        m["Ist-Reifegrad"] = pd.to_numeric(m[ist_col], errors="coerce")
    elif "Ist-Reifegrad" not in m.columns:
        m["Ist-Reifegrad"] = pd.NA

    if soll_col is not None and soll_col != "Soll-Reifegrad":
        m["Soll-Reifegrad"] = pd.to_numeric(m[soll_col], errors="coerce")
    elif "Soll-Reifegrad" not in m.columns:
        m["Soll-Reifegrad"] = pd.NA

    need = m["Gap"].fillna(-1) > 0

    show_all = st.checkbox("Alle anzeigen (inkl. ohne Handlungsbedarf)", value=False)

    f1, f2 = st.columns([1.2, 1.0])
    with f1:
        prio_filter = st.multiselect(
            "Priorität filtern",
            ["A (hoch)", "B (mittel)", "C (niedrig)"],
            default=[],
        )
    with f2:
        st.caption("Standard: nur Handlungsbedarf (Gap > 0)." if not show_all else "Hinweis: Es werden alle Dimensionen angezeigt.")

    filtered = m.copy() if show_all else m[need].copy()

    if prio_filter and "Priorität" in filtered.columns:
        filtered = filtered[filtered["Priorität"].isin(prio_filter)].copy()

    if filtered.empty:
        st.info("Keine Einträge passend zur aktuellen Auswahl.")
    else:
        prio_rank = {"A (hoch)": 0, "B (mittel)": 1, "C (niedrig)": 2, "": 9}
        if "Priorität" in filtered.columns:
            filtered["_prio_rank"] = filtered["Priorität"].map(lambda x: prio_rank.get(str(x), 9))
        else:
            filtered["_prio_rank"] = 9

        filtered["_gap_sort"] = filtered["Gap"].fillna(-1)
        filtered = filtered.sort_values(["_prio_rank", "_gap_sort"], ascending=[True, False])

        cols = [
            "Priorität",
            "Kürzel",
            "Themenbereich",
            "Ist-Reifegrad",
            "Soll-Reifegrad",
            "Gap",
            "Maßnahme",
            "Zeitraum",
        ]
        cols = [c for c in cols if c in filtered.columns]

        st.dataframe(
            filtered[cols],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    # --------------------------------
    # 4) Export (CSV + PDF)
    # --------------------------------
    st.subheader("Export")

    csv_bytes = make_csv_bytes(df_export)

    pdf_bytes = None
    pdf_error = None
    try:
        meta_pdf = dict(meta)
        meta_pdf["global_target"] = f"{float(global_target):.1f}"

        # Wichtig: Für konsistente Charts/Logik im PDF ebenfalls df_raw übergeben
        pdf_bytes = make_pdf_bytes(meta=meta_pdf, df_raw=df_raw)

    except Exception as e:
        pdf_error = str(e)

    ex1, ex2 = st.columns(2)
    with ex1:
        st.download_button(
            "CSV herunterladen",
            data=csv_bytes,
            file_name="reifegrad_gesamtuebersicht.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with ex2:
        if pdf_bytes is not None:
            st.download_button(
                "PDF-Bericht herunterladen",
                data=pdf_bytes,
                file_name="reifegrad_gesamtuebersicht.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.error(f"PDF-Export nicht verfügbar: {pdf_error}")

    st.markdown("---")
    if st.button("Weiter → Dashboard", type="primary", use_container_width=True):
        st.session_state["nav_request"] = "Dashboard"
        st.rerun()


if __name__ == "__main__":
    main()
