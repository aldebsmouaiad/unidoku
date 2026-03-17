from __future__ import annotations

import copy
import json
import urllib.error
import urllib.request
from pathlib import Path

import streamlit as st

from core.model_loader import load_model_config
from core.overview import build_overview_table
from core.state import init_session_state

TU_ORANGE = "#CA7406"
TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"

PRIORITY_OPTIONS = ["", "A (hoch)", "B (mittel)", "C (niedrig)"]

PRIORITY_DISPLAY = {
    "": "— auswählen —",
    "A (hoch)": "A · hoch",
    "B (mittel)": "B · mittel",
    "C (niedrig)": "C · niedrig",
}

MEASURES_FILE = Path(__file__).resolve().parents[1] / "data" / "measures.json"
MEASURE_PICK_PLACEHOLDER = "— bitte auswählen —"


@st.cache_data(ttl=60)
def load_measures_map() -> dict:
    if MEASURES_FILE.exists():
        try:
            data = json.loads(MEASURES_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def normalize_measure_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

def validate_dimension_code(code: str) -> str:
    """
    Validiert und normalisiert den Dimensionscode.
    Erlaubte Beispiele: TD1.1, OG2.3, TD10.12
    """
    import re

    normalized = normalize_measure_text(code)

    if not normalized:
        raise ValueError("Dimensionscode fehlt.")
    if len(normalized) > 20:
        raise ValueError("Dimensionscode ist zu lang.")
    if not re.fullmatch(r"[A-Za-z]{1,5}\d+(?:[.\-_]\d+)*", normalized):
        raise ValueError(f"Ungültiger Dimensionscode: {normalized}")

    return normalized

@st.dialog("Maßnahmen-Vorschläge")
def measure_dialog(code: str, suggestions: list[str]) -> None:
    st.markdown(
        f"<div class='rgm-dialog-meta'>Dimension: <strong>{code}</strong></div>",
        unsafe_allow_html=True,
    )

    if not suggestions:
        st.info("Keine Vorschläge vorhanden.")
        return

    seen = set()
    uniq: list[str] = []
    for s in suggestions:
        s = (s or "").strip()
        key = s.lower()
        if s and key not in seen:
            seen.add(key)
            uniq.append(s)

    pick_key = f"dlg_pick_{code}"

    choice = st.radio(
        "Vorschläge",
        options=[MEASURE_PICK_PLACEHOLDER] + uniq,
        index=0,
        key=pick_key,
        label_visibility="collapsed",
    )

    if choice != MEASURE_PICK_PLACEHOLDER:
        st.session_state[f"action_{code}"] = choice
        st.rerun()
        
def render_measure_sharing_consent() -> None:
    st.info(
        "**Hinweis (Maßnahmen-Pool):**\n\n"
        "Sie können optional Ihre eingegebenen Maßnahmen **als Vorschläge für andere Nutzer** bereitstellen.\n"
        "Wenn Sie zustimmen, wird **ausschließlich der Text im Feld „Maßnahme“** gespeichert.\n\n"
        "Bitte tragen Sie dort **keine sensiblen Daten** ein."
    )

    choice = st.radio(
        "Möchten Sie Ihre Maßnahmen speichern und als Vorschläge für andere Nutzer zur Verfügung stellen?",
        options=["Nein", "Ja"],
        horizontal=True,
        key="share_measures_radio",
    )

    st.session_state["share_measures_opt_in"] = choice == "Ja"


def github_create_measure_issue(measure_text: str, dimension_code: str) -> int:
    """
    Erstellt ein GitHub-Issue mit Label 'measure:pending'.

    Erwartete Secrets in st.secrets:
      - GITHUB_OWNER
      - GITHUB_REPO
      - GITHUB_TOKEN
    """
    owner = str(st.secrets["GITHUB_OWNER"]).strip()
    repo = str(st.secrets["GITHUB_REPO"]).strip()
    token = str(st.secrets["GITHUB_TOKEN"]).strip()

    txt = normalize_measure_text(measure_text)
    code = validate_dimension_code(dimension_code)

    if len(txt) < 3:
        raise ValueError("Maßnahme zu kurz (min. 3 Zeichen).")
    if len(txt) > 240:
        raise ValueError("Maßnahme zu lang (max. 240 Zeichen).")

    # Titel bewusst kurz halten
    title = f"[Measure Pool] {code}: {txt[:80]}"

    # Format MUSS zu scripts/process_measure_issue.py passen
    body = (
        "### measure_text\n"
        f"{txt}\n\n"
        "### dimension_code\n"
        f"{code}\n"
    )

    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    payload = {
        "title": title,
        "body": body,
        "labels": ["measure:pending"],
    }
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "streamlit-measure-pool",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            response_text = resp.read().decode("utf-8")
            out = json.loads(response_text)

            issue_number = out.get("number")
            if not isinstance(issue_number, int):
                raise RuntimeError("GitHub hat keine gültige Issue-Nummer zurückgegeben.")

            return issue_number

    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            error_body = "<keine Fehlermeldung lesbar>"

        raise RuntimeError(
            f"GitHub-Issue konnte nicht erstellt werden ({e.code}): {error_body}"
        ) from e

    except urllib.error.URLError as e:
        raise RuntimeError(f"Netzwerkfehler beim Erstellen des GitHub-Issues: {e}") from e

def get_answers() -> dict:
    return st.session_state.get("answers", {}) or {}


def after_dash(text: str) -> str:
    """
    Gibt nur den Teil nach dem ersten '-' zurück (getrimmt).
    Beispiel:
    'Wissensmanagement - Wissensspeicherung' -> 'Wissensspeicherung'
    """
    s = "" if text is None else str(text)
    return s.split("-", 1)[1].strip() if "-" in s else s.strip()


def _stable_json(obj: dict) -> str:
    return json.dumps(obj or {}, sort_keys=True, ensure_ascii=False)


def collect_priorities_from_session(codes: list[str], keep_existing: dict) -> dict:
    """
    Baut ein priorities-Dict aus den aktuellen Widget-Werten in st.session_state.
    - codes: alle Dimension-Codes, die in dieser Ansicht gerendert wurden
    - keep_existing: vorhandene Werte, die erhalten bleiben sollen
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
    dark = bool(
        st.session_state.get("ui_dark_mode", st.session_state.get("dark_mode", False))
    )

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    soft_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)"
    header_bg = "rgba(255,255,255,0.08)" if dark else "rgba(127,127,127,0.10)"
    hover_bg = "rgba(255,255,255,0.07)" if dark else "rgba(0,0,0,0.035)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"

    # Wie in 05_Gesamtuebersicht.py
    card_bg = "rgba(255,255,255,0.05)" if dark else "rgba(255,255,255,1.00)"
    card_solid = "#111827" if dark else "#ffffff"
    text_color = "rgba(255,255,255,0.92)" if dark else "#111111"

    df_bg = "#0f172a" if dark else "#ffffff"
    df_header = "#0b1220" if dark else "#f3f4f6"
    df_grid = "rgba(255,255,255,0.10)" if dark else "rgba(0,0,0,0.10)"
    df_text = "rgba(250,250,250,0.92)" if dark else "#111111"
    df_muted = "rgba(250,250,250,0.70)" if dark else "rgba(0,0,0,0.60)"
    
    dlg_overlay = "rgba(2, 6, 23, 0.82)" if dark else "rgba(15, 23, 42, 0.24)"
    dlg_bg = "#0b1120" if dark else "#ffffff"
    dlg_surface = "#111827" if dark else "#f8fafc"
    dlg_row_bg = "#0f172a" if dark else "#ffffff"
    dlg_row_hover = "#1e293b" if dark else "#f3f4f6"
    dlg_row_selected = "#2a1b0f" if dark else "#fff7ed"
    dlg_row_selected_border = "#CA7406"

    btn2_bg = df_bg if dark else "#ffffff"
    btn2_text = df_text if dark else "#111111"

    st.markdown(
        f"""
<style>
  /* =========================
     Tokens / Container
     ========================= */
  div[data-testid="stAppViewContainer"] {{
    --rgm-td-blue: {TD_BLUE};
    --rgm-og-orange: {OG_ORANGE};
    --rgm-border: {border};
    --rgm-soft: {soft_bg};
    --rgm-header-bg: {header_bg};
    --rgm-card-bg: {card_bg};
    --rgm-card-solid: {card_solid};
    --rgm-text: {text_color};
    --rgm-df-bg: {df_bg};
    --rgm-df-header: {df_header};
    --rgm-df-grid: {df_grid};
    --rgm-df-text: {df_text};
    --rgm-df-muted: {df_muted};
    --rgm-shadow: {shadow};
  }}

  div[data-testid="stAppViewContainer"] .block-container {{
    max-width: 1200px;
    margin: 0 auto;
    padding-top: 1rem;
    padding-bottom: 6rem;
  }}

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
    background: var(--rgm-card-solid, #fff);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    padding: 18px 18px 14px 18px;
    box-shadow: var(--rgm-shadow);
  }}

  .rgm-accent-line {{
    height: 3px;
    width: 96px;
    border-radius: 999px;
    margin: 10px 0 14px 0;
    background: linear-gradient(90deg, var(--rgm-td-blue), var(--rgm-og-orange));
  }}

  .rgm-card {{
    background: var(--rgm-card-solid, #fff);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: var(--rgm-shadow);
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
    background: var(--rgm-border);
    margin: 16px 0 8px 0;
  }}

  /* =========================
     Expander
     ========================= */
  div[data-testid="stExpander"] {{
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: var(--rgm-shadow);
    background: var(--rgm-card-solid, #fff);
  }}

  div[data-testid="stExpander"] summary {{
    padding: 12px 14px !important;
    font-weight: 850 !important;
    color: var(--rgm-text, #111) !important;
    background: var(--rgm-header-bg) !important;
  }}

  div[data-testid="stExpander"] summary:hover {{
    background: {hover_bg} !important;
  }}

  div[data-testid="stExpander"] details {{
    border-radius: 14px;
  }}

  div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {{
    padding: 12px 14px 14px 14px;
    background: var(--rgm-card-solid, #fff);
  }}

  .rgm-pill {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid var(--rgm-border);
    background: var(--rgm-soft);
    color: var(--rgm-text, #111);
    font-size: 13px;
    font-weight: 750;
    margin: 8px 0 8px 0;
    width: fit-content;
  }}

  .rgm-field-label {{
    font-size: 15px;
    line-height: 1.2;
    font-weight: 600;
    margin: 0 0 0.45rem 0;
    color: var(--rgm-text, #111);
  }}

  div[data-testid="stTextInput"],
  div[data-testid="stSelectbox"],
  div[data-testid="stButton"] {{
    margin-top: 0 !important;
  }}

  /* =========================
     Feldgeometrie
     ========================= */
  :root {{
    --rgm-field-h: 48px;
    --rgm-field-radius: 12px;
    --rgm-field-px: 0.85rem;
  }}

  /* -------------------------
     TextInput
     ------------------------- */
  div[data-testid="stTextInput"] div[data-baseweb="input"] {{
    height: var(--rgm-field-h) !important;
    min-height: var(--rgm-field-h) !important;
    max-height: var(--rgm-field-h) !important;
  }}

  div[data-testid="stTextInput"] div[data-baseweb="input"] > div {{
    height: var(--rgm-field-h) !important;
    min-height: var(--rgm-field-h) !important;
    max-height: var(--rgm-field-h) !important;
    border-radius: var(--rgm-field-radius) !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center !important;
    padding: 0 !important;
    overflow: hidden !important;

    background: var(--rgm-df-bg) !important;
    border: 1px solid var(--rgm-border) !important;
    color: var(--rgm-df-text) !important;
  }}

  div[data-testid="stTextInput"] input {{
    height: 100% !important;
    min-height: 0 !important;
    max-height: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 var(--rgm-field-px) !important;
    border: 0 !important;
    line-height: 1.2 !important;
    box-shadow: none !important;
    background: transparent !important;

    color: var(--rgm-df-text) !important;
    -webkit-text-fill-color: var(--rgm-df-text) !important;
    caret-color: var(--rgm-df-text) !important;
  }}

  div[data-testid="stTextInput"] input::placeholder {{
    color: var(--rgm-df-muted) !important;
    opacity: 1 !important;
  }}

  /* -------------------------
     Selectbox
     ------------------------- */
  div[data-testid="stSelectbox"] div[data-baseweb="select"] {{
    height: var(--rgm-field-h) !important;
    min-height: var(--rgm-field-h) !important;
    max-height: var(--rgm-field-h) !important;
  }}

  div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
    height: var(--rgm-field-h) !important;
    min-height: var(--rgm-field-h) !important;
    max-height: var(--rgm-field-h) !important;
    border-radius: var(--rgm-field-radius) !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center !important;
    padding: 0 !important;
    overflow: hidden !important;

    background: var(--rgm-df-bg) !important;
    border: 1px solid var(--rgm-border) !important;
    color: var(--rgm-df-text) !important;
  }}

  div[data-testid="stSelectbox"] [role="combobox"] {{
    height: 100% !important;
    min-height: 0 !important;
    max-height: 100% !important;
    display: flex !important;
    align-items: center !important;
    margin: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    padding-left: var(--rgm-field-px) !important;
    padding-right: 2.1rem !important;
    line-height: 1.2 !important;

    color: var(--rgm-df-text) !important;
  }}

  div[data-testid="stSelectbox"] [role="combobox"] > * {{
    height: 100% !important;
    min-height: 0 !important;
    display: flex !important;
    align-items: center !important;
    margin: 0 !important;
  }}

  div[data-testid="stSelectbox"] [role="combobox"] span,
  div[data-testid="stSelectbox"] [role="combobox"] div {{
    line-height: 1.2 !important;
    color: var(--rgm-df-text) !important;
  }}

  /* Hover / Focus auf Feldern */
  div[data-testid="stTextInput"] div[data-baseweb="input"] > div:hover,
  div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover {{
    border-color: {TU_ORANGE} !important;
  }}

  div[data-testid="stTextInput"] div[data-baseweb="input"] > div:focus-within,
  div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {{
    border-color: {TU_ORANGE} !important;
    box-shadow: 0 0 0 3px rgba(202,116,6,0.18) !important;
  }}

  /* Browser Autofill sauber dunkel halten */
  input:-webkit-autofill,
  input:-webkit-autofill:hover,
  input:-webkit-autofill:focus,
  textarea:-webkit-autofill,
  textarea:-webkit-autofill:hover,
  textarea:-webkit-autofill:focus {{
    -webkit-text-fill-color: var(--rgm-df-text) !important;
    -webkit-box-shadow: 0 0 0px 1000px var(--rgm-df-bg) inset !important;
    transition: background-color 9999s ease-in-out 0s !important;
  }}

  /* -------------------------
     Dropdown / Popover
     ------------------------- */
  div[data-baseweb="popover"] {{
    color: var(--rgm-df-text) !important;
  }}

  div[data-baseweb="popover"] ul,
  div[data-baseweb="popover"] [role="listbox"] {{
    background: var(--rgm-card-solid) !important;
    border: 1px solid var(--rgm-border) !important;
    box-shadow: var(--rgm-shadow) !important;
  }}

  div[data-baseweb="popover"] li,
  div[data-baseweb="popover"] [role="option"] {{
    background: transparent !important;
    color: var(--rgm-df-text) !important;
  }}

  div[data-baseweb="popover"] li:hover,
  div[data-baseweb="popover"] [role="option"]:hover {{
    background: rgba(202,116,6,0.14) !important;
  }}

  /* -------------------------
     Icon-Button neben Maßnahme
     ------------------------- */
  div[data-testid="stExpanderDetails"] div[data-testid="stButton"] {{
    margin: 0 !important;
    padding: 0 !important;
  }}

  div[data-testid="stExpanderDetails"] div[data-testid="stButton"] > div {{
    height: var(--rgm-field-h) !important;
    min-height: var(--rgm-field-h) !important;
    max-height: var(--rgm-field-h) !important;
  }}

  div[data-testid="stExpanderDetails"] div[data-testid="stButton"] button,
  div[data-testid="stExpanderDetails"] div[data-testid="stButton"] button[kind] {{
    height: var(--rgm-field-h) !important;
    min-height: var(--rgm-field-h) !important;
    max-height: var(--rgm-field-h) !important;

    width: var(--rgm-field-h) !important;
    min-width: var(--rgm-field-h) !important;
    max-width: var(--rgm-field-h) !important;

    padding: 0 !important;
    margin: 0 !important;
    border-radius: var(--rgm-field-radius) !important;
    box-sizing: border-box !important;

    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1 !important;
  }}

  div[data-testid="stExpanderDetails"] div[data-testid="stButton"] button > div,
  div[data-testid="stExpanderDetails"] div[data-testid="stButton"] button span,
  div[data-testid="stExpanderDetails"] div[data-testid="stButton"] button p {{
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1 !important;

    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }}

  .stApp button[data-testid="baseButton-secondary"],
  .stApp div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]) {{
    background: {btn2_bg} !important;
    color: {btn2_text} !important;
    border: 1px solid var(--rgm-border) !important;
    border-radius: var(--rgm-field-radius) !important;
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

  /* =========================
     Dialog / Maßnahmen-Vorschläge
     ========================= */

  /* Overlay im Hintergrund */
  div[data-testid="stDialog"] {{
    background: {dlg_overlay} !important;
    backdrop-filter: blur(6px) !important;
  }}

  /* eigentliche Dialog-Karte: komplett deckend */
  div[data-testid="stDialog"] > div[role="dialog"],
  div[data-testid="stModal"] > div[role="dialog"],
  div[data-testid="stDialog"] div[role="dialog"],
  div[data-testid="stModal"] div[role="dialog"] {{
    width: min(920px, calc(100vw - 48px)) !important;
    max-width: 920px !important;
    height: auto !important;
    max-height: 84vh !important;

    background: {dlg_bg} !important;
    opacity: 1 !important;
    color: var(--rgm-text) !important;
    border: 1px solid var(--rgm-border) !important;
    border-radius: 18px !important;
    box-shadow: 0 24px 70px rgba(0,0,0,0.45) !important;
  }}

div[data-testid="stDialog"] div[role="dialog"] section,
div[data-testid="stModal"] div[role="dialog"] section {{
  max-height: 84vh !important;
  overflow: hidden !important;
  background: {dlg_bg} !important;
  opacity: 1 !important;
  color: var(--rgm-text) !important;
  padding: 0.25rem 0.25rem 0.6rem 0.25rem !important;
}}

  /* Titel + Texte */
  div[data-testid="stDialog"] div[role="dialog"] h1,
  div[data-testid="stDialog"] div[role="dialog"] h2,
  div[data-testid="stDialog"] div[role="dialog"] h3,
  div[data-testid="stModal"] div[role="dialog"] h1,
  div[data-testid="stModal"] div[role="dialog"] h2,
  div[data-testid="stModal"] div[role="dialog"] h3,
  div[data-testid="stDialog"] div[role="dialog"] p,
  div[data-testid="stDialog"] div[role="dialog"] span,
  div[data-testid="stDialog"] div[role="dialog"] label,
  div[data-testid="stModal"] div[role="dialog"] p,
  div[data-testid="stModal"] div[role="dialog"] span,
  div[data-testid="stModal"] div[role="dialog"] label {{
    color: var(--rgm-text) !important;
    opacity: 1 !important;
  }}

  .rgm-dialog-meta {{
    font-size: 14px;
    color: var(--rgm-df-muted);
    margin: 0.15rem 0 0.8rem 0;
  }}
  
/* =========================
   Dialog / Maßnahmen-Vorschläge
   stabiler Scroll-Host + keine Karten-Überlappung
   ========================= */

/* Der Radio-Widget-Block selbst wird zum Scroll-Host */
div[data-testid="stDialog"] div[role="dialog"] [class*="st-key-dlg_pick_"],
div[data-testid="stModal"] div[role="dialog"] [class*="st-key-dlg_pick_"] {{
  max-height: min(420px, calc(84vh - 170px)) !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  overscroll-behavior: contain !important;
  -webkit-overflow-scrolling: touch !important;
  padding-right: 0.25rem !important;
  box-sizing: border-box !important;
  min-height: 0 !important;
}}

/* Scrollbar nur für den Maßnahmen-Block */
div[data-testid="stDialog"] div[role="dialog"] [class*="st-key-dlg_pick_"]::-webkit-scrollbar,
div[data-testid="stModal"] div[role="dialog"] [class*="st-key-dlg_pick_"]::-webkit-scrollbar {{
  width: 10px;
}}

div[data-testid="stDialog"] div[role="dialog"] [class*="st-key-dlg_pick_"]::-webkit-scrollbar-thumb,
div[data-testid="stModal"] div[role="dialog"] [class*="st-key-dlg_pick_"]::-webkit-scrollbar-thumb {{
  background: rgba(202,116,6,0.45);
  border-radius: 999px;
}}

/* Radiogroup sauber vertikal, ohne Shrink/Überlagerung */
div[data-testid="stDialog"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"],
div[data-testid="stModal"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] {{
  display: flex !important;
  flex-direction: column !important;
  align-items: stretch !important;
  gap: 0.55rem !important;

  background: {dlg_surface} !important;
  border: 1px solid var(--rgm-border) !important;
  border-radius: 16px !important;
  padding: 0.5rem !important;
  color: var(--rgm-df-text) !important;
  box-sizing: border-box !important;
}}

/* Jede Karte bleibt ein eigener Block */
div[data-testid="stDialog"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] label[data-baseweb="radio"],
div[data-testid="stModal"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] label[data-baseweb="radio"] {{
  display: flex !important;
  align-items: flex-start !important;
  gap: 0.85rem !important;

  width: 100% !important;
  min-height: 64px !important;
  margin: 0 !important;
  padding: 0.95rem 1rem !important;

  flex: 0 0 auto !important;
  box-sizing: border-box !important;
  position: relative !important;

  background: {dlg_row_bg} !important;
  border: 1px solid transparent !important;
  border-radius: 14px !important;
  opacity: 1 !important;
  transition: background 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
}}

div[data-testid="stDialog"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] label[data-baseweb="radio"]:hover,
div[data-testid="stModal"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] label[data-baseweb="radio"]:hover {{
  background: {dlg_row_hover} !important;
  border-color: rgba(202,116,6,0.22) !important;
}}

div[data-testid="stDialog"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] label[data-baseweb="radio"]:has(input:checked),
div[data-testid="stModal"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {{
  background: {dlg_row_selected} !important;
  border-color: {dlg_row_selected_border} !important;
  box-shadow: 0 0 0 2px rgba(202,116,6,0.12) inset !important;
}}

/* Radio-Layout innen */
div[data-testid="stDialog"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] label[data-baseweb="radio"] > div,
div[data-testid="stModal"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] label[data-baseweb="radio"] > div {{
  margin: 0 !important;
  position: static !important;
}}

div[data-testid="stDialog"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] label[data-baseweb="radio"] > div:first-child,
div[data-testid="stModal"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] label[data-baseweb="radio"] > div:first-child {{
  flex: 0 0 auto !important;
  display: flex !important;
  align-items: flex-start !important;
  justify-content: center !important;
  padding-top: 0.1rem !important;
}}

div[data-testid="stDialog"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] label[data-baseweb="radio"] > div:last-child,
div[data-testid="stModal"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] label[data-baseweb="radio"] > div:last-child {{
  flex: 1 1 auto !important;
  min-width: 0 !important;
}}

/* Text sauber umbrechen */
div[data-testid="stDialog"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] p,
div[data-testid="stDialog"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] span,
div[data-testid="stModal"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] p,
div[data-testid="stModal"] div[role="dialog"] [class*="st-key-dlg_pick_"] [role="radiogroup"] span {{
  margin: 0 !important;
  color: var(--rgm-df-text) !important;
  opacity: 1 !important;
  white-space: normal !important;
  word-break: break-word !important;
  overflow-wrap: anywhere !important;
  line-height: 1.5 !important;
  font-size: 15px !important;
  font-weight: 500 !important;
}}

/* Radiogroup nur als äußerer Block */
div[data-testid="stDialog"] div[role="dialog"] [role="radiogroup"],
div[data-testid="stModal"] div[role="dialog"] [role="radiogroup"] {{
  display: block !important;
  background: {dlg_surface} !important;
  border: 1px solid var(--rgm-border) !important;
  border-radius: 16px !important;
  padding: 0.5rem !important;
  color: var(--rgm-df-text) !important;
  box-sizing: border-box !important;
}}

/* NUR die echten Radio-Karten stylen */
div[data-testid="stDialog"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"],
div[data-testid="stModal"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"] {{
  display: flex !important;
  align-items: flex-start !important;
  gap: 0.85rem !important;

  width: 100% !important;
  min-height: 64px !important;
  margin: 0 0 0.55rem 0 !important;
  padding: 0.95rem 1rem !important;

  box-sizing: border-box !important;
  position: relative !important;

  background: {dlg_row_bg} !important;
  border: 1px solid transparent !important;
  border-radius: 14px !important;
  opacity: 1 !important;
  transition: background 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
}}

div[data-testid="stDialog"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"]:last-of-type,
div[data-testid="stModal"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"]:last-of-type {{
  margin-bottom: 0 !important;
}}

div[data-testid="stDialog"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"]:hover,
div[data-testid="stModal"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"]:hover {{
  background: {dlg_row_hover} !important;
  border-color: rgba(202,116,6,0.22) !important;
}}

div[data-testid="stDialog"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"]:has(input:checked),
div[data-testid="stModal"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {{
  background: {dlg_row_selected} !important;
  border-color: {dlg_row_selected_border} !important;
  box-shadow: 0 0 0 2px rgba(202,116,6,0.12) inset !important;
}}

/* Innere Radio-Struktur sauber ausrichten */
div[data-testid="stDialog"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"] > div,
div[data-testid="stModal"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"] > div {{
  margin: 0 !important;
  position: static !important;
}}

div[data-testid="stDialog"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"] > div:first-child,
div[data-testid="stModal"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"] > div:first-child {{
  flex: 0 0 auto !important;
  display: flex !important;
  align-items: flex-start !important;
  justify-content: center !important;
  padding-top: 0.1rem !important;
}}

div[data-testid="stDialog"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"] > div:last-child,
div[data-testid="stModal"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"] > div:last-child {{
  flex: 1 1 auto !important;
  min-width: 0 !important;
}}

/* Text NUR in den echten Radio-Karten */
div[data-testid="stDialog"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"] p,
div[data-testid="stDialog"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"] span,
div[data-testid="stModal"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"] p,
div[data-testid="stModal"] div[role="dialog"] [role="radiogroup"] label[data-baseweb="radio"] span {{
  margin: 0 !important;
  color: var(--rgm-df-text) !important;
  opacity: 1 !important;
  white-space: normal !important;
  word-break: break-word !important;
  overflow-wrap: anywhere !important;
  line-height: 1.5 !important;
  font-size: 15px !important;
  font-weight: 500 !important;
}}

/* Radio-Farbe */
div[data-testid="stDialog"] input[type="radio"],
div[data-testid="stModal"] input[type="radio"] {{
  accent-color: #639A00 !important;
}}

  /* Clipboard-Button / "Vorschläge anzeigen" im Expander sichtbarer */
  div[data-testid="stExpanderDetails"] div[data-testid="stButton"] button {{
    background: var(--rgm-df-bg) !important;
    color: var(--rgm-df-text) !important;
    border: 1px solid var(--rgm-border) !important;
  }}

  div[data-testid="stExpanderDetails"] div[data-testid="stButton"] button:hover {{
    background: {TU_ORANGE} !important;
    border-color: {TU_ORANGE} !important;
    color: #ffffff !important;
  }}

  div[data-testid="stExpanderDetails"] div[data-testid="stButton"] button * {{
    color: inherit !important;
  }}

  @media (max-width: 700px) {{
    div[data-testid="stDialog"] > div[role="dialog"],
    div[data-testid="stModal"] > div[role="dialog"],
    div[data-testid="stDialog"] div[role="dialog"],
    div[data-testid="stModal"] div[role="dialog"] {{
      width: calc(100vw - 20px) !important;
      max-width: calc(100vw - 20px) !important;
      max-height: 88vh !important;
      border-radius: 16px !important;
    }}

    div[data-testid="stDialog"] div[role="dialog"] section,
    div[data-testid="stModal"] div[role="dialog"] section {{
      max-height: 88vh !important;
    }}
  }}
</style>
        """,
        unsafe_allow_html=True,
    )


def submit_measures_from_priorities(priorities: dict) -> tuple[int, int]:
    """
    Sendet alle Maßnahmen aus priorities als GitHub-Issues,
    sofern sie nicht leer sind. Dedupe in der Session verhindert Spam.
    """
    submitted = st.session_state.setdefault("submitted_measures", [])
    submitted_set = set(submitted)

    created = 0
    skipped = 0

    for code, item in (priorities or {}).items():
        txt = normalize_measure_text((item or {}).get("action", ""))
        if not txt:
            skipped += 1
            continue

        key = f"{code}||{txt.lower()}"
        if key in submitted_set:
            skipped += 1
            continue

        github_create_measure_issue(txt, code)

        submitted.append(key)
        submitted_set.add(key)
        created += 1

    st.session_state["submitted_measures"] = submitted
    return created, skipped

def main() -> None:
    init_session_state()
    _inject_priorisierung_css()

    st.markdown('<div class="rgm-page">', unsafe_allow_html=True)

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

    render_measure_sharing_consent()
    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)

    model = load_model_config()
    answers = get_answers()
    global_target = float(st.session_state.get("global_target_level", 3.0))
    dim_targets = st.session_state.get("dimension_targets", {}) or {}

    priorities_committed = st.session_state.get("priorities", {}) or {}

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

    rendered_codes: list[str] = []
    draft = st.session_state.get("priorities_draft", {}) or {}
    measures_map = load_measures_map()

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
                st.markdown(
                    f"<div class='rgm-pill'>Gap (Soll–Ist): <b>{gap:.2f}</b> Reifegradstufen</div>",
                    unsafe_allow_html=True,
                )

                suggestions = measures_map.get(code, []) or []

                # Zeile 1: Labels
                l1c1, l1c2, l1c3 = st.columns([2.35, 6.35, 0.50], gap="small")
                with l1c1:
                    st.markdown("<div class='rgm-field-label'>Priorität</div>", unsafe_allow_html=True)
                with l1c2:
                    st.markdown("<div class='rgm-field-label'>Maßnahme</div>", unsafe_allow_html=True)
                with l1c3:
                    st.markdown("<div class='rgm-field-label'>&nbsp;</div>", unsafe_allow_html=True)

                # Zeile 1: Felder
                r1c1, r1c2, r1c3 = st.columns([2.35, 6.35, 0.50], gap="small")
                with r1c1:
                    st.selectbox(
                        "Priorität",
                        options=PRIORITY_OPTIONS,
                        index=default_index,
                        key=f"prio_{code}",
                        label_visibility="collapsed",
                        format_func=lambda x: PRIORITY_DISPLAY.get(x, x),
                        help="A = hoch, B = mittel, C = niedrig",
                    )

                with r1c2:
                    st.text_input(
                        "Maßnahme",
                        value=prev_action,
                        key=f"action_{code}",
                        placeholder="z. B. Redaktionsleitfaden erstellen",
                        label_visibility="collapsed",
                    )

                with r1c3:
                    if st.button(
                        "📋",
                        key=f"open_measures_{code}",
                        disabled=not suggestions,
                        help="Vorschläge anzeigen",
                        use_container_width=False,
                    ):
                        st.session_state.pop(f"dlg_pick_{code}", None)
                        measure_dialog(code, suggestions)

                st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

                # Zeile 2: Labels
                l2c1, l2c2 = st.columns([1, 1], gap="medium")
                with l2c1:
                    st.markdown("<div class='rgm-field-label'>Verantwortlich</div>", unsafe_allow_html=True)
                with l2c2:
                    st.markdown("<div class='rgm-field-label'>Zeitraum</div>", unsafe_allow_html=True)

                # Zeile 2: Felder
                r2c1, r2c2 = st.columns([1, 1], gap="medium")
                with r2c1:
                    st.text_input(
                        "Verantwortlich",
                        value=prev_resp,
                        key=f"resp_{code}",
                        placeholder="z. B. Christian Koch",
                        label_visibility="collapsed",
                    )
                with r2c2:
                    st.text_input(
                        "Zeitraum",
                        value=prev_time,
                        key=f"timeframe_{code}",
                        placeholder="z. B. Q1/2026",
                        label_visibility="collapsed",
                    )

        st.session_state["priorities_draft"] = collect_priorities_from_session(
            codes=rendered_codes,
            keep_existing=st.session_state.get("priorities_draft", {}),
        )

    draft_now = st.session_state.get("priorities_draft", {}) or {}
    committed_now = st.session_state.get("priorities_committed", {}) or {}
    dirty = _stable_json(draft_now) != _stable_json(committed_now)

    if st.button(
        "Priorisierungen übernehmen",
        type="primary",
        use_container_width=True,
        disabled=not dirty,
    ):
        st.session_state["priorities"] = copy.deepcopy(draft_now)
        st.session_state["priorities_committed"] = copy.deepcopy(draft_now)

        if st.session_state.get("share_measures_opt_in", False):
            try:
                created, skipped = submit_measures_from_priorities(draft_now)
                st.success(
                    f"Priorisierungen übernommen. {created} Vorschlag/Vorschläge automatisch übermittelt "
                    f"({skipped} übersprungen)."
                )
            except Exception as e:
                st.warning(
                    f"Priorisierungen übernommen, aber die Übermittlung der Vorschläge ist fehlgeschlagen: {e}"
                )
        else:
            st.success("Priorisierungen wurden übernommen.")

        st.rerun()

    if dirty:
        st.warning(
            "Sie haben Priorisierungen geändert, die noch nicht übernommen wurden. "
            "Bitte zuerst „Priorisierungen übernehmen“ klicken, damit diese Werte verwendet werden."
        )

    st.markdown("---")

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