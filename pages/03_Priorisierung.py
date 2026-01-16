# /workspaces/unidoku/pages/03_Priorisierung.py
from __future__ import annotations

import copy
import json

import streamlit as st

from core.model_loader import load_model_config
from core.overview import build_overview_table
from core.state import init_session_state

TU_ORANGE = "#CA7406"
TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"

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
        responsible = st.session_state.get(f"resp_{code}", "") or ""

        if prio or action or timeframe or responsible:
            new_priorities[code] = {
                "priority": prio,
                "action": action,
                "timeframe": timeframe,
                "responsible": responsible,
            }
        else:
            new_priorities.pop(code, None)

    return new_priorities


def _inject_priorisierung_css() -> None:
    """Einheitliches Design (wie Einführung/Ausfüllhinweise) für Priorisierung."""
    # Darkmode robust (falls App "ui_dark_mode" nutzt)
    dark = bool(st.session_state.get("ui_dark_mode", st.session_state.get("dark_mode", False)))

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    soft_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)"
    header_bg = "rgba(255,255,255,0.08)" if dark else "rgba(127,127,127,0.10)"
    hover_bg = "rgba(255,255,255,0.07)" if dark else "rgba(0,0,0,0.035)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"

    # Secondary-Button (Zurück) – wie in Einführung
    btn2_bg = "rgba(255,255,255,0.06)" if dark else "#ffffff"
    btn2_text = "rgba(250,250,250,0.92)" if dark else "#111111"

    st.markdown(
        f"""
<style>
  .rgm-page {{
    max-width: 1200px;
    margin: 0 auto;
    padding-bottom: 6px;
  }}

  .rgm-h1 {{
    font-size: 30px;
    font-weight: 850;
    line-height: 1.15;
    margin: 0 0 6px 0;
    color: var(--rgm-text, #111);
  }}

  .rgm-lead {{
    font-size: 15px;
    line-height: 1.75;
    color: var(--rgm-text, #111);
    opacity: 0.92;
    margin: 0;
  }}

  .rgm-muted {{
    font-size: 15px;
    line-height: 1.75;
    color: var(--rgm-text, #111);
    opacity: 0.92;
  }}

  .rgm-hero {{
    background: var(--rgm-card-bg, #fff);
    border: 1px solid {border};
    border-radius: 14px;
    padding: 18px 18px 14px 18px;
    box-shadow: {shadow};
  }}

  .rgm-accent-line {{
    height: 3px;
    width: 96px;
    border-radius: 999px;
    margin: 10px 0 14px 0;
    background: linear-gradient(90deg, {TD_BLUE}, {OG_ORANGE});
  }}

  .rgm-card {{
    background: var(--rgm-card-bg, #fff);
    border: 1px solid {border};
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: {shadow};
    margin-top: 16px;
  }}

  .rgm-card-title {{
    font-weight: 850;
    font-size: 15px;
    margin: 0 0 10px 0;
    color: var(--rgm-text, #111);
  }}

  .rgm-subtle {{
    font-size: 13px;
    line-height: 1.6;
    color: var(--rgm-text, #111);
    opacity: 0.85;
    margin: 0;
  }}

  .rgm-divider {{
    height: 1px;
    background: {border};
    margin: 16px 0 8px 0;
  }}

  /* Expander als „Card“ */
  div[data-testid="stExpander"] {{
    border: 1px solid {border};
    border-radius: 14px;
    overflow: hidden;
    box-shadow: {shadow};
    background: var(--rgm-card-bg, #fff);
  }}

  div[data-testid="stExpander"] summary {{
    padding: 12px 14px !important;
    font-weight: 850 !important;
    color: var(--rgm-text, #111) !important;
    background: {header_bg} !important;
  }}

  div[data-testid="stExpander"] summary:hover {{
    background: {hover_bg} !important;
  }}

  div[data-testid="stExpander"] details {{
    border-radius: 14px;
  }}

  /* Expander Body Padding (Innenraum) */
  div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {{
    padding: 12px 14px 14px 14px;
  }}

  /* Kleine Pill für Gap */
  .rgm-pill {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid {border};
    background: {soft_bg};
    color: var(--rgm-text, #111);
    font-size: 13px;
    font-weight: 750;
    margin: 8px 0 8px 0;
    width: fit-content;
  }}

  /* Widgets: etwas ruhiger (ohne zu aggressiv in Streamlit einzugreifen) */
  div[data-testid="stTextInput"] input,
  div[data-testid="stSelectbox"] div {{
    border-radius: 10px !important;
  }}

  /* =========================================
     NAV-BUTTONS: Secondary wie in Einführung
     ========================================= */
  .stApp button[data-testid="baseButton-secondary"],
  .stApp div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]) {{
    background: {btn2_bg} !important;
    color: {btn2_text} !important;
    border: 1px solid {border} !important;
    border-radius: 10px !important;
    font-weight: 650 !important;
    opacity: 1 !important;
    transition: background 120ms ease, border-color 120ms ease, color 120ms ease;
  }}

  .stApp button[data-testid="baseButton-secondary"] *,
  .stApp div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]) * {{
    color: inherit !important;
  }}

  .stApp button[data-testid="baseButton-secondary"]:not(:disabled):hover,
  .stApp div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]):not(:disabled):hover {{
    background: {TU_ORANGE} !important;
    border-color: {TU_ORANGE} !important;
    color: #ffffff !important;
  }}

  .stApp button[data-testid="baseButton-secondary"]:not(:disabled):hover *,
  .stApp div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]):not(:disabled):hover * {{
    color: #ffffff !important;
  }}

  .stApp button[data-testid="baseButton-secondary"]:focus,
  .stApp div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]):focus {{
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(99,154,0,0.25) !important;
  }}

  @media (max-width: 900px) {{
    .rgm-h1 {{ font-size: 26px; }}
    .rgm-hero {{ padding: 16px; }}
    .rgm-card {{ padding: 12px 12px; }}
  }}
</style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    init_session_state()
    _inject_priorisierung_css()

    st.markdown('<div class="rgm-page">', unsafe_allow_html=True)

    # HERO
    st.markdown(
        """
<div class="rgm-hero">
  <div class="rgm-h1">Priorisierung &amp; Maßnahmenplanung</div>
  <div class="rgm-accent-line"></div>
  <p class="rgm-lead">
    Legen Sie für jede Dimension fest, wie wichtig sie ist und welche konkreten Maßnahmen Sie angehen möchten.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

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
        st.markdown(
            """
<div class="rgm-card">
  <div class="rgm-card-title">Hinweis</div>
  <p class="rgm-subtle">Noch keine Ergebnisse vorhanden – bitte zuerst die Erhebung durchführen.</p>
</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = df.copy()
    df["name_short"] = df["name"].apply(after_dash)

    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        cat = st.selectbox("Kategorie", options=["Alle", "TD", "OG"], index=0)
    with c2:
        show_all = st.checkbox("Alle Dimensionen anzeigen (auch Gap ≤ 0)", value=False)

    df_view = df.copy()
    if cat != "Alle":
        df_view = df_view[df_view["category"] == cat]
    if not show_all:
        df_view = df_view[df_view["gap"] > 0]

    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)

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
            prev_resp = prev.get("responsible", "")

            try:
                default_index = PRIORITY_OPTIONS.index(prev_prio)
            except ValueError:
                default_index = 0

            label = f"{code} – {name_short} · Gap {gap:.2f}"
            with st.expander(label, expanded=(gap >= 1.0)):
                st.markdown(f"<div class='rgm-pill'>Gap (Soll–Ist): <b>{gap:.2f}</b> Reifegradstufen</div>", unsafe_allow_html=True)

                # Zeile 1: Priorität + Maßnahme
                r1c1, r1c2 = st.columns([1, 5], gap="large")
                with r1c1:
                    st.selectbox(
                        "Priorität",
                        options=PRIORITY_OPTIONS,
                        index=default_index,
                        key=f"prio_{code}",
                    )
                with r1c2:
                    st.text_input(
                        "Maßnahme",
                        value=prev_action,
                        key=f"action_{code}",
                        placeholder="z. B. Redaktionsleitfaden erstellen",
                    )

                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

                # Zeile 2: Verantwortlich + Zeitraum
                r2c1, r2c2 = st.columns([3, 2], gap="large")
                with r2c1:
                    st.text_input(
                        "Verantwortlich",
                        value=prev_resp,
                        key=f"resp_{code}",
                        placeholder="z. B. Christian Koch",
                    )
                with r2c2:
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
    # Übernehmen + Hinweis
    # -----------------------------
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

    if dirty:
        st.warning(
            "Sie haben Priorisierungen geändert, die noch nicht übernommen wurden. "
            "Bitte zuerst „Priorisierungen übernehmen“ klicken, damit diese Werte verwendet werden."
        )

    st.markdown("---")

    # Navigation (einheitlich)
    left, right = st.columns([1, 1], gap="large")
    with left:
        if st.button("Zurück", use_container_width=True):
            st.session_state["nav_request"] = "Dashboard"
            st.rerun()

    with right:
        if st.button(
            "Weiter zur Gesamtübersicht",
            type="primary",
            use_container_width=True,
            disabled=dirty,
        ):
            st.session_state["nav_request"] = "Gesamtübersicht"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
