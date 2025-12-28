# pages/00_Ausfuellhinweise.py
from __future__ import annotations

import streamlit as st
from core.state import init_session_state


def main():
    init_session_state()

    st.markdown(
        """
<style>
  .rgm-wrap { max-width: 1100px; }

  .rgm-title {
    font-weight: 800;
    font-size: 20px;
    margin: 6px 0 10px 0;
    color: var(--rgm-text, #111);
  }

  .rgm-text {
    color: var(--rgm-text, #111);
    font-size: 14px;
    line-height: 1.75;
    margin: 6px 0 12px 0;
  }

  .rgm-subtitle {
    font-weight: 800;
    font-size: 14px;
    margin: 14px 0 6px 0;
    color: var(--rgm-text, #111);
  }

  .rgm-table {
    width: 100%;
    border-collapse: collapse;
    background: var(--rgm-card-bg, #fff);
    border: 1px solid var(--rgm-border, rgba(0,0,0,0.10));
    border-radius: 10px;
    overflow: hidden;
    margin: 8px 0 14px 0;
  }

  .rgm-table th {
    text-align: left;
    padding: 10px 10px;
    font-weight: 800;
    font-size: 13px;
    color: var(--rgm-text, #111);
    background: rgba(127,127,127,0.10);
    border-bottom: 1px solid var(--rgm-border, rgba(0,0,0,0.10));
    vertical-align: top;
  }

  .rgm-table td {
    padding: 10px 10px;
    font-size: 13px;
    color: var(--rgm-text, #111);
    border-bottom: 1px solid var(--rgm-border, rgba(0,0,0,0.10));
    vertical-align: top;
  }

  .rgm-table tr:last-child td { border-bottom: none; }

  .rgm-strong { font-weight: 800; }

  .rgm-warning {
    background: rgba(242, 140, 40, 0.10);
    border: 1px solid rgba(242, 140, 40, 0.55);
    border-radius: 10px;
    padding: 12px 14px;
    margin: 10px 0 8px 0;
  }

  .rgm-warning-title {
    font-weight: 900;
    color: #c0392b;
    margin-bottom: 6px;
  }

  .rgm-warning ul {
    margin: 0;
    padding-left: 18px;
    color: var(--rgm-text, #111);
    font-size: 13px;
    line-height: 1.65;
  }
</style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="rgm-wrap">
  <div class="rgm-title">Ausfüllhinweise zum Reifegradmodell</div>

  <div class="rgm-text">
    Anhand des Reifegradmodells ist eine rasche und einheitliche Bestimmung von Reifegraden der technischen Dokumentation möglich.
    Hierzu werden je Subdimension spezifische Fragestellungen beantwortet. Das Reifegradmodell orientiert sich an den Reifegradstufen
    der Capability Maturity Model Integration (CMMI).
  </div>

  <div class="rgm-subtitle">Beschreibung der Reifegradstufen:</div>
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

  <div class="rgm-text">
    Um eine inhaltliche Abgrenzung zwischen den jeweiligen Reifegradstufen zu ermöglichen, werden Schlüsselwörter verwendet.
    Diese werden nachfolgend erläutert.
  </div>

  <div class="rgm-subtitle">Beschreibung der Schlüsselwörter:</div>
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

  <div class="rgm-text">
    Zur Identifikation der Reifegrade werden spezifische Fragestellungen definiert. Die Antwortmöglichkeiten spiegeln den Umsetzungsgrad des jeweiligen Prüfkriteriums wider.
    Basierend auf der Konsolidierung der Antworten wird der Reifegrad des betrachteten Prozessbereichs identifiziert. Das methodische Basismodell zur Identifikation der Reifegrade ist die Normreihe ISO/IEC 330xx.
  </div>

  <div class="rgm-subtitle">Beschreibung der Antwortmöglichkeiten:</div>
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

  <div class="rgm-warning">
    <div class="rgm-warning-title">WICHTIG! Bitte beachten Sie:</div>
    <ul>
      Die Fragen des Reifegradmodells sind so formuliert, dass jede Reifegradstufe auf den vorhergehenden Stufen aufbaut. Das bedeutet: Wenn Ihre Organisation eine höhere Stufe bereits erreicht hat und der beschriebene Zustand einer niedrigeren Stufe dadurch überwunden wurde (z. B. Varianten werden nicht mehr manuell gepflegt), ist die Frage dennoch mit „Vollständig“ zu beantworten. „Vollständig“ bedeutet in diesem Zusammenhang: Der beschriebene Zustand dieser Stufe wurde vollständig erreicht oder übertroffen. Antworten wie „Gar nicht“, „In ein paar Fällen“ oder „In den meisten Fällen“ würden fälschlicherweise anzeigen, dass diese Stufe noch nicht erfüllt ist.
    </ul>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Navigation
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Zurück", use_container_width=True):
            st.session_state["nav_request"] = "Einführung"
            st.rerun()
    with c2:
        if st.button("Weiter zur Erhebung", type="primary", use_container_width=True):
            st.session_state["nav_request"] = "Erhebung"
            st.rerun()


if __name__ == "__main__":
    main()
