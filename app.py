# app.py
from __future__ import annotations

import base64
import html
import importlib.util
from pathlib import Path
from typing import Optional

import streamlit as st

from core.state import init_session_state
from core import persist

import os
import tempfile

TU_GREEN = "#639A00"
TU_ORANGE = "#CA7406"

st.set_page_config(
    page_title="Reifegradmodell Technische Dokumentation",
    layout="wide",
)

@st.cache_resource(show_spinner=False)
def _ensure_plotly_chrome() -> str:
    import plotly.io as pio

    chrome_dir = Path(tempfile.gettempdir()) / "plotly-chrome"
    chrome_dir.mkdir(parents=True, exist_ok=True)

    # benötigt plotly >= 6.3.0
    chrome_exe = pio.get_chrome(path=chrome_dir)
    os.environ["BROWSER_PATH"] = str(chrome_exe)
    return str(chrome_exe)


BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"

# Interner Widget-Key (Pages sollen KEIN Widget mit diesem Key erzeugen)
_DARK_TOGGLE_KEY = "_rgm_dark_toggle"


@st.cache_data(show_spinner=False)
def _img_b64(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _clear_query_params_keep_aid(aid: str) -> None:
    """
    Robust: erst persist-Helfer, dann Streamlit-Fallback.
    """
    try:
        persist.clear_query_params_keep_aid(aid)
        return
    except Exception:
        pass

    # Fallbacks (je nach Streamlit-Version)
    try:
        st.query_params.clear()
        st.query_params["aid"] = aid
        return
    except Exception:
        pass

    try:
        st.experimental_set_query_params(aid=aid)
    except Exception:
        pass


def _theme_from_toggle() -> bool:
    return bool(st.session_state.get(_DARK_TOGGLE_KEY, False))


def _sync_theme_aliases_from_toggle() -> None:
    """
    Canonical für die UI ist _DARK_TOGGLE_KEY (Widget-State).
    Aliases für alte Pages:
      - ui_dark_mode
      - dark_mode
      - dark_mode_ui (falls irgendwo noch genutzt)
    """
    d = _theme_from_toggle()
    st.session_state["ui_dark_mode"] = d
    st.session_state["dark_mode"] = d
    st.session_state["dark_mode_ui"] = d


def _init_theme_state_from_snapshot() -> None:
    """
    Setzt den Toggle-State NUR initial (damit Klicks nicht überschrieben werden).
    Quelle: ui_dark_mode / dark_mode aus Snapshot (persist.restore).
    """
    if _DARK_TOGGLE_KEY not in st.session_state:
        d = bool(st.session_state.get("ui_dark_mode", st.session_state.get("dark_mode", False)))
        st.session_state[_DARK_TOGGLE_KEY] = d
    _sync_theme_aliases_from_toggle()


def apply_global_theme_css(dark: bool) -> None:
    bg = "#0e1117" if dark else "#ffffff"
    text = "rgba(250,250,250,0.92)" if dark else "#111111"
    sidebar_bg = "#0b0f16" if dark else "#f6f7f9"
    card_bg = "#111827" if dark else "#ffffff"
    border = "rgba(255,255,255,0.10)" if dark else "rgba(0,0,0,0.10)"

    btn2_bg = "rgba(255,255,255,0.06)" if dark else "#ffffff"
    btn2_text = "rgba(250,250,250,0.92)" if dark else "#111111"

    pop_hover = "rgba(202,116,6,0.22)" if dark else "rgba(202,116,6,0.14)"
    pop_sel = "rgba(255,255,255,0.08)" if dark else "rgba(0,0,0,0.04)"

    pipe_inactive = "rgba(255,255,255,0.14)" if dark else "rgba(0,0,0,0.10)"

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

    --rgm-logo-bg: {("rgba(255,255,255,0.95)" if dark else "#ffffff")};
    --rgm-logo-border: {("rgba(255,255,255,0.14)" if dark else "rgba(0,0,0,0.10)")};
    --rgm-logo-shadow: {("0 6px 18px rgba(0,0,0,0.35)" if dark else "0 6px 18px rgba(0,0,0,0.20)")};

    --tu-green: {TU_GREEN};
    --tu-orange: {TU_ORANGE};

    --rgm-pipe-inactive: {pipe_inactive};
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
  .stMarkdown, .stText, p, li, span, label,
  div[data-testid="stCaptionContainer"],
  div[data-testid="stMarkdownContainer"] {{
    color: var(--rgm-text) !important;
  }}

  hr {{
    border-color: var(--rgm-border) !important;
  }}

  a {{
    color: var(--tu-green) !important;
  }}

  div[data-baseweb="input"] input,
  div[data-baseweb="textarea"] textarea,
  div[data-baseweb="select"] > div {{
    background-color: var(--rgm-card-bg) !important;
    color: var(--rgm-text) !important;
    border-color: var(--rgm-border) !important;
  }}

  div[data-baseweb="select"] svg {{
    color: var(--rgm-text) !important;
  }}

  div[role="radiogroup"] label,
  div[data-testid="stSidebar"] label {{
    color: var(--rgm-text) !important;
  }}

  div[data-baseweb="popover"] div[data-baseweb="menu"],
  div[data-baseweb="popover"] ul {{
    background: var(--rgm-card-bg) !important;
    border: 1px solid var(--rgm-border) !important;
    box-shadow: 0 12px 28px rgba(0,0,0,0.35) !important;
  }}

  div[data-baseweb="popover"] div[role="option"],
  div[data-baseweb="popover"] div[role="option"] *,
  div[data-baseweb="popover"] li,
  div[data-baseweb="popover"] li * {{
    color: var(--rgm-text) !important;
  }}

  div[data-baseweb="popover"] div[role="option"]:hover,
  div[data-baseweb="popover"] li:hover {{
    background: rgba(202,116,6,0.18) !important;
  }}

  div[data-baseweb="popover"] div[role="option"][aria-selected="true"],
  div[data-baseweb="popover"] li[aria-selected="true"] {{
    background: rgba(99,154,0,0.18) !important;
  }}

  div[data-baseweb="popover"] > div {{
    background: var(--rgm-card-bg) !important;
    color: var(--rgm-text) !important;
    border: 1px solid var(--rgm-border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
  }}

  div[data-baseweb="popover"] ul[role="listbox"],
  div[data-baseweb="popover"] div[role="listbox"],
  div[data-baseweb="menu"] {{
    background: var(--rgm-card-bg) !important;
    color: var(--rgm-text) !important;
  }}

  div[data-baseweb="popover"] li[role="option"],
  div[data-baseweb="menu"] li {{
    background: transparent !important;
    color: var(--rgm-text) !important;
  }}

  div[data-baseweb="popover"] li[role="option"]:hover,
  div[data-baseweb="menu"] li:hover {{
    background: {pop_hover} !important;
  }}

  div[data-baseweb="popover"] li[aria-selected="true"],
  div[data-baseweb="menu"] li[aria-selected="true"] {{
    background: {pop_sel} !important;
  }}

  .rgm-sidebar-logo {{
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;

    background: var(--rgm-logo-bg);
    border: 1px solid var(--rgm-logo-border);
    border-radius: 14px;
    padding: 10px 14px;
    box-shadow: var(--rgm-logo-shadow);

    text-decoration: none;
    color: inherit;
    margin: 4px 0 14px 0;
  }}
  .rgm-sidebar-logo:hover {{
    opacity: 0.94;
  }}
  .rgm-sidebar-logo img {{
    height: 64px;
    width: auto;
    max-width: 100%;
    object-fit: contain;
    display: block;
  }}

  .stApp button[kind="primary"],
  .stApp button[data-testid="baseButton-primary"] {{
    background: var(--tu-green) !important;
    border: 1px solid var(--tu-green) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    font-weight: 650 !important;
    opacity: 1 !important;
  }}

  .stApp button[kind="secondary"],
  .stApp button[data-testid="baseButton-secondary"] {{
    background: {btn2_bg} !important;
    border: 1px solid var(--rgm-border) !important;
    color: {btn2_text} !important;
    border-radius: 10px !important;
    font-weight: 650 !important;
    opacity: 1 !important;
  }}

  .stApp div.stButton > button *,
  .stApp button[data-testid^="baseButton-"] * {{
    color: inherit !important;
  }}

  .stApp div.stButton > button:not(:disabled):hover,
  .stApp button[data-testid^="baseButton-"]:not(:disabled):hover,
  .stApp div[data-testid="stFormSubmitButton"] button:not(:disabled):hover,
  .stApp div[data-testid="stDownloadButton"] button:not(:disabled):hover,
  .stApp div[data-testid="stFileUploader"] [data-baseweb="button"] button:not(:disabled):hover {{
    background: var(--tu-orange) !important;
    background-color: var(--tu-orange) !important;
    background-image: none !important;
    border-color: var(--tu-orange) !important;
    color: #ffffff !important;
    opacity: 1 !important;
  }}

  .stApp div.stButton > button:not(:disabled):hover *,
  .stApp button[data-testid^="baseButton-"]:not(:disabled):hover *,
  .stApp div[data-testid="stFormSubmitButton"] button:not(:disabled):hover *,
  .stApp div[data-testid="stDownloadButton"] button:not(:disabled):hover *,
  .stApp div[data-testid="stFileUploader"] [data-baseweb="button"] button:not(:disabled):hover * {{
    color: #ffffff !important;
    fill: currentColor !important;
    stroke: currentColor !important;
  }}

  .stApp div.stButton > button:disabled,
  .stApp button[data-testid^="baseButton-"]:disabled {{
    opacity: 0.55 !important;
    cursor: not-allowed !important;
  }}

  .stApp div.stButton > button:focus,
  .stApp button[data-testid^="baseButton-"]:focus {{
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(99,154,0,0.25) !important;
  }}

  .stApp div.stButton > button,
  .stApp button[data-testid^="baseButton-"] {{
    transition: background 120ms ease, border-color 120ms ease, color 120ms ease;
  }}

  section[data-testid="stSidebar"] div[role="radiogroup"] label {{
    padding: 6px 10px;
    border-radius: 10px;
    transition: background 120ms ease, color 120ms ease;
  }}
  section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
    background: rgba(202,116,6,0.14);
  }}
  section[data-testid="stSidebar"] div[role="radiogroup"] label:hover span {{
    color: var(--tu-orange) !important;
  }}
  section[data-testid="stSidebar"] div[role="radiogroup"] label:hover svg {{
    color: var(--tu-orange) !important;
  }}

  div[data-testid="stAppViewContainer"] .rgm-seg {{
    background: var(--rgm-pipe-inactive) !important;
  }}
  div[data-testid="stAppViewContainer"] .rgm-seg.active,
  div[data-testid="stAppViewContainer"] .rgm-seg.filled,
  div[data-testid="stAppViewContainer"] .rgm-seg--active,
  div[data-testid="stAppViewContainer"] .rgm-seg--filled {{
    background: var(--tu-green) !important;
  }}

  div[data-testid="stExpander"],
  details[data-testid="stExpander"],
  .stExpander {{
    border: 1px solid var(--rgm-border) !important;
    border-radius: 14px !important;
    background: transparent !important;
    overflow: hidden !important;
  }}

  div[data-testid="stExpander"] summary,
  details[data-testid="stExpander"] summary,
  .stExpander summary {{
    background: var(--rgm-card-bg) !important;
    color: var(--rgm-text) !important;
    padding: 10px 14px !important;
    border-radius: 14px !important;
  }}

  div[data-testid="stExpander"] summary *,
  details[data-testid="stExpander"] summary *,
  .stExpander summary * {{
    color: var(--rgm-text) !important;
  }}

  div[data-testid="stExpander"] summary svg,
  details[data-testid="stExpander"] summary svg,
  .stExpander summary svg {{
    color: var(--rgm-text) !important;
    fill: currentColor !important;
  }}

  div[data-testid="stExpander"] summary:hover,
  details[data-testid="stExpander"] summary:hover,
  .stExpander summary:hover {{
    box-shadow: 0 0 0 2px rgba(202,116,6,0.28) !important;
  }}

  div[data-testid="stExpander"] .streamlit-expanderContent,
  details[data-testid="stExpander"] .streamlit-expanderContent,
  .stExpander .streamlit-expanderContent,
  div[data-testid="stExpander"] > div,
  details[data-testid="stExpander"] > div {{
    background: var(--rgm-card-bg) !important;
    color: var(--rgm-text) !important;
    padding: 12px 14px 14px 14px !important;
  }}

  div[data-testid="stExpander"] div[role="region"],
  details[data-testid="stExpander"] div[role="region"],
  .stExpander div[role="region"] {{
    background: transparent !important;
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
    page = persist.qp_get("page")
    term = persist.qp_get("term")
    from_page = persist.qp_get("from")

    g = persist.qp_get("g") or persist.qp_get("glossary")
    if g and not term:
        term = g

    if term and not page:
        page = "Glossar"

    ret_step = persist.qp_get("ret_step")
    ret_idx = persist.qp_get("ret_idx")
    ret_code = persist.qp_get("ret_code")
    ret_q = persist.qp_get("ret_q")

    did_apply = False

    # ui_dark=0|1: darf NUR initial wirken (sonst überschreibt URL jeden Toggle-Klick)
    ui_dark = (persist.qp_get("ui_dark") or "").strip()
    if ui_dark in ("0", "1") and not st.session_state.get("_rgm_ui_dark_applied", False):
        d = (ui_dark == "1")
        st.session_state[_DARK_TOGGLE_KEY] = d
        _sync_theme_aliases_from_toggle()
        st.session_state["_rgm_ui_dark_applied"] = True
        did_apply = True

    if page and page in PAGES:
        st.session_state["nav_request"] = page
        did_apply = True

    if from_page:
        st.session_state["nav_return_page"] = from_page
        did_apply = True

    if term:
        st.session_state["glossary_focus_term"] = term
        did_apply = True

    if ret_step or ret_idx or ret_code or ret_q:
        payload = dict(st.session_state.get("nav_return_payload", {}) or {})
        if ret_step and ret_step.isdigit():
            payload["erhebung_step"] = int(ret_step)
        if ret_idx and ret_idx.isdigit():
            payload["erhebung_dim_idx"] = int(ret_idx)
        if ret_code:
            payload["dim_code"] = ret_code
        if ret_q:
            payload["erhebung_qid"] = ret_q
        st.session_state["nav_return_payload"] = payload
        did_apply = True

    if did_apply:
        _clear_query_params_keep_aid(aid)


def main() -> None:
    init_session_state()

    aid = persist.get_or_create_aid()

    # Restore nur einmal pro Session/AID (sonst überschreibt es Widget-Klicks)
    if st.session_state.get("_rgm_restored_aid") != aid:
        persist.restore(aid)
        st.session_state["_rgm_restored_aid"] = aid

    # Theme-State initialisieren (NUR wenn Toggle-Key fehlt)
    _init_theme_state_from_snapshot()

    # Navigation Defaults
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "Start"
    if "nav_page_ui" not in st.session_state:
        st.session_state["nav_page_ui"] = st.session_state["nav_page"]
    if "nav_request" not in st.session_state:
        st.session_state["nav_request"] = None
    if "nav_history" not in st.session_state:
        st.session_state["nav_history"] = []

    # Query-Nav anwenden (und danach Params säubern)
    _apply_query_navigation(aid)

    # Wichtig: Nach Query-Nav nochmal Aliases aus Toggle synchronisieren
    # (damit Pages, die dark_mode/ui_dark_mode lesen, konsistent sind)
    _sync_theme_aliases_from_toggle()

    # ---- Sidebar: IPS Logo + Darkmode Toggle ----
    IPS_URL = "https://ips.mb.tu-dortmund.de/"
    ips_path = IMAGES_DIR / "IPS-Logo-RGB.png"
    ips_b64 = _img_b64(ips_path)

    if ips_b64:
        st.sidebar.markdown(
            f"""
            <a class="rgm-sidebar-logo" href="{html.escape(IPS_URL)}" target="_blank" rel="noopener noreferrer">
              <img src="data:image/png;base64,{ips_b64}" alt="IPS Institut für Produktionssysteme"/>
            </a>
            """,
            unsafe_allow_html=True,
        )




    # Chrome nur einmal vorbereiten (cached)
    try:
        _ensure_plotly_chrome()
    except Exception as e:
        st.warning(f"Chrome für Plotly-Export konnte nicht vorbereitet werden: {e}")
    
    
    def _on_dark_toggle() -> None:
        # Toggle ist ab jetzt Chef (Query-Param darf nicht mehr überschreiben)
        st.session_state["_rgm_ui_dark_applied"] = True
        _sync_theme_aliases_from_toggle()
        _clear_query_params_keep_aid(aid)

    if hasattr(st, "toggle"):
        st.sidebar.toggle("Darkmodus", key=_DARK_TOGGLE_KEY, on_change=_on_dark_toggle)
    else:
        st.sidebar.checkbox("Darkmodus", key=_DARK_TOGGLE_KEY, on_change=_on_dark_toggle)

    st.sidebar.markdown("---")

    # CSS aus DIREKTEM Toggle-State (damit es IMMER sofort klappt)
    apply_global_theme_css(_theme_from_toggle())

    # ---- Programmatic Navigation VOR dem Radio ----
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
