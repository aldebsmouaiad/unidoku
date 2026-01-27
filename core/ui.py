from __future__ import annotations
import streamlit as st

TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"
TU_ORANGE = "#CA7406"
TU_GREEN = "#639A00"

def is_dark_mode() -> bool:
    # Robust: unterstützt beide Keys
    return bool(st.session_state.get("ui_dark_mode", st.session_state.get("dark_mode", False)))

def ui_tokens(dark: bool) -> dict:
    return {
        "dark": dark,
        "TD_BLUE": TD_BLUE,
        "OG_ORANGE": OG_ORANGE,
        "TU_ORANGE": TU_ORANGE,
        "TU_GREEN": TU_GREEN,
        "border": "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)",
        "soft_bg": "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)",
        "header_bg": "rgba(255,255,255,0.08)" if dark else "rgba(127,127,127,0.10)",
        "zebra_bg": "rgba(255,255,255,0.04)" if dark else "rgba(0,0,0,0.018)",
        "hover_bg": "rgba(255,255,255,0.07)" if dark else "rgba(0,0,0,0.035)",
        "shadow": "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)",
        "btn2_bg": "rgba(255,255,255,0.06)" if dark else "#ffffff",
        "btn2_text": "rgba(250,250,250,0.92)" if dark else "#111111",
    }

def inject_base_css(t: dict, limit_secondary_to_nav: bool = False) -> None:
    """
    Injiziert das gemeinsame Design.
    limit_secondary_to_nav:
      - False: wirkt global auf alle secondary Buttons (dein aktuelles Verhalten)
      - True: wirkt nur innerhalb eines Wrappers .rgm-nav (empfohlen für spätere Seiten)
    """
    border = t["border"]
    soft_bg = t["soft_bg"]
    header_bg = t["header_bg"]
    zebra_bg = t["zebra_bg"]
    hover_bg = t["hover_bg"]
    shadow = t["shadow"]

    TD_BLUE = t["TD_BLUE"]
    OG_ORANGE = t["OG_ORANGE"]
    TU_ORANGE = t["TU_ORANGE"]

    btn2_bg = t["btn2_bg"]
    btn2_text = t["btn2_text"]

    scope = ".rgm-nav " if limit_secondary_to_nav else ".stApp "
    # (scope wird nur für secondary buttons genutzt; rest bleibt global über .rgm- Klassen)

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

  /* Tabellen */
  .rgm-table-wrap {{
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    border-radius: 12px;
  }}
  .rgm-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    min-width: 760px;
    background: var(--rgm-card-bg, #fff);
    border: 1px solid {border};
    border-radius: 12px;
    overflow: hidden;
  }}
  .rgm-table thead th {{
    position: sticky;
    top: 0;
    z-index: 2;
    text-align: left;
    padding: 10px 10px;
    font-weight: 850;
    font-size: 13px;
    color: var(--rgm-text, #111);
    background: {header_bg};
    border-bottom: 1px solid {border};
    vertical-align: top;
    white-space: nowrap;
  }}
  .rgm-table tbody td {{
    padding: 10px 10px;
    font-size: 13px;
    color: var(--rgm-text, #111);
    border-bottom: 1px solid {border};
    vertical-align: top;
  }}
  .rgm-table tbody tr:nth-child(even) td {{ background: {zebra_bg}; }}
  .rgm-table tbody tr:hover td {{ background: {hover_bg}; }}
  .rgm-table tr:last-child td {{ border-bottom: none; }}

  /* Secondary Buttons */
  {scope}button[data-testid="baseButton-secondary"],
  {scope}div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]) {{
    background: {btn2_bg} !important;
    color: {btn2_text} !important;
    border: 1px solid {border} !important;
    border-radius: 10px !important;
    font-weight: 650 !important;
    opacity: 1 !important;
    transition: background 120ms ease, border-color 120ms ease, color 120ms ease;
  }}
  {scope}button[data-testid="baseButton-secondary"] *,
  {scope}div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]) * {{
    color: inherit !important;
  }}
  {scope}button[data-testid="baseButton-secondary"]:not(:disabled):hover,
  {scope}div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]):not(:disabled):hover {{
    background: {TU_ORANGE} !important;
    border-color: {TU_ORANGE} !important;
    color: #ffffff !important;
  }}
  {scope}button[data-testid="baseButton-secondary"]:not(:disabled):hover *,
  {scope}div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]):not(:disabled):hover * {{
    color: #ffffff !important;
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

def init_ui(limit_secondary_to_nav: bool = False) -> dict:
    dark = is_dark_mode()
    t = ui_tokens(dark)
    inject_base_css(t, limit_secondary_to_nav=limit_secondary_to_nav)
    return t
