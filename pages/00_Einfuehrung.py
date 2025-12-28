# pages/00_Einfuehrung.py
from __future__ import annotations

import html
import streamlit as st

from core.state import init_session_state
from core.model_loader import load_tool_meta

TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"


def main():
    init_session_state()

    meta = load_tool_meta()
    title = meta.get("title", "Reifegradmodell für die Technische Dokumentation")

    # ---- CSS: Theme-kompatibel (Light/Dark) ----
    st.markdown(
        f"""
<style>
  /* Seite insgesamt: Text größer */
  .rgm-muted {{
    color: var(--rgm-text, #111);
    font-size: 15px;
    line-height: 1.75;
  }}

  .rgm-paragraph {{
    margin-top: 8px;
    margin-bottom: 14px;
    max-width: 1100px;
  }}

  .rgm-note {{
    margin: 8px 0 22px 0;
    max-width: 1100px;
  }}

  /* Bereichsüberschriften */
  .rgm-section-title {{
    font-weight: 800;
    margin-top: 4px;
    margin-bottom: 6px;
    font-size: 16px;
  }}

  .rgm-td-title {{
    color: {TD_BLUE};
    font-weight: 800;
  }}

  .rgm-og-title {{
    color: {OG_ORANGE};
    font-weight: 800;
  }}

  /* Rechte Boxen (TD/OG) */
  .rgm-box {{
    background: var(--rgm-card-bg, #fff);
    padding: 14px 18px;
    margin: 6px 0 0 0;

    /* Optional: leichte Rundung, wirkt in Dark Mode besser */
    border-radius: 10px;
  }}

  .rgm-box-td {{
    border: 2px solid {TD_BLUE};
  }}

  .rgm-box-og {{
    border: 2px solid {OG_ORANGE};
  }}

  .rgm-box-head {{
    text-align: center;
    font-weight: 800;
    margin-bottom: 10px;
    font-size: 15px;
    color: var(--rgm-text, #111);
  }}

  .rgm-bullets {{
    margin: 0;
    padding-left: 22px;
    font-size: 15px;
    line-height: 1.7;
    color: var(--rgm-text, #111);
  }}

  .rgm-bullets li {{
    margin: 6px 0;
  }}

  /* Codes (TD1/OG1) fett und farbig */
  .rgm-code-td {{
    color: {TD_BLUE};
    font-weight: 800;
  }}

  .rgm-code-og {{
    color: {OG_ORANGE};
    font-weight: 800;
  }}
</style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"### Willkommen zum {html.escape(str(title))}")

    # ---- Intro-Text ohne Box ----
    st.markdown(
        """
<div class="rgm-muted rgm-paragraph">
  Das Reifegradmodell ist ein fragenbasiertes Tool zur Erhebung der Reifegrade der technischen Dokumentation.
  Es wurde entwickelt, um Unternehmen eine Hilfestellung bei der nachhaltigen Weiterentwicklung der technischen
  Dokumentation zu geben.
</div>

<div class="rgm-muted rgm-paragraph">
  Das Reifegradmodell basiert auf Ergebnissen einer Recherche zu bestehenden Reifegradmodellen sowie der Auswertung
  von Interviews. Das RGM besteht aus 33 Subdimensionen, aufgeteilt auf 8 Dimensionen und ist modellhaft zu verstehen.
  Dies bedeutet, dass die Aspekte der Dimensionen je nach Organisation unterschiedlich interpretiert werden können.
  Die Nutzenden sind herzlich dazu eingeladen, eigene, unternehmensspezifische Punkte zu ergänzen.
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="rgm-muted rgm-note">
  Das Tool deckt die folgenden Bereiche ab. Die jeweiligen Betrachtungsobjekte sind farblich hervorgehoben.
</div>
        """,
        unsafe_allow_html=True,
    )

    # --- TD Block ---
    col_left, col_right = st.columns([1.1, 1.9], gap="large")

    with col_left:
        st.markdown(
            f"""
<div class="rgm-section-title rgm-td-title">Technische Dokumentation (TD):</div>
<div class="rgm-muted">Relevante Themenbereiche der technischen Dokumentation.</div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown(
            f"""
<div class="rgm-box rgm-box-td">
  <div class="rgm-box-head">Technische Dokumentation</div>
  <ul class="rgm-bullets">
    <li><span class="rgm-code-td">TD1</span> Redaktionsprozess</li>
    <li><span class="rgm-code-td">TD2</span> Content Management</li>
    <li><span class="rgm-code-td">TD3</span> Content Delivery</li>
    <li><span class="rgm-code-td">TD4</span> Zielgruppenorientierung</li>
  </ul>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # --- OG Block ---
    col_left2, col_right2 = st.columns([1.1, 1.9], gap="large")

    with col_left2:
        st.markdown(
            f"""
<div class="rgm-section-title rgm-og-title">Organisation (OG):</div>
<div class="rgm-muted">
  Relevante Themenbereiche der Organisation, die mit der technischen Dokumentation in Verbindung stehen bzw.
  diese beeinflussen.
</div>
            """,
            unsafe_allow_html=True,
        )

    with col_right2:
        st.markdown(
            f"""
<div class="rgm-box rgm-box-og">
  <div class="rgm-box-head">Organisation</div>
  <ul class="rgm-bullets">
    <li><span class="rgm-code-og">OG1</span> Wissensmanagement</li>
    <li><span class="rgm-code-og">OG2</span> Organisationale Verankerung der technischen Dokumentation</li>
    <li><span class="rgm-code-og">OG3</span> Schnittstellen</li>
    <li><span class="rgm-code-og">OG4</span> Technologische Infrastruktur</li>
  </ul>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Navigation (WICHTIG: nur nav_request setzen)
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Zurück", use_container_width=True):
            st.session_state["nav_request"] = "Start"
            st.rerun()
    with c2:
        if st.button("Weiter zur Ausfüllhinweise", type="primary", use_container_width=True):
            st.session_state["nav_request"] = "Ausfüllhinweise"
            st.rerun()


if __name__ == "__main__":
    main()
