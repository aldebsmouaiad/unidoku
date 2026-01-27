# app.py
import importlib.util
from pathlib import Path

import streamlit as st
import base64
import html
from core.state import init_session_state
from core import persist

TU_GREEN = "#639A00"
TU_ORANGE = "#CA7406"

st.set_page_config(
    page_title="Reifegradmodell Technische Dokumentation",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"

@st.cache_data(show_spinner=False)
def _img_b64(path: Path) -> str | None:
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def apply_global_theme_css(dark: bool) -> None:
    bg = "#0e1117" if dark else "#ffffff"
    text = "rgba(250,250,250,0.92)" if dark else "#111111"
    sidebar_bg = "#0b0f16" if dark else "#f6f7f9"
    card_bg = "#111827" if dark else "#ffffff"
    border = "rgba(255,255,255,0.10)" if dark else "rgba(0,0,0,0.10)"

    # Secondary-Button Grundzustand passend zu Light/Dark
    btn2_bg = "rgba(255,255,255,0.06)" if dark else "#ffffff"
    btn2_text = "rgba(250,250,250,0.92)" if dark else "#111111"

    # Dropdown/Popover (Selectbox-Menü)
    pop_hover = "rgba(202,116,6,0.22)" if dark else "rgba(202,116,6,0.14)"  # TU_ORANGE leicht
    pop_sel = "rgba(255,255,255,0.08)" if dark else "rgba(0,0,0,0.04)"

    # Fortschritt-Pipeline: inaktiv sichtbar machen
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

    /* Logo-Karte in Sidebar (IPS) */
    --rgm-logo-bg: {("rgba(255,255,255,0.95)" if dark else "#ffffff")};
    --rgm-logo-border: {("rgba(255,255,255,0.14)" if dark else "rgba(0,0,0,0.10)")};
    --rgm-logo-shadow: {("0 6px 18px rgba(0,0,0,0.35)" if dark else "0 6px 18px rgba(0,0,0,0.20)")};

    /* TU Farben */
    --tu-green: {TU_GREEN};
    --tu-orange: {TU_ORANGE};

    /* Pipeline */
    --rgm-pipe-inactive: {pipe_inactive};
  }}

  /* =========================================================
     APP BACKGROUND / LAYOUT
     ========================================================= */
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

  /* Sidebar */
  section[data-testid="stSidebar"] {{
    background: var(--rgm-sidebar-bg) !important;
    border-right: 1px solid var(--rgm-border) !important;
  }}
  section[data-testid="stSidebar"] > div {{
    background: var(--rgm-sidebar-bg) !important;
  }}

  /* Default text */
  html, body,
  .stMarkdown, .stText, p, li, span, label,
  div[data-testid="stCaptionContainer"],
  div[data-testid="stMarkdownContainer"] {{
    color: var(--rgm-text) !important;
  }}

  hr {{
    border-color: var(--rgm-border) !important;
  }}

  /* Links */
  a {{
    color: var(--tu-green) !important;
  }}

  /* =========================================================
     INPUTS
     ========================================================= */
  div[data-baseweb="input"] input,
  div[data-baseweb="textarea"] textarea,
  div[data-baseweb="select"] > div {{
    background-color: var(--rgm-card-bg) !important;
    color: var(--rgm-text) !important;
    border-color: var(--rgm-border) !important;
  }}

  /* Selectbox Pfeil/Icons sichtbar halten */
  div[data-baseweb="select"] svg {{
    color: var(--rgm-text) !important;
  }}

  /* Radio-Labels (inkl. Sidebar) */
  div[role="radiogroup"] label,
  div[data-testid="stSidebar"] label {{
    color: var(--rgm-text) !important;
  }}

  /* =========================================================
   SELECTBOX DROPDOWN (BaseWeb Popover/Menu)
   Fix: Optionen im Darkmode lesbar + Menü im App-Style
   ========================================================= */
  div[data-baseweb="popover"] div[data-baseweb="menu"],
  div[data-baseweb="popover"] ul {{
    background: var(--rgm-card-bg) !important;
    border: 1px solid var(--rgm-border) !important;
    box-shadow: 0 12px 28px rgba(0,0,0,0.35) !important;
  }}

  /* Option-Text */
  div[data-baseweb="popover"] div[role="option"],
  div[data-baseweb="popover"] div[role="option"] * ,
  div[data-baseweb="popover"] li,
  div[data-baseweb="popover"] li * {{
    color: var(--rgm-text) !important;
  }}

  /* Hover im Dropdown */
  div[data-baseweb="popover"] div[role="option"]:hover,
  div[data-baseweb="popover"] li:hover {{
    background: rgba(202,116,6,0.18) !important;
  }}

  /* Selected Option */
  div[data-baseweb="popover"] div[role="option"][aria-selected="true"],
  div[data-baseweb="popover"] li[aria-selected="true"] {{
    background: rgba(99,154,0,0.18) !important;
  }}

  /* =========================================================
     BASEWEB POPOVER / SELECT DROPDOWN (Darkmode-Lesbarkeit!)
     ========================================================= */
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

  /* =========================================================
     SIDEBAR LOGO (IPS)
     ========================================================= */
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
  @media (max-width: 1200px) {{
    .rgm-sidebar-logo img {{ height: 58px; }}
  }}
  @media (max-width: 900px) {{
    .rgm-sidebar-logo img {{ height: 52px; }}
  }}

  /* =========================================================
     BUTTONS
     - Primary: Grün
     - Hover (alle Buttons): Orange
     - Secondary: neutral (light/dark), Hover: Orange
     ========================================================= */

  /* Primary */
  .stApp button[kind="primary"],
  .stApp button[data-testid="baseButton-primary"] {{
    background: var(--tu-green) !important;
    border: 1px solid var(--tu-green) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    font-weight: 650 !important;
    opacity: 1 !important;
  }}

  /* Secondary */
  .stApp button[kind="secondary"],
  .stApp button[data-testid="baseButton-secondary"] {{
    background: {btn2_bg} !important;
    border: 1px solid var(--rgm-border) !important;
    color: {btn2_text} !important;
    border-radius: 10px !important;
    font-weight: 650 !important;
    opacity: 1 !important;
  }}

  /* Innerer Text/Icons erbt Buttonfarbe */
  .stApp div.stButton > button *,
  .stApp button[data-testid^="baseButton-"] * {{
    color: inherit !important;
  }}

  /* Hover für ALLE Buttons -> Orange + Weiß
   (inkl. DownloadButton + FileUploader Browse Button) */
  .stApp div.stButton > button:not(:disabled):hover,
  .stApp button[data-testid^="baseButton-"]:not(:disabled):hover,
  .stApp div[data-testid="stFormSubmitButton"] button:not(:disabled):hover,

  /* NEU: DownloadButton (st.download_button) */
  .stApp div[data-testid="stDownloadButton"] button:not(:disabled):hover,

  /* NEU: FileUploader Browse files Button */
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

  /* NEU: innerer Text/Icon auch weiß */
  .stApp div[data-testid="stDownloadButton"] button:not(:disabled):hover *,
  .stApp div[data-testid="stFileUploader"] [data-baseweb="button"] button:not(:disabled):hover * {{
    color: #ffffff !important;
    fill: currentColor !important;
    stroke: currentColor !important;
  }}

  /* ---- PATCH: Form-Submit-Buttons (Step 0 + alle Erhebung-Steps) sicher treffen ---- */
  div[data-testid="stAppViewContainer"] div.stFormSubmitButton > button[kind="primary"],
  div[data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] > button[kind="primary"] {{
    background: var(--tu-green) !important;
    border-color: var(--tu-green) !important;
    color: #ffffff !important;
  }}
  div[data-testid="stAppViewContainer"] div.stFormSubmitButton > button[kind="secondary"],
  div[data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] > button[kind="secondary"] {{
    background: {btn2_bg} !important;
    border: 1px solid var(--rgm-border) !important;
    color: {btn2_text} !important;
  }}
  div[data-testid="stAppViewContainer"] div.stFormSubmitButton > button:not(:disabled):hover,
  div[data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] > button:not(:disabled):hover {{
    background: var(--tu-orange) !important;
    border-color: var(--tu-orange) !important;
    color: #ffffff !important;
  }}
  div[data-testid="stAppViewContainer"] div.stFormSubmitButton > button:not(:disabled):hover *,
  div[data-testid="stAppViewContainer"] div[data-testid="stFormSubmitButton"] > button:not(:disabled):hover * {{
    color: #ffffff !important;
  }}

  /* Disabled */
  .stApp div.stButton > button:disabled,
  .stApp button[data-testid^="baseButton-"]:disabled {{
    opacity: 0.55 !important;
    cursor: not-allowed !important;
  }}

  /* Focus ring */
  .stApp div.stButton > button:focus,
  .stApp button[data-testid^="baseButton-"]:focus {{
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(99,154,0,0.25) !important;
  }}

  /* Smooth transitions */
  .stApp div.stButton > button,
  .stApp button[data-testid^="baseButton-"] {{
    transition: background 120ms ease, border-color 120ms ease, color 120ms ease;
  }}

  /* =========================================================
     SIDEBAR NAVIGATION (st.radio): Hover -> Orange
     ========================================================= */
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

  /* =========================================================
     PATCH: Fortschritt-Pipeline in Darkmode sichtbar
     (deine Pipeline nutzt i.d.R. .rgm-seg; wir setzen inaktive Segmente fest)
     ========================================================= */
  div[data-testid="stAppViewContainer"] .rgm-seg {{
    background: var(--rgm-pipe-inactive) !important;
  }}
  div[data-testid="stAppViewContainer"] .rgm-seg.active,
  div[data-testid="stAppViewContainer"] .rgm-seg.filled,
  div[data-testid="stAppViewContainer"] .rgm-seg--active,
  div[data-testid="stAppViewContainer"] .rgm-seg--filled {{
    background: var(--tu-green) !important;
  }}

  /* =========================================================
   EXPANDER (st.expander) – UNVERÄNDERT wie bei dir (war korrekt)
   ========================================================= */
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

  div[data-testid="stExpander"] summary * ,
  details[data-testid="stExpander"] summary * ,
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
    ret_q    = persist.qp_get("ret_q")

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
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False

    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "Start"

    if "nav_page_ui" not in st.session_state:
        st.session_state["nav_page_ui"] = st.session_state["nav_page"]

    if "nav_request" not in st.session_state:
        st.session_state["nav_request"] = None

    if "nav_history" not in st.session_state:
        st.session_state["nav_history"] = []

    # ---- Sidebar: IPS Logo + Darkmode Toggle ----
    IPS_URL = "https://ips.mb.tu-dortmund.de/"  # ggf. anpassen

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

    if hasattr(st, "toggle"):
        st.sidebar.toggle("Darkmodus", key="dark_mode")
    else:
        st.sidebar.checkbox("Darkmodus", key="dark_mode")

    st.sidebar.markdown("---")

    # CSS anwenden
    apply_global_theme_css(bool(st.session_state["dark_mode"]))

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
