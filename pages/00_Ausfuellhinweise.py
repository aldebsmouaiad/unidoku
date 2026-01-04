# pages/00_Ausfuellhinweise.py
from __future__ import annotations

import streamlit as st
from core.state import init_session_state

TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"


def main() -> None:
    init_session_state()

    dark = bool(st.session_state.get("dark_mode", False))

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    soft_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)"
    header_bg = "rgba(255,255,255,0.08)" if dark else "rgba(127,127,127,0.10)"
    zebra_bg = "rgba(255,255,255,0.04)" if dark else "rgba(0,0,0,0.018)"
    hover_bg = "rgba(255,255,255,0.07)" if dark else "rgba(0,0,0,0.035)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"

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

  /* Schnellnavigation (optional aber sehr „tool-like“) */
  .rgm-chips {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
  }}
  .rgm-chip {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    border-radius: 999px;
    border: 1px solid {border};
    background: {soft_bg};
    color: var(--rgm-text, #111);
    font-size: 13px;
    font-weight: 750;
    text-decoration: none;
  }}
  .rgm-chip:hover {{
    background: {hover_bg};
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

  .rgm-text {{
    margin: 10px 0 0 0;
  }}

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

  /* Sticky Header */
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
    background: transparent;
  }}

  /* Zebra + Hover -> bessere Lesbarkeit */
  .rgm-table tbody tr:nth-child(even) td {{
    background: {zebra_bg};
  }}
  .rgm-table tbody tr:hover td {{
    background: {hover_bg};
  }}

  .rgm-table tr:last-child td {{
    border-bottom: none;
  }}

  .rgm-strong {{
    font-weight: 850;
  }}

  .rgm-warning {{
    margin-top: 14px;
    padding: 14px 14px;
    border-radius: 14px;
    border: 1px solid rgba(242, 140, 40, 0.60);
    background: rgba(242, 140, 40, 0.10);
    box-shadow: {shadow};
  }}

  .rgm-warning-title {{
    font-weight: 900;
    font-size: 14px;
    color: #c0392b;
    margin: 0 0 6px 0;
  }}

  .rgm-warning ul {{
    margin: 0;
    padding-left: 18px;
    color: var(--rgm-text, #111);
    font-size: 13px;
    line-height: 1.65;
  }}

  .rgm-warning li {{
    margin: 0;
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

    st.markdown('<div class="rgm-page">', unsafe_allow_html=True)

    # HERO + Schnellnavigation
    st.markdown(
        """
<div class="rgm-hero">
  <div class="rgm-h1">Ausfüllhinweise zum Reifegradmodell</div>
  <div class="rgm-accent-line"></div>

  <p class="rgm-lead">
    Anhand des Reifegradmodells ist eine rasche und einheitliche Bestimmung von Reifegraden der technischen Dokumentation möglich.
    Hierzu werden je Subdimension spezifische Fragestellungen beantwortet. Das Reifegradmodell orientiert sich an den Reifegradstufen
    der Capability Maturity Model Integration (CMMI).
  </p>

  <div class="rgm-chips">
    <a class="rgm-chip" href="#rgm_reifegrad">Reifegradstufen</a>
    <a class="rgm-chip" href="#rgm_keywords">Schlüsselwörter</a>
    <a class="rgm-chip" href="#rgm_answers">Antwortmöglichkeiten</a>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # Anchor: Reifegradstufen
    st.markdown('<div id="rgm_reifegrad"></div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="rgm-card">
  <div class="rgm-card-title">Beschreibung der Reifegradstufen</div>

  <div class="rgm-table-wrap">
    <table class="rgm-table">
      <thead>
        <tr>
          <th style="width: 180px;">Reifegradstufe</th>
          <th>Beschreibung</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rgm-strong">1 - initial</td>
          <td>Prozesse laufen unvorhersehbar und reaktiv. Der Erfolg auf dieser Ebene hängt hauptsächlich von den individuellen Anstrengungen und nicht von etablierten organisatorischen Prozessen ab.</td>
        </tr>
        <tr>
          <td class="rgm-strong">2 - gemanagt</td>
          <td>Organisationen auf dieser Ebene etablieren grundlegende Projektmanagementpraktiken. Projekte folgen grundlegenden Planungs- und Kontrollmechanismen und führen so zu vorhersehbaren Ergebnissen.</td>
        </tr>
        <tr>
          <td class="rgm-strong">3 - definiert</td>
          <td>Diese Ebene markiert einen deutlichen Wandel hin zu einer unternehmensweiten Prozessstandardisierung. Einheiten/Projekte folgen einheitlichen Vorgehensweisen, wodurch die Variabilität der Ausführung sinkt.</td>
        </tr>
        <tr>
          <td class="rgm-strong">4 - quantitativ gemanagt</td>
          <td>Organisationen erreichen eine präzise Prozesskontrolle. Prozesse werden messbar gesteuert, u. a. über Kennzahlen zur Prozess- und Produktqualität.</td>
        </tr>
        <tr>
          <td class="rgm-strong">5 - optimiert</td>
          <td>Organisationen verbessern ihre Prozesse systematisch und kontinuierlich – insbesondere durch inkrementelle und innovative Änderungen.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="rgm-muted rgm-text">
    Um eine inhaltliche Abgrenzung zwischen den jeweiligen Reifegradstufen zu ermöglichen, werden Schlüsselwörter verwendet.
    Diese werden nachfolgend erläutert.
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # Anchor: Schlüsselwörter
    st.markdown('<div id="rgm_keywords"></div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="rgm-card">
  <div class="rgm-card-title">Beschreibung der Schlüsselwörter</div>

  <div class="rgm-table-wrap">
    <table class="rgm-table">
      <thead>
        <tr>
          <th style="width: 220px;">Schlüsselwort</th>
          <th>Interpretation / Bedeutung</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rgm-strong">Situativ / Ad-Hoc</td>
          <td>Der Prozess wird anlassbezogen durchgeführt und beispielsweise durch externe Trigger angestoßen.</td>
        </tr>
        <tr>
          <td class="rgm-strong">Gelegentlich</td>
          <td>Der Prozess wird zwar wiederholt durchgeführt, jedoch ohne ein fest definiertes Intervall.</td>
        </tr>
        <tr>
          <td class="rgm-strong">Regelmäßig</td>
          <td>Der Prozess wird in einem fest definierten Intervall durchgeführt.</td>
        </tr>
        <tr>
          <td class="rgm-strong">Regelmäßig überprüft</td>
          <td>Die Einhaltung der fest definierten Intervalle wird mit Hilfe von Kennzahlen gesteuert.</td>
        </tr>
        <tr>
          <td class="rgm-strong">Kontinuierlich verbessert</td>
          <td>Der Prozess wird durch die durchführenden Mitarbeitenden kontinuierlich verbessert.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="rgm-muted rgm-text">
    Zur Identifikation der Reifegrade werden spezifische Fragestellungen definiert. Die Antwortmöglichkeiten spiegeln den Umsetzungsgrad des jeweiligen Prüfkriteriums wider.
    Basierend auf der Konsolidierung der Antworten wird der Reifegrad des betrachteten Prozessbereichs identifiziert. Das methodische Basismodell zur Identifikation der Reifegrade ist die Normreihe ISO/IEC 330xx.
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # Anchor: Antwortmöglichkeiten
    st.markdown('<div id="rgm_answers"></div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="rgm-card">
  <div class="rgm-card-title">Beschreibung der Antwortmöglichkeiten</div>

  <div class="rgm-table-wrap">
    <table class="rgm-table">
      <thead>
        <tr>
          <th style="width: 170px;">Antwort</th>
          <th style="width: 140px;">Umsetzungsgrad</th>
          <th>Beschreibung</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rgm-strong">Nicht anwendbar</td>
          <td>-</td>
          <td>Das Prüfkriterium ist nicht auf die Organisation anwendbar. Sollten alle Fragen einer Stufe nicht anwendbar sein, verbleibt der Reifegrad auf der darunterliegenden Stufe (bzw. als „NV“).</td>
        </tr>
        <tr>
          <td class="rgm-strong">Gar nicht</td>
          <td>0% – 15%</td>
          <td>Es gibt keinen Nachweis für die Erreichung des Prüfkriteriums.</td>
        </tr>
        <tr>
          <td class="rgm-strong">In ein paar Fällen</td>
          <td>&gt;15% – 50%</td>
          <td>Es bestehen teilweise Anzeichen für die Erreichung des Prüfkriteriums.</td>
        </tr>
        <tr>
          <td class="rgm-strong">In den meisten Fällen</td>
          <td>&gt;50% – 85%</td>
          <td>Es gibt signifikante Anzeichen für die Erreichung des Prüfkriteriums.</td>
        </tr>
        <tr>
          <td class="rgm-strong">Vollständig</td>
          <td>&gt;85% – 100%</td>
          <td>Es gibt einen vollständigen Nachweis für die Erreichung des Prüfkriteriums.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="rgm-warning">
    <div class="rgm-warning-title">WICHTIG! Bitte beachten Sie:</div>
    <ul>
      <li>
        Die Fragen des Reifegradmodells sind so formuliert, dass jede Reifegradstufe auf den vorhergehenden Stufen aufbaut.
        Wenn Ihre Organisation eine höhere Stufe bereits erreicht hat und der beschriebene Zustand einer niedrigeren Stufe dadurch
        überwunden wurde (z. B. Varianten werden nicht mehr manuell gepflegt), ist die Frage dennoch mit „Vollständig“ zu beantworten.
        „Vollständig“ bedeutet: Der beschriebene Zustand dieser Stufe wurde vollständig erreicht oder übertroffen.
        Antworten wie „Gar nicht“, „In ein paar Fällen“ oder „In den meisten Fällen“ würden fälschlicherweise anzeigen, dass diese Stufe noch nicht erfüllt ist.
      </li>
    </ul>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Zurück", use_container_width=True):
            st.session_state["nav_request"] = "Einführung"
            st.rerun()
    with c2:
        if st.button("Weiter zur Erhebung", type="primary", use_container_width=True):
            st.session_state["nav_request"] = "Erhebung"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
