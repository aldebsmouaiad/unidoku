# app.py
import importlib.util
from pathlib import Path

import streamlit as st

from core.state import init_session_state
from core import persist

st.set_page_config(
    page_title="Reifegradmodell Technische Dokumentation",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent


def apply_global_theme_css(dark: bool) -> None:
    bg = "#0e1117" if dark else "#ffffff"
    text = "rgba(250,250,250,0.92)" if dark else "#111111"
    sidebar_bg = "#0b0f16" if dark else "#f6f7f9"
    card_bg = "#111827" if dark else "#ffffff"
    border = "rgba(255,255,255,0.10)" if dark else "rgba(0,0,0,0.10)"

    st.markdown(
        f"""
        <style>
          :root {{
            --rgm-bg: {bg};
            --rgm-text: {text};
            --rgm-sidebar-bg: {sidebar_bg};
            --rgm-card-bg: {card_bg};
            --rgm-border: {border};
            --rgm-footer-bg: {("#0e1117" if dark else "#ffffff")};
            --rgm-logo-bg: {("rgba(255,255,255,0.95)" if dark else "transparent")};
            --rgm-logo-border: {("rgba(0,0,0,0.10)" if dark else "transparent")};
          }}

          div[data-testid="stAppViewContainer"] {{
            background: var(--rgm-bg) !important;
            color: var(--rgm-text) !important;
          }}

          header[data-testid="stHeader"] {{
            background: transparent !important;
          }}

          section[data-testid="stMain"] {{
            background: var(--rgm-bg) !important;
          }}

          section[data-testid="stSidebar"] {{
            background: var(--rgm-sidebar-bg) !important;
            border-right: 1px solid var(--rgm-border) !important;
          }}
          section[data-testid="stSidebar"] > div {{
            background: var(--rgm-sidebar-bg) !important;
          }}

          html, body,
          .stMarkdown, .stText, p, li, span, label {{
            color: var(--rgm-text) !important;
          }}

          div[data-baseweb="input"] input,
          div[data-baseweb="textarea"] textarea,
          div[data-baseweb="select"] > div {{
            background-color: var(--rgm-card-bg) !important;
            color: var(--rgm-text) !important;
            border-color: var(--rgm-border) !important;
          }}

          div[role="radiogroup"] label,
          div[data-testid="stSidebar"] label {{
            color: var(--rgm-text) !important;
          }}

          hr {{
            border-color: var(--rgm-border) !important;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_page_module(filename: str, module_name: str):
    file_path = BASE_DIR / "pages" / filename
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# Page-Module laden
page_start = load_page_module("00_Start.py", "page_start")
page_einfuehrung = load_page_module("00_Einfuehrung.py", "page_einfuehrung")
page_ausfuellhinweise = load_page_module("00_Ausfuellhinweise.py", "page_ausfuellhinweise")
page_erhebung = load_page_module("01_Erhebung.py", "page_erhebung")
page_dashboard = load_page_module("02_Dashboard.py", "page_dashboard")
page_priorisierung = load_page_module("03_Priorisierung.py", "page_priorisierung")
page_glossar = load_page_module("04_Glossar.py", "page_glossar")
page_gesamt = load_page_module("05_Gesamtuebersicht.py", "page_gesamt")

PAGES = {
    "Start": page_start.main,
    "Einführung": page_einfuehrung.main,
    "Ausfüllhinweise": page_ausfuellhinweise.main,
    "Erhebung": page_erhebung.main,
    "Dashboard": page_dashboard.main,
    "Priorisierung": page_priorisierung.main,
    "Gesamtübersicht": page_gesamt.main,
    "Glossar": page_glossar.main,
}


def _apply_query_navigation(aid: str) -> None:
    """
    Liest Query-Params (über persist.qp_get) und setzt Session-Navigation.
    Danach: entfernt NUR unsere Params, lässt 'aid' stehen.
    """
    page = persist.qp_get("page")
    term = persist.qp_get("term")
    from_page = persist.qp_get("from")

    # Backward compatibility: ?g=... oder ?glossary=...
    g = persist.qp_get("g") or persist.qp_get("glossary")
    if g and not term:
        term = g

    # wenn g/term da ist, aber page fehlt: -> Glossar
    if term and not page:
        page = "Glossar"

    ret_step = persist.qp_get("ret_step")
    ret_idx = persist.qp_get("ret_idx")
    ret_code = persist.qp_get("ret_code")

    did_apply = False

    if page and page in PAGES:
        st.session_state["nav_request"] = page
        did_apply = True

    if from_page:
        st.session_state["nav_return_page"] = from_page
        did_apply = True

    if term:
        st.session_state["glossary_focus_term"] = term
        did_apply = True

    if ret_step or ret_idx or ret_code:
        payload = dict(st.session_state.get("nav_return_payload", {}) or {})
        if ret_step and ret_step.isdigit():
            payload["erhebung_step"] = int(ret_step)
        if ret_idx and ret_idx.isdigit():
            payload["erhebung_dim_idx"] = int(ret_idx)
        if ret_code:
            payload["dim_code"] = ret_code
        st.session_state["nav_return_payload"] = payload
        did_apply = True

    if did_apply:
        persist.clear_query_params_keep_aid(aid)


def main():
    init_session_state()

    # AID: immer zuerst (und stabil in URL)
    aid = persist.get_or_create_aid()

    # Restore kann hier global laufen (pages dürfen zusätzlich restore machen; restore überschreibt nicht “live”)
    persist.restore(aid)

    # Query-Nav anwenden (und danach unsere Params säubern, AID bleibt)
    _apply_query_navigation(aid)

    # ---- Defaults ----
    if "ui_dark_mode" not in st.session_state:
        st.session_state["ui_dark_mode"] = False

    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "Start"

    if "nav_page_ui" not in st.session_state:
        st.session_state["nav_page_ui"] = st.session_state["nav_page"]

    if "nav_request" not in st.session_state:
        st.session_state["nav_request"] = None

    if "nav_history" not in st.session_state:
        st.session_state["nav_history"] = []

    # ---- Sidebar: Darkmode Toggle ----
    if hasattr(st, "toggle"):
        st.sidebar.toggle("Darkmodus", key="ui_dark_mode")
    else:
        st.sidebar.checkbox("Darkmodus", key="ui_dark_mode")

    st.sidebar.markdown("---")

    # CSS anwenden
    apply_global_theme_css(bool(st.session_state["ui_dark_mode"]))

    # ---- Programmatic Navigation (Weiter/Zurück) VOR dem Radio ----
    nav_req = st.session_state.get("nav_request")
    if nav_req:
        target = str(nav_req)
        if target in PAGES and target != st.session_state["nav_page"]:
            st.session_state["nav_history"].append(st.session_state["nav_page"])
            st.session_state["nav_page"] = target
            st.session_state["nav_page_ui"] = target
        st.session_state["nav_request"] = None

    # ---- Navigation ----
    st.sidebar.title("Navigation")
    selected = st.sidebar.radio(
        "Seite wählen",
        list(PAGES.keys()),
        key="nav_page_ui",
    )

    if selected != st.session_state["nav_page"]:
        st.session_state["nav_history"].append(st.session_state["nav_page"])
        st.session_state["nav_page"] = selected

    # ---- Seite rendern ----
    PAGES[st.session_state["nav_page"]]()  # type: ignore

    # Snapshot am Ende
    persist.save(aid)


if __name__ == "__main__":
    main()
