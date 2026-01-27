# pages/00_Einfuehrung.py
from __future__ import annotations

import html
import streamlit as st

from core.state import init_session_state
from core.model_loader import load_tool_meta

TU_GREEN = "#639A00"
TU_ORANGE = "#CA7406"
TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"


def main() -> None:
    init_session_state()

    meta = load_tool_meta()
    title = meta.get("title", "Reifegradmodell für die Technische Dokumentation")

    # Darkmode robust (falls App "ui_dark_mode" nutzt)
    dark = bool(st.session_state.get("ui_dark_mode", st.session_state.get("dark_mode", False)))

    # Farbtokens abhängig vom Darkmode
    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    soft_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"

    # Secondary-Button Grundzustand (Zurück)
    btn2_bg = "rgba(255,255,255,0.06)" if dark else "#ffffff"
    btn2_text = "rgba(250,250,250,0.92)" if dark else "#111111"

    st.markdown(
        f"""
<style>
  /* Seite begrenzen -> wirkt „produktmäßig“ */
  .rgm-page {{
    max-width: 1200px;
    margin: 0 auto;
    padding-bottom: 6px;
  }}

  /* Typografie */
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

  /* Hero */
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

  /* Flex-Row für TD/OG (statt st.columns) */
  .rgm-row {{
    display: flex;
    gap: 38px;
    align-items: center;
    margin-top: 18px;
  }}

  .rgm-left {{
    flex: 0 0 36%;
    min-width: 320px;
  }}

  .rgm-right {{
    flex: 1 1 64%;
  }}

  @media (max-width: 980px) {{
    .rgm-row {{
      flex-direction: column;
      align-items: stretch;
      gap: 16px;
    }}
    .rgm-left {{
      flex: 1 1 auto;
      min-width: 0;
    }}
  }}

  /* Section Heading */
  .rgm-section-title {{
    font-weight: 850;
    font-size: 16px;
    margin: 0 0 6px 0;
  }}
  .rgm-td-title {{ color: {TD_BLUE}; }}
  .rgm-og-title {{ color: {OG_ORANGE}; }}

  /* Cards (Basis-Rahmen für Konsistenz mit anderen Seiten) */
  .rgm-card {{
    background: var(--rgm-card-bg, #fff);
    border: 1px solid {border};
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: {shadow};
  }}

  .rgm-card-td {{
    border: 2px solid {TD_BLUE};
  }}
  .rgm-card-og {{
    border: 2px solid {OG_ORANGE};
  }}

  .rgm-card-head {{
    text-align: center;
    font-weight: 850;
    margin: 0 0 12px 0;
    font-size: 15px;
    color: var(--rgm-text, #111);
  }}

  /* Liste wie „professionelle Chips“ */
  .rgm-list {{
    margin: 0;
    padding-left: 0;
    list-style: none;
  }}

  .rgm-li {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 10px;
    border-radius: 10px;
    margin: 7px 0;
    background: {soft_bg};
    color: var(--rgm-text, #111);
    font-size: 15px;
    line-height: 1.5;
  }}

  .rgm-li:hover {{
    filter: brightness(1.02);
  }}

  /* Badges */
  .rgm-badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    min-width: 44px;
    padding: 0 10px;
    border-radius: 999px;
    font-weight: 850;
    font-size: 13px;
    letter-spacing: 0.2px;
    white-space: nowrap;
  }}

  .rgm-badge-td {{
    color: {TD_BLUE};
    border: 1.8px solid {TD_BLUE};
    background: rgba(47, 61, 184, 0.08);
  }}

  .rgm-badge-og {{
    color: {OG_ORANGE};
    border: 1.8px solid {OG_ORANGE};
    background: rgba(242, 140, 40, 0.10);
  }}

  .rgm-li-text {{
    flex: 1;
  }}

  /* Trennlinie zwischen TD und OG */
  .rgm-divider {{
    height: 1px;
    background: {border};
    margin: 18px 0 8px 0;
  }}

  /* =========================================
     NAV-BUTTONS: Secondary NUR im Nav-Bereich
     (verhindert Styling von Download/Filter/etc.)
     ========================================= */

  .rgm-nav button[data-testid="baseButton-secondary"],
  .rgm-nav div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]) {{
    background: {btn2_bg} !important;
    color: {btn2_text} !important;
    border: 1px solid {border} !important;
    border-radius: 10px !important;
    font-weight: 650 !important;
    opacity: 1 !important;
    transition: background 120ms ease, border-color 120ms ease, color 120ms ease;
  }}

  .rgm-nav button[data-testid="baseButton-secondary"] *,
  .rgm-nav div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]) * {{
    color: inherit !important;
  }}

  .rgm-nav button[data-testid="baseButton-secondary"]:not(:disabled):hover,
  .rgm-nav div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]):not(:disabled):hover {{
    background: {TU_ORANGE} !important;
    border-color: {TU_ORANGE} !important;
    color: #ffffff !important;
  }}

  .rgm-nav button[data-testid="baseButton-secondary"]:not(:disabled):hover *,
  .rgm-nav div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]):not(:disabled):hover * {{
    color: #ffffff !important;
  }}

  .rgm-nav button[data-testid="baseButton-secondary"]:focus,
  .rgm-nav div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]):focus {{
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(99,154,0,0.25) !important;
  }}
</style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="rgm-page">', unsafe_allow_html=True)

    # Hero
    st.markdown(
        f"""
<div class="rgm-hero">
  <div class="rgm-h1">Willkommen zum {html.escape(str(title))}</div>
  <div class="rgm-accent-line"></div>

  <p class="rgm-lead">
    Das Reifegradmodell ist ein fragenbasiertes Tool zur Erhebung der Reifegrade der technischen Dokumentation.
    Es wurde entwickelt, um Unternehmen eine Hilfestellung bei der nachhaltigen Weiterentwicklung der technischen
    Dokumentation zu geben.
  </p>

  <div style="height:10px"></div>

  <p class="rgm-muted">
    Das Reifegradmodell basiert auf Ergebnissen einer Recherche zu bestehenden Reifegradmodellen sowie der Auswertung
    von Interviews. Das RGM besteht aus 33 Subdimensionen, aufgeteilt auf 8 Dimensionen und ist modellhaft zu verstehen.
    Dies bedeutet, dass die Aspekte der Dimensionen je nach Organisation unterschiedlich interpretiert werden können.
    Die Nutzenden sind herzlich dazu eingeladen, eigene, unternehmensspezifische Punkte zu ergänzen.
  </p>

  <div style="height:10px"></div>

  <p class="rgm-muted" style="margin-bottom:0">
    Das Tool deckt die folgenden Bereiche ab. Die jeweiligen Betrachtungsobjekte sind farblich hervorgehoben.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    # TD (Flex Row)
    st.markdown(
        f"""
<div class="rgm-row">
  <div class="rgm-left">
    <div class="rgm-section-title rgm-td-title">Technische Dokumentation (TD)</div>
    <div class="rgm-muted">Relevante Themenbereiche der technischen Dokumentation.</div>
  </div>

  <div class="rgm-right">
    <div class="rgm-card rgm-card-td">
      <div class="rgm-card-head">Technische Dokumentation</div>
      <ul class="rgm-list">
        <li class="rgm-li"><span class="rgm-badge rgm-badge-td">TD1</span><span class="rgm-li-text">Redaktionsprozess</span></li>
        <li class="rgm-li"><span class="rgm-badge rgm-badge-td">TD2</span><span class="rgm-li-text">Content Management</span></li>
        <li class="rgm-li"><span class="rgm-badge rgm-badge-td">TD3</span><span class="rgm-badge rgm-badge-td" style="display:none"></span><span class="rgm-li-text">Content Delivery</span></li>
        <li class="rgm-li"><span class="rgm-badge rgm-badge-td">TD4</span><span class="rgm-li-text">Zielgruppenorientierung</span></li>
      </ul>
    </div>
  </div>
</div>

<div class="rgm-divider"></div>
        """,
        unsafe_allow_html=True,
    )

    # OG (Flex Row)
    st.markdown(
        f"""
<div class="rgm-row">
  <div class="rgm-left">
    <div class="rgm-section-title rgm-og-title">Organisation (OG)</div>
    <div class="rgm-muted">
      Relevante Themenbereiche der Organisation, die mit der technischen Dokumentation in Verbindung stehen bzw.
      diese beeinflussen.
    </div>
  </div>

  <div class="rgm-right">
    <div class="rgm-card rgm-card-og">
      <div class="rgm-card-head">Organisation</div>
      <ul class="rgm-list">
        <li class="rgm-li"><span class="rgm-badge rgm-badge-og">OG1</span><span class="rgm-li-text">Wissensmanagement</span></li>
        <li class="rgm-li"><span class="rgm-badge rgm-badge-og">OG2</span><span class="rgm-li-text">Organisationale Verankerung der technischen Dokumentation</span></li>
        <li class="rgm-li"><span class="rgm-badge rgm-badge-og">OG3</span><span class="rgm-li-text">Schnittstellen</span></li>
        <li class="rgm-li"><span class="rgm-badge rgm-badge-og">OG4</span><span class="rgm-li-text">Technologische Infrastruktur</span></li>
      </ul>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Navigation (scoped)
    st.markdown('<div class="rgm-nav">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Zurück", use_container_width=True):
            st.session_state["nav_request"] = "Start"
            st.rerun()

    with c2:
        if st.button("Weiter zur Ausfüllhinweise", type="primary", use_container_width=True):
            st.session_state["nav_request"] = "Ausfüllhinweise"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
