# /workspaces/unidoku/pages/03_Priorisierung.py
from __future__ import annotations

import copy
import json

import streamlit as st

from core.model_loader import load_model_config
from core.overview import build_overview_table
from core.state import init_session_state


PRIORITY_OPTIONS = ["", "A (hoch)", "B (mittel)", "C (niedrig)"]


def get_answers() -> dict:
    return st.session_state.get("answers", {}) or {}


def after_dash(text: str) -> str:
    """
    Gibt nur den Teil nach dem ersten '-' zurück (getrimmt).
    Beispiel: 'Wissensmanagement - Wissensspeicherung' -> 'Wissensspeicherung'
    """
    s = "" if text is None else str(text)
    return s.split("-", 1)[1].strip() if "-" in s else s.strip()


def _stable_json(obj: dict) -> str:
    """Stabiler Vergleich für Dicts (Dirty-Check)."""
    return json.dumps(obj or {}, sort_keys=True, ensure_ascii=False)


def collect_priorities_from_session(codes: list[str], keep_existing: dict) -> dict:
    """
    Baut ein priorities-dict aus den aktuellen Widget-Werten in st.session_state.
    - codes: alle Dimension-Codes, die in dieser Ansicht gerendert wurden
    - keep_existing: vorhandene Werte, die erhalten bleiben sollen (z.B. nicht gerenderte Codes)
    """
    new_priorities = dict(keep_existing) if isinstance(keep_existing, dict) else {}

    for code in codes:
        prio = st.session_state.get(f"prio_{code}", "") or ""
        action = st.session_state.get(f"action_{code}", "") or ""
        timeframe = st.session_state.get(f"timeframe_{code}", "") or ""

        if prio or action or timeframe:
            new_priorities[code] = {
                "priority": prio,
                "action": action,
                "timeframe": timeframe,
            }
        else:
            new_priorities.pop(code, None)

    return new_priorities


def main() -> None:
    init_session_state()

    st.title("Priorisierung & Maßnahmenplanung")
    st.caption("Legen Sie für jede Dimension fest, wie wichtig sie ist und welche konkreten Maßnahmen Sie angehen möchten.")
    st.markdown("---")

    model = load_model_config()

    answers = get_answers()
    global_target = float(st.session_state.get("global_target_level", 3.0))
    dim_targets = st.session_state.get("dimension_targets", {}) or {}

    # committed = offiziell übernommene Werte
    priorities_committed = st.session_state.get("priorities", {}) or {}

    # Draft/Committed einmalig initialisieren
    if "priorities_draft" not in st.session_state:
        st.session_state["priorities_draft"] = copy.deepcopy(priorities_committed)
    if "priorities_committed" not in st.session_state:
        st.session_state["priorities_committed"] = copy.deepcopy(priorities_committed)

    df = build_overview_table(
        model=model,
        answers=answers,
        global_target_level=global_target,
        per_dimension_targets=dim_targets,
        priorities=priorities_committed,
    )

    if df is None or df.empty:
        st.info("Noch keine Ergebnisse vorhanden – bitte zuerst die Erhebung durchführen.")
        return

    df = df.copy()
    df["name_short"] = df["name"].apply(after_dash)

    # Filter
    c1, c2 = st.columns([1, 1])
    with c1:
        cat = st.selectbox("Kategorie", options=["Alle", "TD", "OG"], index=0)
    with c2:
        show_all = st.checkbox("Alle Dimensionen anzeigen (auch Gap ≤ 0)", value=False)

    df_view = df.copy()
    if cat != "Alle":
        df_view = df_view[df_view["category"] == cat]
    if not show_all:
        df_view = df_view[df_view["gap"] > 0]

    # -----------------------------
    # Eingaben (Draft) – ohne Form
    # -----------------------------
    rendered_codes: list[str] = []
    draft = st.session_state.get("priorities_draft", {}) or {}

    if df_view.empty:
        st.info("Keine Dimensionen mit Handlungsbedarf (Gap > 0) in der aktuellen Filterauswahl.")
    else:
        for _, row in df_view.iterrows():
            code = str(row["code"])
            name_short = str(row["name_short"])
            gap = float(row["gap"])
            rendered_codes.append(code)

            prev = draft.get(code, {})
            prev_prio = prev.get("priority", "")
            prev_action = prev.get("action", "")
            prev_time = prev.get("timeframe", "")

            try:
                default_index = PRIORITY_OPTIONS.index(prev_prio)
            except ValueError:
                default_index = 0

            with st.expander(f"{code} – {name_short}", expanded=(gap >= 1.0)):
                st.caption(f"Gap (Soll–Ist): **{gap:.2f}** Reifegradstufen")

                col1, col2, col3 = st.columns([1, 3, 2])

                with col1:
                    st.selectbox(
                        "Priorität",
                        options=PRIORITY_OPTIONS,
                        index=default_index,
                        key=f"prio_{code}",
                    )

                with col2:
                    st.text_input(
                        "Maßnahme",
                        value=prev_action,
                        key=f"action_{code}",
                        placeholder="z. B. Redaktionsleitfaden erstellen",
                    )

                with col3:
                    st.text_input(
                        "Zeitraum",
                        value=prev_time,
                        key=f"timeframe_{code}",
                        placeholder="z. B. Q1/2026",
                    )

        # Draft aus Widgets aktualisieren
        st.session_state["priorities_draft"] = collect_priorities_from_session(
            codes=rendered_codes,
            keep_existing=st.session_state.get("priorities_draft", {}),
        )

    # Dirty-Check
    draft_now = st.session_state.get("priorities_draft", {}) or {}
    committed_now = st.session_state.get("priorities_committed", {}) or {}
    dirty = _stable_json(draft_now) != _stable_json(committed_now)

    # -----------------------------
    # FOOTER-BEREICH (stabil wie im Screenshot)
    # 1) Übernehmen-Leiste
    # 2) Button-Zeile (Zurück/Weiter) bleibt unverändert
    # 3) Hinweis UNTER der Button-Zeile (verschiebt keine Buttons)
    # -----------------------------
    # st.markdown("---")

    if st.button(
        "Priorisierungen übernehmen",
        type="primary",
        use_container_width=True,
        disabled=not dirty,
    ):
        st.session_state["priorities"] = copy.deepcopy(draft_now)
        st.session_state["priorities_committed"] = copy.deepcopy(draft_now)
        st.success("Priorisierungen wurden übernommen.")
        st.rerun()

    # Hinweis kommt danach (unter den Buttons) -> Buttons springen nicht
    if dirty:
        st.warning(
            "Sie haben Priorisierungen geändert, die noch nicht übernommen wurden. "
            "Bitte zuerst „Priorisierungen übernehmen“ klicken, damit diese Werte verwendet werden."
        )

    st.markdown("---")

    left, right = st.columns([1, 1])

    with left:
        if st.button("← Zurück", use_container_width=True):
            st.session_state["nav_request"] = "Dashboard"
            st.rerun()

    with right:
        if st.button(
            "Weiter zu Gesamtübersicht",
            type="primary",
            use_container_width=True,
            disabled=dirty,
        ):
            st.session_state["nav_request"] = "Gesamtübersicht"
            st.rerun()

    


if __name__ == "__main__":
    main()
